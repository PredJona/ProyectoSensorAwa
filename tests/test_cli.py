import importlib
import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

RAIZ=Path(__file__).resolve().parents[1]


class CliTest(unittest.TestCase):
    def ejecutar(self,*args):
        return subprocess.run([sys.executable,'-m','python.main',*args],cwd=RAIZ,
                              capture_output=True,text=True)

    def test_resolver_exporta_todo(self):
        with tempfile.TemporaryDirectory() as d:
            r=self.ejecutar('resolver','--salida',d)
            self.assertEqual(r.returncode,0,r.stderr)
            p=Path(d)
            resumen=json.loads((p/'datos/resultados/resumen.json').read_text())
            self.assertEqual(resumen['origen'],'academico')
            self.assertEqual(resumen['parametros']['tol'],.001)
            self.assertEqual(len(resumen['metodos']),3)
            self.assertEqual(resumen['graficas'][0], 'graficas/convergencia.png')
            self.assertTrue(all(m['converge'] for m in resumen['metodos']))
            self.assertEqual(len(list((p/'graficas').glob('*.png'))),4)
            self.assertTrue((p/'datos/resultados/gauss_jordan_operaciones.csv').exists())

    def test_limite_no_se_anuncia_como_convergencia(self):
        with tempfile.TemporaryDirectory() as d:
            r=self.ejecutar('resolver','--salida',d,'--max-iter','1','--sin-graficas')
            self.assertEqual(r.returncode,2)
            resumen=json.loads((Path(d)/'datos/resultados/resumen.json').read_text())
            self.assertFalse(resumen['metodos'][0]['converge'])

    def test_argumento_invalido(self):
        r=self.ejecutar('resolver','--tol','0','--sin-graficas')
        self.assertEqual(r.returncode,2)
        self.assertIn('positiva',r.stderr)

    def test_problemas_separados_y_compatibilidad_historica(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)
            r=self.ejecutar('resolver','--salida',d)
            self.assertEqual(r.returncode,0,r.stderr)
            historicos={f.relative_to(p):f.read_bytes() for f in p.rglob('*') if f.is_file()}
            legacy=json.loads((p/'datos/resultados/resumen.json').read_text())
            r=self.ejecutar('resolver','--problema','11.1','--salida',d)
            self.assertEqual(r.returncode,0,r.stderr)
            self.assertIn('11.1',r.stdout)
            self.assertIn('A =',r.stdout)
            self.assertIn('b =',r.stdout)
            for nombre,contenido in historicos.items():
                self.assertEqual((p/nombre).read_bytes(),contenido)
            res=json.loads((p/'datos/resultados/11_1/resumen.json').read_text())
            self.assertEqual(res['problema'],'11.1')
            self.assertEqual(res['origen'],'academico')
            self.assertEqual(res['A'],[[2,-1,0],[-1,3,-1],[0,-1,2]])
            self.assertEqual(res['b'],[3,2,1])
            self.assertEqual(res['parametros']['alpha'],1)
            self.assertEqual(res['parametros']['niveles_anteriores'],[3,2,1])
            self.assertEqual([m['metodo'] for m in res['metodos']],['Jacobi','Gauss-Seidel'])
            self.assertEqual([m['iteraciones'] for m in res['metodos']],[14,9])
            self.assertEqual(res['conservacion']['suma_anterior'],6)
            self.assertAlmostEqual(res['conservacion']['suma_referencia'],6)
            self.assertFalse((p/'datos/resultados/11_1/gauss_jordan_operaciones.csv').exists())
            for nombre in ('jacobi.csv','gauss_seidel.csv','comparacion.csv'):
                self.assertTrue((p/'datos/resultados/11_1'/nombre).exists())
            self.assertEqual(len(res['graficas']),4)
            for nombre in res['graficas']:
                self.assertTrue(nombre.startswith('graficas/11_1/'))
                self.assertEqual((p/nombre).read_bytes()[:8],b'\x89PNG\r\n\x1a\n')
            r=self.ejecutar('resolver','--problema','11.2','--salida',str(p/'explicito'))
            self.assertEqual(r.returncode,0,r.stderr)
            res2=json.loads((p/'explicito/datos/resultados/resumen.json').read_text())
            self.assertEqual(res2['problema'],'11.2')
            self.assertEqual(res2['A'],[[5,-1,0],[-1,5,-1],[0,-1,4]])
            self.assertEqual(res2['b'],[20,30,25])
            self.assertEqual(res2['metodos'],[legacy['metodos'][0],legacy['metodos'][2]])
            for nombre in ('jacobi.csv','gauss_jordan_operaciones.csv'):
                self.assertEqual((p/'explicito/datos/resultados'/nombre).read_bytes(),
                                 (RAIZ/'datos/resultados'/nombre).read_bytes())
            for nombre in ('jacobi.csv','gauss_seidel.csv','gauss_jordan_operaciones.csv','comparacion.csv'):
                self.assertEqual((p/'datos/resultados'/nombre).read_bytes(),
                                 (RAIZ/'datos/resultados'/nombre).read_bytes())

    def test_11_1_niveles_anteriores_distintos_de_x0(self):
        with tempfile.TemporaryDirectory() as d:
            r=self.ejecutar('resolver','--problema','11.1','--alpha','.5',
                '--niveles-anteriores','4','2','0','--x0','1','1','1','--salida',d,'--sin-graficas')
            self.assertEqual(r.returncode,0,r.stderr)
            res=json.loads((Path(d)/'datos/resultados/11_1/resumen.json').read_text())
            self.assertEqual(res['b'],[4,2,0])
            self.assertEqual(res['parametros']['x0'],[1,1,1])
            self.assertEqual(res['A'],[[1.5,-.5,0],[-.5,2,-.5],[0,-.5,1.5]])
            self.assertEqual(res['graficas'],[])

    def test_parametros_de_problema_invalidos_no_generan_archivos(self):
        casos=[['--problema','12'],['--alpha','1'],
               ['--problema','11.2','--niveles-anteriores','3','2','1']]
        casos += [['--problema','11.1','--alpha',a] for a in ('0','-1','nan','inf','1e308')]
        casos += [['--problema','11.1','--niveles-anteriores',*b] for b in
                  (['1','2'],['-1','2','3'],['nan','2','3'])]
        casos += [['--problema','11.1',*kw] for kw in
                  (['--tol','0'],['--max-iter','0'],['--x0','nan','0','0'])]
        for args in casos:
            with self.subTest(args=args), tempfile.TemporaryDirectory() as d:
                r=self.ejecutar('resolver',*args,'--salida',d,'--sin-graficas')
                self.assertEqual(r.returncode,2)
                self.assertEqual(list(Path(d).iterdir()),[])

    def test_11_1_limite_no_es_convergencia(self):
        with tempfile.TemporaryDirectory() as d:
            r=self.ejecutar('resolver','--problema','11.1','--salida',d,'--max-iter','1','--sin-graficas')
            self.assertEqual(r.returncode,2)
            res=json.loads((Path(d)/'datos/resultados/11_1/resumen.json').read_text())
            self.assertTrue(all(not m['converge'] for m in res['metodos']))

    def test_captura_baudios_r4_y_opcion_legacy(self):
        from python.main import parser
        argumentos=['capturar','--salida','sin_hardware.csv']
        self.assertEqual(parser().parse_args(argumentos).baudios,115200)
        self.assertEqual(parser().parse_args(argumentos+['--baudios','9600']).baudios,9600)

    def test_qr_exige_contenido_explicito(self):
        q=importlib.import_module('python.qr')
        with tempfile.TemporaryDirectory() as d:
            with self.assertRaises(ValueError): q.generar('',Path(d)/'no.png')
            with self.assertRaises(ValueError): q.generar('   ',Path(d)/'no.png')

    def test_qr_protege_texto_existente(self):
        q=importlib.import_module('python.qr')
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'qr.png'
            texto=p.with_suffix('.contenido.txt')
            texto.write_text('Contenido anterior')
            with self.assertRaises(FileExistsError): q.generar('nuevo',p)
            self.assertEqual(texto.read_text(),'Contenido anterior')
            self.assertFalse(p.exists())

    def test_qr_cli_rechaza_endpoint_de_telemetria(self):
        with tempfile.TemporaryDirectory() as d:
            ruta=Path(d)/'no_crear.png'
            for url in ('https://host.invalid/api/v1/privado/telemetry',
                        ' \thttps://host.invalid/api/v1/privado/telemetry\n'):
                with self.subTest(url=url):
                    r=self.ejecutar('qr','--contenido',url,'--salida',str(ruta))
                    self.assertEqual(r.returncode,2,r.stderr)
                    self.assertFalse(ruta.exists())
                    self.assertNotIn('privado',r.stderr)

    def test_cadencia_cli_distingue_burst_de_recepcion_normal(self):
        with tempfile.TemporaryDirectory() as d:
            ruta=Path(d)/'CADENCIA_SINTETICA.csv'
            texto=('timestamp_utc,t_ms,adc1,adc2,adc3,origen\n'
                   '2026-01-01T00:00:00+00:00,500,1,2,3,prueba_controlada\n'
                   '2026-01-01T00:00:00.500000+00:00,1000,1,2,3,prueba_controlada\n')
            ruta.write_text(texto)
            r=self.ejecutar('cadencia','--csv',str(ruta))
            self.assertEqual(r.returncode,0,r.stderr)
            self.assertEqual(json.loads(r.stdout)['recepcion_ms']['mediana'],500)
            ruta.write_text(texto.replace('.500000','.000100'))
            r=self.ejecutar('cadencia','--csv',str(ruta))
            self.assertEqual(r.returncode,2,r.stderr)
            self.assertFalse(json.loads(r.stdout)['cadencia_compatible'])

    @unittest.skipUnless(importlib.util.find_spec('qrcode') and importlib.util.find_spec('cv2'),
                         'qrcode y OpenCV no disponibles: QR final pendiente')
    def test_qr_roundtrip_real(self):
        q=importlib.import_module('python.qr')
        with tempfile.TemporaryDirectory() as d:
            p=q.generar('PRUEBA_CONTROLADA_P11',Path(d)/'prueba.png')
            self.assertEqual(q.leer(p),'PRUEBA_CONTROLADA_P11')


if __name__=='__main__': unittest.main()
