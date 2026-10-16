"""Flujos SINTÉTICOS con reloj virtual; no son mediciones experimentales."""
import csv
import json
import os
import threading
import time
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import patch

from python import comunicacion as c


class Reloj:
    def __init__(self):
        self.t = 0.

    def sleep(self, segundos):
        self.t += segundos

    def utc(self, *args):
        return datetime(2026, 1, 1, tzinfo=timezone.utc) + timedelta(seconds=self.t)


class SerialSimulado:
    """reset_input_buffer NO borra eventos: emula datos retenidos tras el USB."""
    timeout = .05

    def __init__(self, reloj, eventos):
        self.reloj = reloj
        self.eventos = list(eventos)
        self.pendiente = b''
        self.vaciados = 0

    def reset_input_buffer(self):
        self.vaciados += 1

    def read(self, size):
        if self.pendiente:
            dato, self.pendiente = self.pendiente[:size], self.pendiente[size:]
            return dato
        if self.eventos and self.eventos[0][0] <= self.reloj.t + self.timeout:
            momento, dato = self.eventos.pop(0)
            self.reloj.t = max(momento, self.reloj.t)
            if isinstance(dato, Exception):
                raise dato
            self.pendiente = dato
            return self.read(size)
        self.reloj.sleep(self.timeout)
        return b''


def normal(inicio=0, cantidad=12, t_ms=10000):
    return [(inicio + i * .5, f'{(t_ms+i*500) % 2**32},1,2,3\n'.encode())
            for i in range(cantidad)]


class SincronizacionTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.ruta = Path(self.tmp.name) / 'SINTETICO.csv'
        self.reloj = Reloj()
        for nombre, reemplazo in [('time.monotonic', lambda: self.reloj.t),
                                 ('time.sleep', self.reloj.sleep),
                                 ('datetime', None)]:
            p = patch('python.comunicacion.' + nombre, reemplazo) if reemplazo else patch('python.comunicacion.datetime')
            obj = p.start()
            if nombre == 'datetime':
                obj.now.side_effect = self.reloj.utc
            self.addCleanup(p.stop)

    def ejecutar(self, eventos, **kwargs):
        fuente = SerialSimulado(self.reloj, eventos)
        resultado = c.registrar(fuente, self.ruta, origen='prueba_controlada',
                                sincronizar=True, max_muestras=4, duracion=6, **kwargs)
        return resultado, fuente

    def filas(self):
        with self.ruta.open() as f:
            return list(csv.DictReader(f))

    def test_descarta_acumulacion_del_usb_incluso_despues_de_vaciar(self):
        viejos = b''.join(f'{i*500},9,9,9\n'.encode() for i in range(20))
        resultado, fuente = self.ejecutar([(0, b'fragmento\n'), (.1, viejos)] + normal(.5))
        self.assertEqual(resultado[0], 4)
        filas = self.filas()
        self.assertTrue(all(f['adc1'] == '1' for f in filas))
        fechas = [datetime.fromisoformat(f['timestamp_utc']) for f in filas]
        self.assertEqual([(b-a).total_seconds() for a,b in zip(fechas, fechas[1:])], [.5]*3)
        self.assertEqual(fuente.vaciados, 1)

    def test_fragmento_inicial_no_pasa_como_linea_y_no_pierde_datos_tras_inicio(self):
        self.ejecutar([(0, b'99,8,7\n')] + normal(.5))
        self.assertEqual([int(f['t_ms']) for f in self.filas()], [12000,12500,13000,13500])

    def test_timeouts_intermedios_conservan_fragmentos_despues_del_inicio(self):
        eventos = [(0, b'\n')] + normal(.5, 5)
        eventos += [(3., b'12500,1,'), (3.1, b'2,3\n')] + normal(3.5, 2, 13000)
        self.ejecutar(eventos)
        self.assertEqual([f['t_ms'] for f in self.filas()], ['12000','12500','13000','13500'])

    def test_sin_datos_nuevos_no_registra_el_burst_y_finaliza(self):
        with self.assertRaisesRegex(TimeoutError, 'sincroniz'):
            self.ejecutar(normal(0, 0) + [(0, b'\n500,1,2,3\n1000,1,2,3\n')], timeout_sincronizacion=2)
        self.assertEqual(self.filas(), [])
        self.assertLess(self.reloj.t, 2.2)

    def test_timeout_activo_conserva_parcial(self):
        with self.assertRaisesRegex(TimeoutError, 'datos nuevos'):
            self.ejecutar([(0,b'\n')]+normal(.5,5), timeout_inactivo=1)
        self.assertEqual(len(self.filas()), 1)

    def test_desconexion_y_recuperacion_en_archivo_nuevo(self):
        with self.assertRaises(OSError):
            self.ejecutar([(0,b'\n')]+normal(.5,5)+[(3.,OSError('USB desconectado'))])
        self.assertEqual(len(self.filas()), 1)
        self.ruta = self.ruta.with_name('RECUPERACION_SINTETICA.csv')
        self.ejecutar([(self.reloj.t,b'\n')]+normal(self.reloj.t+.5))
        self.assertEqual(len(self.filas()), 4)

    def test_reinicio_no_se_confunde_con_desborde(self):
        with self.assertRaisesRegex(RuntimeError, 'reinicio'):
            self.ejecutar([(0,b'\n')]+normal(.5,5)+[(3., b'500,1,2,3\n')])
        self.assertEqual(len(self.filas()), 1)

    def test_desborde_compatible_con_cadencia_continua(self):
        self.ejecutar([(0,b'\n')]+normal(.5,12,2**32-3000))
        self.assertEqual([int(f['t_ms']) for f in self.filas()], [2**32-1000,2**32-500,0,500])
        informe = json.loads(self.ruta.with_suffix('.sesion.json').read_text())
        self.assertEqual(informe['desbordamientos_compatibles'], 1)

    def test_salto_y_burst_durante_captura_se_detectan(self):
        for dato in (b'15000,1,2,3\n', b'12500,1,2,3\n13000,1,2,3\n'):
            with self.subTest(dato=dato):
                self.ruta = self.ruta.with_name(self.ruta.stem+'x.csv')
                self.reloj.t = 0
                with self.assertRaisesRegex(RuntimeError, 'temporal|cadencia'):
                    self.ejecutar([(0,b'\n')]+normal(.5,5)+[(3.,dato)])
                self.assertLessEqual(len(self.filas()), 2)

    def test_experimental_no_acepta_rafaga_sin_datos_nuevos(self):
        fuente=SerialSimulado(self.reloj,[(0,b'\n'+b'500,9,9,9\n'*20)])
        with self.assertRaises(TimeoutError):
            c.registrar(fuente,self.ruta,max_muestras=4,duracion=6)
        self.assertEqual(self.filas(),[])

    def test_cabecera_en_captura_es_reinicio_y_salto_utc_detiene(self):
        with self.assertRaisesRegex(RuntimeError,'reinicio'):
            self.ejecutar([(0,b'\n')]+normal(.5,5)+[(3.,c.CABECERA.encode()+b'\n')])
        self.ruta=self.ruta.with_name('RELOJ_UTC_SINTETICO.csv')
        self.reloj.t=0
        def utc_con_salto(*args):
            fecha=self.reloj.utc()
            return fecha+timedelta(seconds=5) if self.reloj.t>=3 else fecha
        with patch('python.comunicacion.datetime') as fecha:
            fecha.now.side_effect=utc_con_salto
            with self.assertRaisesRegex(RuntimeError,'reloj UTC'):
                self.ejecutar([(0,b'\n')]+normal(.5))
        self.assertEqual(len(self.filas()),1)


