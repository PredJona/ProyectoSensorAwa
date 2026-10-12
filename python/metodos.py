"""Métodos de clase: norma infinito del cambio < tol, sin redondeo interno."""
import csv
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np

A_VALIDACION = np.array([[5., -1., 0.], [-1., 5., -1.], [0., -1., 4.]])
B_VALIDACION = np.array([20., 30., 25.])


@dataclass
class Resultado:
    metodo: str
    x: np.ndarray
    residuo: np.ndarray
    converge: bool
    motivo: str
    historial: list = field(default_factory=list)
    operaciones: list = field(default_factory=list)

    @property
    def iteraciones(self):
        return len(self.historial)-1 if self.historial else 0


def validar_sistema(A, b):
    A = np.array(A, dtype=float, copy=True)
    b = np.array(b, dtype=float, copy=True)
    if A.ndim != 2 or A.shape[0] != A.shape[1] or not A.size:
        raise ValueError('A debe ser cuadrada y no vacía.')
    if b.ndim != 1 or b.shape != (len(A),):
        raise ValueError('b debe ser un vector con un valor por ecuación.')
    if not np.isfinite(A).all() or not np.isfinite(b).all():
        raise ValueError('A y b deben contener números finitos.')
    return A, b


def residuo(A, b, x):
    A, b = validar_sistema(A, b)
    x = np.asarray(x, dtype=float)
    if x.shape != b.shape or not np.isfinite(x).all():
        raise ValueError('x debe ser un vector finito compatible con b.')
    return A @ x - b


def _fila(k, x, anterior, A, b):
    fila = {'k': k}
    fila.update({f'h{i+1}': float(v) for i,v in enumerate(x)})
    cambio = None if anterior is None else np.abs(x-anterior)
    for i in range(len(x)):
        fila[f'error_abs_h{i+1}'] = None if cambio is None else float(cambio[i])
        fila[f'error_rel_h{i+1}'] = (
            None if cambio is None or x[i] == 0 else float(cambio[i]/abs(x[i])))
    norma = float(np.linalg.norm(x, np.inf))
    fila['error_abs_inf'] = None if cambio is None else float(max(cambio))
    fila['error_rel_inf'] = (
        None if cambio is None or norma == 0 else float(max(cambio)/norma))
    r = A @ x - b
    fila.update({f'r{i+1}': float(v) for i,v in enumerate(r)})
    fila['residuo_inf'] = float(np.linalg.norm(r, np.inf))
    return fila


def _iterar(A, b, x0, tol, max_iter, seidel):
    A, b = validar_sistema(A,b)
    if not np.isfinite(tol) or tol <= 0:
        raise ValueError('tol debe ser positiva y finita.')
    if isinstance(max_iter, bool) or not isinstance(max_iter, (int,np.integer)) or max_iter <= 0:
        raise ValueError('max_iter debe ser un entero positivo.')
    if np.any(np.diag(A) == 0):
        raise ValueError('Diagonal nula: no se puede despejar la incógnita.')
    x = np.zeros(len(b)) if x0 is None else np.array(x0,dtype=float,copy=True)
    if x.shape != b.shape or not np.isfinite(x).all():
        raise ValueError('x0 debe ser un vector finito compatible con b.')
    historial = [_fila(0,x,None,A,b)]
    nombre = 'Gauss-Seidel' if seidel else 'Jacobi'
    for k in range(1,max_iter+1):
        anterior = x.copy()
        nuevo = anterior.copy()
        with np.errstate(over='ignore',invalid='ignore',divide='ignore'):
            for i in range(len(b)):
                izquierda = nuevo[:i] if seidel else anterior[:i]
                suma = A[i,:i] @ izquierda + A[i,i+1:] @ anterior[i+1:]
                nuevo[i] = (b[i]-suma)/A[i,i]
        if not np.isfinite(nuevo).all():
            return Resultado(nombre,x,A@x-b,False,
                             f'Valores no finitos en el intento {k}.',historial)
        x = nuevo
        historial.append(_fila(k,x,anterior,A,b))
        if historial[-1]['error_abs_inf'] < tol:
            return Resultado(nombre,x,A@x-b,True,'Cambio menor que tol.',historial)
    return Resultado(nombre,x,A@x-b,False,'Máximo de iteraciones alcanzado.',historial)


def jacobi(A, b, x0=None, tol=.001, max_iter=100):
    return _iterar(A,b,x0,tol,max_iter,False)


def gauss_seidel(A, b, x0=None, tol=.001, max_iter=100):
    return _iterar(A,b,x0,tol,max_iter,True)


def gauss_jordan(A, b, pivot_tol=1e-12):
    """Pivoteo parcial y operaciones sobre [A|b], con umbral relativo a A."""
    A,b = validar_sistema(A,b)
    if not np.isfinite(pivot_tol) or pivot_tol <= 0:
        raise ValueError('pivot_tol debe ser positiva y finita.')
    M = np.column_stack((A,b))
    umbral = pivot_tol * np.max(np.abs(A))
    operaciones = [{'operacion':'Matriz inicial [A|b]', 'matriz':M.copy()}]

    def guardar(texto):
        if not np.isfinite(M).all():
            raise ValueError('Desbordamiento durante Gauss-Jordan.')
        operaciones.append({'operacion':texto,'matriz':M.copy()})

    for k in range(len(b)):
        p = k + int(np.argmax(np.abs(M[k:,k])))
        if abs(M[p,k]) <= umbral:
            raise ValueError('Pivote nulo o pequeño: sistema singular o mal condicionado.')
        if p != k:
            M[[k,p]] = M[[p,k]]
            guardar(f'F{k+1} <-> F{p+1}')
        pivote = M[k,k]
        M[k] /= pivote
        guardar(f'F{k+1} <- F{k+1} / ({pivote:.17g})')
        for i in range(len(b)):
            if i == k: continue
            factor = M[i,k]
            if factor == 0: continue
            M[i] -= factor*M[k]
            guardar(f'F{i+1} <- F{i+1} - ({factor:.17g}) F{k+1}')
    x = M[:,-1].copy()
    # Un desbordamiento no puede certificar una solución: inf <= inf sería True.
    with np.errstate(over='ignore',invalid='ignore'):
        r = A @ x-b
        escala = np.linalg.norm(A,np.inf)*np.linalg.norm(x,np.inf)+np.linalg.norm(b,np.inf)
    if not np.isfinite(r).all() or not np.isfinite(escala):
        raise ValueError('Desbordamiento al verificar el residuo de Gauss-Jordan.')
    # Comprobación independiente de las filas reducidas: error hacia atrás escalado.
    correcto = np.linalg.norm(r,np.inf) <= 100*np.finfo(float).eps*escala
    return Resultado('Gauss-Jordan',x,r,bool(correcto),
                     'Residuo verificado.' if correcto else 'Residuo excesivo.',
                     operaciones=operaciones)


def exportar_tabla(resultado, ruta):
    if not resultado.historial:
        raise ValueError('El método no tiene tabla iterativa.')
    ruta = Path(ruta)
    ruta.parent.mkdir(parents=True,exist_ok=True)
    with ruta.open('w',newline='',encoding='utf-8') as f:
        writer = csv.DictWriter(f,fieldnames=list(resultado.historial[0]))
        writer.writeheader()
        writer.writerows(resultado.historial)
