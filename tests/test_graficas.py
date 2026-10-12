import csv
import importlib
import tempfile
import unittest
from pathlib import Path

from python.metodos import A_VALIDACION as A, B_VALIDACION as B, jacobi, gauss_seidel, gauss_jordan


class GraficasTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls): cls.g=importlib.import_module('python.graficas')

    def test_png_academicos(self):
        with tempfile.TemporaryDirectory() as d:
            archivos=self.g.academicas([jacobi(A,B),gauss_seidel(A,B),gauss_jordan(A,B)],d)
            self.assertEqual(len(archivos),4)
            for p in archivos:
                self.assertEqual(Path(p).read_bytes()[:8],b'\x89PNG\r\n\x1a\n')
                self.assertGreater(Path(p).stat().st_size,5000)

    def test_mediciones_controladas_y_reinicio(self):
        with tempfile.TemporaryDirectory() as d:
            csvpath=Path(d)/'entradas_controladas.csv'
            csvpath.write_text('timestamp_utc,t_ms,adc1,adc2,adc3,origen\n'
                '2026-10-12T00:00:00+00:00,4294967295,100,200,300,prueba_controlada\n'
                '2026-10-12T00:00:01+00:00,2,200,300,400,prueba_controlada\n')
            p=self.g.mediciones(csvpath,Path(d)/'prueba.png')
            self.assertEqual(p.read_bytes()[:8],b'\x89PNG\r\n\x1a\n')

    def test_mediciones_vacias_invalidas(self):
        with tempfile.TemporaryDirectory() as d:
            for contenido in ('','t_ms,adc1\n1,100\n'):
                p=Path(d)/'vacio.csv'; p.write_text(contenido)
                with self.assertRaises(ValueError): self.g.mediciones(p,Path(d)/'no.png')


if __name__=='__main__': unittest.main()
