"""Figuras PNG sin interfaz gráfica; datos académicos y experimentales separados."""
import csv
import os
from datetime import datetime, timedelta
from pathlib import Path

import numpy as np

os.environ.setdefault('MPLCONFIGDIR',str(Path(__file__).resolve().parents[1]/'.mplconfig'))
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

from .calibracion import cargar,convertir
from .comunicacion import parsear_linea


def _guardar(fig,ruta):
    ruta=Path(ruta)
    ruta.parent.mkdir(parents=True,exist_ok=True)
    fig.tight_layout(rect=(0,0,1,.96) if fig._suptitle else None)
    fig.savefig(ruta,dpi=160)
    plt.close(fig)
    return ruta



def academicas(resultados,carpeta):
    carpeta=Path(carpeta)
    iterativos=[r for r in resultados if r.historial]
    archivos=[]
    for campo,nombre,ylabel in (
        ('error_abs_inf','convergencia.png','Cambio ||h(k) − h(k−1)||∞ [u. académicas]'),
        ('residuo_inf','residuos.png','Residuo ||Ah − b||∞ [u. del balance académico]')):
        fig,ax=plt.subplots(figsize=(8,4.5))
        for r in iterativos:
            filas=[f for f in r.historial if f[campo] is not None]
            valores=np.array([f[campo] for f in filas])
            # Un cero exacto no tiene logaritmo; se omite, sin alterar el CSV.
            valores=np.where(valores>0,valores,np.nan)
            ax.semilogy([f['k'] for f in filas],valores,'o-',label=r.metodo)
        ax.set(title='Convergencia — sistema académico',xlabel='Iteración k',ylabel=ylabel)
        ax.grid(True,which='both',alpha=.3)
        ax.legend()
        archivos.append(_guardar(fig,carpeta/nombre))
    fig,axs=plt.subplots(1,len(iterativos),figsize=(12,4),squeeze=False)
    for ax,r in zip(axs[0],iterativos):
        for i in range(1,4):
            ax.plot([f['k'] for f in r.historial],[f[f'h{i}'] for f in r.historial],
                    'o-',label=f'h{i}')
        ax.set(title=r.metodo,xlabel='Iteración k',ylabel='Nivel [u. académicas]')
        ax.grid(alpha=.3); ax.legend()
    fig.suptitle('Aproximaciones del sistema académico')
    archivos.append(_guardar(fig,carpeta/'niveles_iteraciones.png'))
    fig,ax=plt.subplots(figsize=(8,4.5))
    posiciones=np.arange(3)
    ancho=.8/len(resultados)
    for j,r in enumerate(resultados):
        ax.bar(posiciones-.4+(j+.5)*ancho,r.x,ancho,label=r.metodo)
    ax.set(xticks=posiciones,xticklabels=['h1','h2','h3'],
           title='Soluciones — sistema académico',xlabel='Variable',ylabel='Nivel [u. académicas]')
    ax.legend(); ax.grid(axis='y',alpha=.3)
    archivos.append(_guardar(fig,carpeta/'comparacion_metodos.png'))
    return archivos


def mediciones(ruta_csv,ruta_png,calibracion=None):
    with Path(ruta_csv).open(encoding='utf-8',newline='') as f:
        filas=list(csv.DictReader(f))
    requeridas={'timestamp_utc','t_ms','adc1','adc2','adc3','origen'}
    if not filas or not requeridas.issubset(filas[0]):
        raise ValueError('CSV vacío o sin columnas de adquisición.')
    if any(None in fila or any(valor is None for valor in fila.values()) for fila in filas):
        raise ValueError('CSV con columnas faltantes o adicionales.')
    origenes={f['origen'] for f in filas}
    if len(origenes)!=1 or not origenes.issubset({'experimental','prueba_controlada'}):
        raise ValueError('El archivo debe tener un único origen conocido.')
    for fila in filas:
        parsear_linea(','.join(fila[c] for c in ('t_ms','adc1','adc2','adc3')))
    try:
        fechas=[datetime.fromisoformat(f['timestamp_utc']) for f in filas]
    except (ValueError,TypeError) as e:
        raise ValueError('Marcas de tiempo inválidas.') from e
    if any(t.tzinfo is None or t.utcoffset()!=timedelta(0) for t in fechas):
        raise ValueError('Se requiere zona horaria UTC.')
    tiempos=np.array([(t-fechas[0]).total_seconds() for t in fechas])
    if np.any(np.diff(tiempos)<0): raise ValueError('Marcas de tiempo no ordenadas.')
    cal=cargar(calibracion) if calibracion else None
    unidad=cal['unidad'] if cal else 'cuentas ADC, sin calibrar'
    fig,ax=plt.subplots(figsize=(9,4.5))
    for i in range(1,4):
        adc=np.array([int(f[f'adc{i}']) for f in filas])
        valores=convertir(adc,cal['sensores'][f'adc{i}']) if cal else adc
        ax.plot(tiempos,valores,'o-',label=f'Sensor {i}')
    etiqueta='Mediciones experimentales' if origenes=={'experimental'} else 'Prueba controlada — NO experimental'
    ax.set(title=etiqueta,xlabel='Tiempo desde primera recepción UTC [s]',
           ylabel=f'Nivel [{unidad}]' if cal else f'Lectura [{unidad}]')
    ax.legend(); ax.grid(alpha=.3)
    return _guardar(fig,ruta_png)