class SerialIntegracionTest(unittest.TestCase):
    @unittest.skipUnless(os.name=='posix','Requiere pseudoterminal POSIX')
    def test_capturar_pyserial_a_500ms_reales_sin_hardware(self):
        """Pseudoterminal con datos SINTÉTICOS; nunca abre el Arduino."""
        import pty
        master,slave=pty.openpty()
        parar=threading.Event()
        def emitir():
            if parar.wait(.1): return
            os.write(master,b'fragmento\n'+b'500,9,9,9\n'*20)
            if parar.wait(.3): return
            for i in range(9):
                os.write(master,f'{10000+i*500},1,2,3\n'.encode())
                if parar.wait(.5): return
        hilo=threading.Thread(target=emitir)
        try:
            hilo.start()
            with tempfile.TemporaryDirectory() as d:
                ruta=Path(d)/'PSEUDOTERMINAL_SINTETICO.csv'
                inicio=time.monotonic()
                self.assertEqual(c.capturar(os.ttyname(slave),ruta,max_muestras=3,duracion=5),(3,0))
                self.assertGreater(time.monotonic()-inicio,3.2)
                informe=c.verificar_cadencia(ruta)
                self.assertTrue(informe['cadencia_compatible'],informe)
                with ruta.open() as f:
                    self.assertEqual([r['adc1'] for r in csv.DictReader(f)],['1']*3)
        finally:
            parar.set()
            hilo.join(timeout=1)
            os.close(master)
            os.close(slave)


if __name__ == '__main__':
    unittest.main()
