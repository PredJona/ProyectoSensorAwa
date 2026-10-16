"""Datos controlados: no constituyen mediciones del montaje."""
import csv
import hashlib
import importlib
import json
import tempfile
import unittest
from pathlib import Path


class AnalisisSesionTest(unittest.TestCase):
    def setUp(self):
        self.assertIsNotNone(importlib.util.find_spec('python.analisis_sesion'),
                             'Falta el analizador reproducible de la sesión')
        self.mod = importlib.import_module('python.analisis_sesion')
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.folder = Path(self.tmp.name)

    def fuente(self, nombre, valores, origen='prueba_controlada'):
        path = self.folder / f'{nombre}.csv'
        with path.open('w', newline='') as f:
            w = csv.writer(f)
            w.writerow(['timestamp_utc','t_ms','adc1','adc2','adc3','origen'])
            for i, valor in enumerate(valores):
                w.writerow([f'2026-10-16T00:00:{i:02d}+00:00',i*500,valor,10,20,origen])
        return path

    def sesion(self, fuentes):
        entries = []
        for name, path, state in fuentes:
            entries.append({'id':name,'csv':str(path),'sensor':'adc1',
                            'altura_inmersion':10,'unidad':'mm','estado':state})
        path = self.folder/'sesion.json'
        path.write_text(json.dumps({'ensayos':entries}))
        return path

    def test_cuenta_filas_y_tres_canales_separa_excluidos(self):
        a=self.fuente('aceptado',[1,3,5])
        b=self.fuente('excluido',[9])
        p=self.sesion([('a',a,'pendiente'),('b',b,'excluido_de_calibracion')])
        result=self.mod.auditar_sesion(p)
        self.assertEqual(result['filas_csv_principales'],4)
        self.assertEqual(result['lecturas_adc_principales'],12)
        self.assertEqual(result['filas_resumen_preliminar'],3)
        s=result['ensayos'][0]['canales']['adc1']
        self.assertEqual((s['media'],s['minimo'],s['maximo']),(3,1,5))
        self.assertEqual(s['desviacion_muestral'],2)
        self.assertEqual(s['varianza_muestral'],4)
        self.assertEqual(s['rango'],4)
        self.assertEqual(s['iqr'],2)
        self.assertIsNone(result['ensayos'][1]['canales']['adc1']['desviacion_muestral'])
        self.assertEqual(result['ensayos'][0]['sensor_con_altura_comunicada'],'adc1')

    def test_detecta_huella_incorrecta_y_fuente_duplicada(self):
        a=self.fuente('a',[1,2])
        p=self.sesion([('a',a,'pendiente')])
        data=json.loads(p.read_text())
        data['ensayos'][0]['sha256']='0'*64
        p.write_text(json.dumps(data))
        with self.assertRaisesRegex(ValueError,'huella'):
            self.mod.auditar_sesion(p)
        p=self.sesion([('a',a,'pendiente'),('duplicado',a,'pendiente')])
        with self.assertRaisesRegex(ValueError,'duplicad'):
            self.mod.auditar_sesion(p)

    def test_no_acepta_csv_malformado_como_medicion(self):
        a=self.fuente('a',[1,2])
        p=self.sesion([('a',a,'pendiente')])
        with a.open('a') as f: f.write('2026-10-16T00:00:02+00:00,1000,1024,1,2,prueba_controlada\n')
        with self.assertRaises(ValueError): self.mod.auditar_sesion(p)

    def test_seleccion_del_resumen_no_borra_repeticiones_inestables(self):
        a=self.fuente('a',[1,2,3])
        b=self.fuente('b',[8,9])
        p=self.sesion([('a',a,'no_apto_por_inestabilidad'),('b',b,'pendiente')])
        summary=self.folder/'resumen.csv'
        summary.write_text('ensayo\na\n')
        data=json.loads(p.read_text())
        data['resumen_preliminar']=str(summary)
        p.write_text(json.dumps(data))
        result=self.mod.auditar_sesion(p)
        self.assertEqual(result['filas_csv_principales'],5)
        self.assertEqual(result['filas_resumen_preliminar'],3)
        self.assertTrue(result['ensayos'][0]['incluido_resumen_preliminar'])
        self.assertFalse(result['ensayos'][1]['incluido_resumen_preliminar'])

    def test_exporta_sin_sobrescribir_fuentes_ni_destino(self):
        a=self.fuente('a',[1,2,3])
        p=self.sesion([('a',a,'pendiente')])
        before=hashlib.sha256(a.read_bytes()).hexdigest()
        result=self.mod.auditar_sesion(p)
        output=self.folder/'salida'
        self.mod.exportar(result,output)
        self.assertEqual(hashlib.sha256(a.read_bytes()).hexdigest(),before)
        self.assertEqual(json.loads((output/'auditoria.json').read_text())['filas_csv_principales'],3)
        self.assertEqual((output/'adc_a.png').read_bytes()[:8],b'\x89PNG\r\n\x1a\n')
        self.assertGreater((output/'adc_a.png').stat().st_size,5000)
        with self.assertRaises(FileExistsError): self.mod.exportar(result,output)
