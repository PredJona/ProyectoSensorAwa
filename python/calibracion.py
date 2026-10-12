"""Interpolación lineal entre puntos ADC-altura medidos, por cada sensor."""
import json
from pathlib import Path

import numpy as np


def validar_puntos(puntos):
    p=np.asarray(puntos,dtype=float)
    if p.ndim!=2 or p.shape[1]!=2 or len(p)<2 or not np.isfinite(p).all():
        raise ValueError('Se requieren al menos dos pares finitos [ADC,altura].')
    if np.any(p[:,0]<0) or np.any(p[:,0]>1023) or np.any(p[:,1]<0):
        raise ValueError('ADC fuera de 0..1023 o altura negativa.')
    if np.any(np.diff(p[:,0])<=0) or np.any(np.diff(p[:,1])<=0):
        raise ValueError('ADC y altura deben aumentar estrictamente; revise la calibración.')
    return p


def convertir(adc,puntos):
    p=validar_puntos(puntos)
    x=np.asarray(adc,dtype=float)
    if not np.isfinite(x).all() or np.any(x<p[0,0]) or np.any(x>p[-1,0]):
        raise ValueError('Lectura fuera del intervalo calibrado; no se extrapola.')
    return np.interp(x,p[:,0],p[:,1])


def cargar(ruta):
    contenido=json.loads(Path(ruta).read_text(encoding='utf-8'))
    if not isinstance(contenido,dict) or contenido.get('unidad') not in ('cm','mm','m','%'):
        raise ValueError('La calibración debe indicar unidad: cm, mm, m o %.')
    sensores=contenido.get('sensores',{})
    if not isinstance(sensores,dict) or set(sensores)!={'adc1','adc2','adc3'}:
        raise ValueError('Se requiere calibración independiente para adc1, adc2 y adc3.')
    for puntos in sensores.values(): validar_puntos(puntos)
    return contenido
