import csv
import importlib
import tempfile
import unittest
from pathlib import Path

import numpy as np

A = np.array([[5., -1., 0.], [-1., 5., -1.], [0., -1., 4.]])
B = np.array([20., 30., 25.])
EXACTA = np.array([75/13, 115/13, 110/13])


class MetodosTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.m = importlib.import_module('python.metodos')

    def test_convergencia_y_referencia_independiente(self):
        for nombre in ('jacobi', 'gauss_seidel'):
            with self.subTest(nombre=nombre):
                r = getattr(self.m, nombre)(A, B, tol=1e-10)
                self.assertTrue(r.converge)
                np.testing.assert_allclose(r.x, EXACTA, atol=1e-10, rtol=0)
                np.testing.assert_allclose(r.x, np.linalg.solve(A, B), atol=1e-10, rtol=0)

    def test_convencion_profesor_y_primera_iteracion(self):
        j = self.m.jacobi(A, B)
        g = self.m.gauss_seidel(A, B)
        np.testing.assert_allclose([j.historial[1][f'h{i}'] for i in range(1,4)], [4,6,6.25])
        np.testing.assert_allclose([g.historial[1][f'h{i}'] for i in range(1,4)], [4,6.8,7.95])
        self.assertEqual(j.iteraciones, 9)
        self.assertEqual(g.iteraciones, 6)
        for r in (j, g):
            self.assertLess(r.historial[-1]['error_abs_inf'], .001)
            self.assertGreaterEqual(r.historial[-2]['error_abs_inf'], .001)

    def test_inicial_configurable_y_no_mutacion(self):
        x0 = np.ones(3)
        copia = A.copy()
        r = self.m.jacobi(A, B, x0=x0)
        self.assertEqual(r.historial[0]['h1'], 1)
        np.testing.assert_array_equal(A, copia)
        np.testing.assert_array_equal(x0, np.ones(3))

    def test_residuo_y_errores(self):
        np.testing.assert_array_equal(self.m.residuo(A, B, [4,6,6.25]), [-6,-10.25,-6])
        r = self.m.jacobi(A, B)
        self.assertEqual(r.historial[1]['error_abs_inf'], 6.25)
        self.assertEqual(r.historial[1]['error_rel_inf'], 1)
        np.testing.assert_allclose(r.residuo, A @ r.x - B, atol=0)

    def test_relativo_indefinido_sin_division_por_cero(self):
        r = self.m.jacobi(np.eye(2), [0,1])
        self.assertIsNone(r.historial[1]['error_rel_h1'])
        self.assertEqual(r.historial[1]['error_rel_inf'], 1)
        z = self.m.jacobi(np.eye(2), [0,0])
        self.assertIsNone(z.historial[-1]['error_rel_inf'])

    def test_no_convergencia(self):
        for f in (self.m.jacobi, self.m.gauss_seidel):
            r = f([[1,2],[2,1]], [1,1], max_iter=5)
            self.assertFalse(r.converge)
            self.assertEqual(r.iteraciones, 5)
            self.assertEqual(len(r.historial), 6)

    def test_entradas_invalidas(self):
        casos = [([1,2], [1,2]), ([[1,2]], [1]), ([], []),
                 ([[1,0],[0,1]], [1]), ([[float('nan')]], [1]),
                 ([[1]], [float('inf')]), ([[1]], [[1]])]
        for a,b in casos:
            for f in (self.m.jacobi, self.m.gauss_seidel, self.m.gauss_jordan):
                with self.subTest(a=a, f=f.__name__):
                    with self.assertRaises(ValueError): f(a,b)
        for kw in ({'tol':0}, {'tol':float('nan')}, {'max_iter':0},
                   {'max_iter':1.5}, {'x0':[1,2]}, {'x0':[float('inf')]*3}):
            with self.subTest(kw=kw):
                with self.assertRaises(ValueError): self.m.jacobi(A,B,**kw)
        with self.assertRaises(ValueError): self.m.jacobi([[0,1],[1,1]],[1,2])

    def test_gauss_jordan_solucion_y_operaciones(self):
        r = self.m.gauss_jordan(A,B)
        np.testing.assert_allclose(r.x, EXACTA, atol=1e-12, rtol=0)
        np.testing.assert_allclose(r.operaciones[-1]['matriz'][:,:3], np.eye(3), atol=1e-12)
        self.assertLess(np.linalg.norm(r.residuo,np.inf),1e-12)

    def test_pivoteo_y_singularidad(self):
        for a,b in (([[0,1],[2,3]],[1,5]), ([[1e-20,1],[2,3]],[1,5])):
            np.testing.assert_allclose(self.m.gauss_jordan(a,b).x,[1,1],atol=1e-12)
        for a in ([[1,2],[2,4]], [[0,0],[0,0]]):
            with self.assertRaises(ValueError): self.m.gauss_jordan(a,[1,2])
        with self.assertRaises(ValueError): self.m.gauss_jordan([[1]], [1], pivot_tol=0)

    def test_exportacion_csv(self):
        r = self.m.jacobi(A,B)
        with tempfile.TemporaryDirectory() as d:
            p = Path(d)/'tabla.csv'
            self.m.exportar_tabla(r,p)
            with p.open() as f: filas = list(csv.DictReader(f))
            self.assertEqual(len(filas), r.iteraciones+1)
            self.assertEqual(filas[0]['error_abs_inf'], '')
            self.assertEqual(float(filas[1]['h1']), 4)
            self.assertIn('residuo_inf', filas[-1])

    def test_desbordamiento_residuo_no_se_verifica(self):
        with np.errstate(over='ignore',invalid='ignore'):
            with self.assertRaises(ValueError):
                self.m.gauss_jordan([[1e308,6e307],[7e307,3e307]],[-9e307,6e307])


if __name__ == '__main__': unittest.main()
