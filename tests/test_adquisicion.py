import csv
import importlib
import io
import json
import os
import threading
import time
import tempfile
import unittest
from unittest.mock import patch
from pathlib import Path

import numpy as np


class AdquisicionTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.c = importlib.import_module('python.comunicacion')
        cls.cal = importlib.import_module('python.calibracion')

    def test_parser_controlado(self):
        self.assertEqual(self.c.parsear_linea(b'1000,0,512,1023\r\n'), (1000,0,512,1023))
        self.assertIsNone(self.c.parsear_linea('t_ms,adc1,adc2,adc3'))

    def test_cabecera_r4_y_registro_compatible_con_graficas(self):
        self.assertIsNone(self.c.parsear_linea(b'tiempo_ms,sensor1,sensor2,sensor3\r\n'))
        entradas=io.BytesIO(b'tiempo_ms,sensor1,sensor2,sensor3\r\n'
                            b'500,0,512,1023\r\n1000,1023,1,0\r\n')
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'r4.csv'
            self.assertEqual(self.c.registrar(entradas,p,max_muestras=2,
                             origen='prueba_controlada'),(2,0))
            with p.open() as f: filas=list(csv.DictReader(f))
            self.assertEqual(set(filas[0]),
                             {'timestamp_utc','t_ms','adc1','adc2','adc3','origen'})
            self.assertEqual([filas[0][c] for c in ('t_ms','adc1','adc2','adc3')],
                             ['500','0','512','1023'])

    def test_parser_rechaza_invalidos(self):
        for s in ('1,2,3', '1,2,3,4,5', '1,2.5,3,4', '-1,1,2,3',
                  '1,1024,2,3', '1,-1,2,3', 'nan,1,2,3', '4294967296,1,2,3', b'\xff'):
            with self.subTest(s=s):
                with self.assertRaises(ValueError): self.c.parsear_linea(s)

    def test_registro_valida_y_conserva_adc(self):
        entradas = io.BytesIO(b't_ms,adc1,adc2,adc3\n100,0,512,1023\nmal\n200,1,500,900\n')
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'control.csv'
            n,invalidos=self.c.registrar(entradas,p,max_muestras=2,origen='prueba_controlada')
            with p.open() as f: filas=list(csv.DictReader(f))
            self.assertEqual((n,invalidos),(2,1))
            self.assertEqual(filas[0]['adc3'],'1023')
            self.assertEqual(filas[0]['origen'],'prueba_controlada')
            self.assertTrue(filas[0]['timestamp_utc'].endswith('+00:00'))
            self.assertNotIn('h1_cm',filas[0])
            with self.assertRaises(FileExistsError):
                self.c.registrar(io.BytesIO(),p,origen='prueba_controlada')

    def test_linea_fragmentada_y_timeout(self):
        class Puerto:
            def __init__(self): self.partes=iter([b'100,1,',b'',b'2,3\n'])
            def read(self,size): return next(self.partes,b'')
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'fragmento.csv'
            n,bad=self.c.registrar(Puerto(),p,max_muestras=1,duracion=.2,
                                  origen='prueba_controlada')
            self.assertEqual((n,bad),(1,0))

    def test_timeout_finaliza(self):
        class Vacio:
            def read(self,size): return b''
        with tempfile.TemporaryDirectory() as d:
            self.assertEqual(self.c.registrar(Vacio(),Path(d)/'vacio.csv',
                             duracion=.01,origen='prueba_controlada'),(0,0))

    def test_argumentos_invalidos_no_abren_el_puerto(self):
        with tempfile.TemporaryDirectory() as d, patch('serial.Serial',side_effect=AssertionError('Puerto abierto')) as abrir:
            for indice,argumentos in enumerate(({'max_muestras':0}, {'duracion':True},
                               {'duracion':float('nan')}, {'baudios':0},
                               {'baudios':True})):
                destino=Path(d)/f'invalido_{indice}.csv'
                with self.subTest(argumentos=argumentos):
                    with self.assertRaises(ValueError):
                        self.c.capturar('/dev/puerto-prueba',destino,**argumentos)
                    self.assertFalse(destino.exists())
            abrir.assert_not_called()

    def test_desconexion_conserva_archivo(self):
        class Desconectado:
            def __init__(self): self.n=0
            def read(self,size):
                self.n+=1
                if self.n==1: return b'10,1,2,3\n'
                raise OSError('Desconectado')
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'parcial.csv'
            with self.assertRaises(OSError): self.c.registrar(Desconectado(),p,origen='prueba_controlada')
            with p.open() as f: self.assertEqual(len(list(csv.DictReader(f))),1)

    def test_calibracion_interpolada_sin_extrapolar(self):
        # Valores controlados para probar interpolación: NO calibración del circuito.
        puntos=[[100,0],[300,2],[700,3]]
        np.testing.assert_allclose(self.cal.convertir([100,200,500,700],puntos),[0,1,2.5,3])
        with self.assertRaises(ValueError): self.cal.convertir([99],puntos)
        with self.assertRaises(ValueError): self.cal.convertir([701],puntos)
        for puntos in ([[1,0]],[[100,0],[100,2]],[[100,2],[300,1]],[[0,0],[1024,2]]):
            with self.subTest(puntos=puntos):
                with self.assertRaises(ValueError): self.cal.convertir([100],puntos)

    def test_carga_calibracion_exige_tres_sensores(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'cal.json'
            p.write_text(json.dumps({'unidad':'cm','sensores':{'adc1':[[0,0],[100,1]]}}))
            with self.assertRaises(ValueError): self.cal.cargar(p)

    @unittest.skipUnless(os.name=='posix','Pseudo terminal solo disponible en POSIX')
    def test_serial_timeout_antes_de_muestras_no_es_fin_de_archivo(self):
        import pty
        import serial
        master,slave=pty.openpty()
        parar=threading.Event()

        def emitir():
            if parar.wait(.06): return
            os.write(master,b'500,2,3,4\n')
            if parar.wait(.06): return
            os.write(master,b'1000,3,4,5\n')

        hilo=None
        try:
            with serial.Serial(os.ttyname(slave),115200,timeout=.01) as puerto:
                hilo=threading.Thread(target=emitir)
                hilo.start()
                with tempfile.TemporaryDirectory() as d:
                    destino=Path(d)/'serial.csv'
                    self.assertEqual(self.c.registrar(puerto,destino,max_muestras=2,
                                     duracion=1,origen='prueba_controlada'),(2,0))
                    with destino.open() as archivo:
                        filas=list(csv.DictReader(archivo))
                    self.assertEqual([f['t_ms'] for f in filas],['500','1000'])
        finally:
            parar.set()
            if hilo: hilo.join(timeout=1)
            os.close(master)
            os.close(slave)

    @unittest.skipUnless(os.name=='posix','Pseudo terminal solo disponible en POSIX')
    def test_serial_real_trama_sin_newline_respeta_limite(self):
        import pty
        import serial
        master,slave=pty.openpty()
        parar=threading.Event()

        def emitir():
            limite=time.monotonic()+.25
            while not parar.is_set() and time.monotonic()<limite:
                os.write(master,b'1')
                parar.wait(.003)
            os.write(master,b'\n')

        hilo=None
        try:
            with serial.Serial(os.ttyname(slave),9600,timeout=.02) as puerto:
                hilo=threading.Thread(target=emitir)
                hilo.start()
                with tempfile.TemporaryDirectory() as d:
                    inicio=time.monotonic()
                    self.c.registrar(puerto,Path(d)/'limite.csv',duracion=.04,
                                     origen='prueba_controlada')
                    self.assertLess(time.monotonic()-inicio,.15)
        finally:
            parar.set()
            if hilo: hilo.join(timeout=1)
            os.close(master)
            os.close(slave)


if __name__=='__main__': unittest.main()
