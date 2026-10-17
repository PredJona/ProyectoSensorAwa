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

    def test_sistema_11_1_y_conservacion_exacta(self):
        a,b = self.m.sistema_11_1()
        np.testing.assert_array_equal(a, [[2,-1,0],[-1,3,-1],[0,-1,2]])
        np.testing.assert_array_equal(b, [3,2,1])
        exacta = np.array([2.5,2,1.5])
        np.testing.assert_array_equal(a @ exacta, b)
        np.testing.assert_allclose(np.linalg.solve(a,b), exacta, atol=1e-14)
        self.assertEqual(exacta.sum(), b.sum())
        self.assertTrue(np.all(np.diag(a) > np.sum(np.abs(a),axis=1)-np.diag(a)))
        np.testing.assert_array_equal(self.m.A_VALIDACION, A)
        np.testing.assert_array_equal(self.m.B_VALIDACION, B)

    def test_11_1_iteraciones_errores_y_residuos(self):
        a,b = self.m.sistema_11_1()
        for metodo,primera,n in ((self.m.jacobi,[1.5,2/3,.5],14),
                                 (self.m.gauss_seidel,[1.5,7/6,13/12],9)):
            with self.subTest(metodo=metodo.__name__):
                r=metodo(a,b)
                self.assertTrue(r.converge)
                self.assertEqual(r.iteraciones,n)
                self.assertEqual(len(r.historial),n+1)
                np.testing.assert_allclose([r.historial[1][f'h{i}'] for i in range(1,4)],primera)
                np.testing.assert_allclose(r.x,[2.5,2,1.5],atol=.001,rtol=0)
                self.assertLess(r.historial[-1]['error_abs_inf'],.001)
                self.assertGreaterEqual(r.historial[-2]['error_abs_inf'],.001)
                self.assertLess(np.linalg.norm(r.residuo,np.inf),.001)
                # Columnas de A suman 1: defecto de suma = suma del residuo.
                self.assertAlmostEqual(r.x.sum()-b.sum(),r.residuo.sum(),places=13)
                self.assertLessEqual(abs(r.x.sum()-b.sum()),3*np.linalg.norm(r.residuo,np.inf)+1e-14)
                anterior=np.zeros(3)
                for fila in r.historial[1:]:
                    x=np.array([fila[f'h{i}'] for i in range(1,4)])
                    cambio=np.abs(x-anterior)
                    np.testing.assert_allclose([fila[f'error_abs_h{i}'] for i in range(1,4)],cambio)
                    np.testing.assert_allclose([fila[f'error_rel_h{i}'] for i in range(1,4)],cambio/abs(x))
                    np.testing.assert_allclose([fila[f'r{i}'] for i in range(1,4)],a@x-b)
                    self.assertAlmostEqual(fila['error_rel_inf'],max(cambio)/max(abs(x)))
                    anterior=x

    def test_11_1_parametros_y_copias_independientes(self):
        niveles=np.array([4.,2.,0.])
        a,b=self.m.sistema_11_1(.5,niveles)
        np.testing.assert_array_equal(a,[[1.5,-.5,0],[-.5,2,-.5],[0,-.5,1.5]])
        self.assertAlmostEqual(np.linalg.solve(a,b).sum(),6)
        b[0]=99
        self.assertEqual(niveles[0],4)
        np.testing.assert_array_equal(self.m.sistema_11_1()[1],[3,2,1])
        for alpha in (.01,2,100):
            a,b=self.m.sistema_11_1(alpha,[5,5,5])
            np.testing.assert_allclose(np.linalg.solve(a,b),[5,5,5],atol=1e-12)

    def test_11_1_rechaza_parametros_invalidos(self):
        for alpha in (0,-1,float('inf'),float('nan'),1e308,True):
            with self.subTest(alpha=alpha), self.assertRaises(ValueError):
                self.m.sistema_11_1(alpha)
        for niveles in ([1,2],[1,2,float('nan')],[1,2,float('inf')],[-1,2,3],[[1,2,3]]):
            with self.subTest(niveles=niveles), self.assertRaises(ValueError):
                self.m.sistema_11_1(niveles_anteriores=niveles)


if __name__ == '__main__': unittest.main()
