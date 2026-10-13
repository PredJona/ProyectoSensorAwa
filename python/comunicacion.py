"""USB UNO R4 a 115200: tiempo_ms,sensor1,sensor2,sensor3; admite cabecera anterior."""
import csv
import io
import time
from datetime import datetime, timezone
from pathlib import Path

CABECERA='tiempo_ms,sensor1,sensor2,sensor3'
CABECERA_LEGACY='t_ms,adc1,adc2,adc3'


def parsear_linea(linea):
    if isinstance(linea,bytes):
        try: linea=linea.decode('ascii')
        except UnicodeDecodeError as e: raise ValueError('La línea no es ASCII.') from e
    linea=linea.strip()
    if linea in (CABECERA,CABECERA_LEGACY): return None
    partes=linea.split(',')
    if len(partes)!=4 or any(not p.isascii() or not p.isdigit() for p in partes):
        raise ValueError('Se requieren cuatro enteros sin signo separados por comas.')
    valores=tuple(int(p) for p in partes)
    if valores[0]>4294967295 or any(v>1023 for v in valores[1:]):
        raise ValueError('Millis o ADC fuera de rango.')
    return valores


def puertos_disponibles():
    from serial.tools import list_ports
    return [(p.device,p.description) for p in list_ports.comports()]


def registrar(fuente,ruta,max_muestras=100,duracion=60.,origen='experimental'):
    """Recibe un puerto con read(size) o un archivo binario de prueba.

    Vacíos seriales son timeout; en archivos son EOF. Los fragmentos se unen
    hasta newline. Un límite temporal impide esperas indefinidas. Cada fila se
    vacía a disco; si ocurre OSError/SerialException, el CSV parcial se conserva.
    """
    if not isinstance(max_muestras,int) or isinstance(max_muestras,bool) or max_muestras<=0:
        raise ValueError('max_muestras debe ser un entero positivo.')
    if not isinstance(duracion,(float,int)) or not 0<duracion<float('inf'):
        raise ValueError('duracion debe ser positiva y finita.')
    if origen not in ('experimental','prueba_controlada'):
        raise ValueError('Origen desconocido.')
    ruta=Path(ruta)
    ruta.parent.mkdir(parents=True,exist_ok=True)
    n=invalidos=0
    inicio=time.monotonic()
    pendiente=b''
    descartando=False
    with ruta.open('x',newline='',encoding='utf-8') as f:
        w=csv.writer(f)
        w.writerow(['timestamp_utc','t_ms','adc1','adc2','adc3','origen'])
        f.flush()
        while n<max_muestras and time.monotonic()-inicio<duracion:
            # read(1) permite revisar el plazo incluso con bytes continuos sin
            # newline. readline() reinicia esperas internas y puede bloquear.
            fragmento=fuente.read(1)
            if not fragmento:
                if isinstance(fuente,io.IOBase): break
                time.sleep(.005)
                continue
            if not isinstance(fragmento,bytes):
                raise ValueError('La fuente debe entregar bytes.')
            if descartando:
                if b'\n' not in fragmento: continue
                fragmento=fragmento.split(b'\n',1)[1]
                descartando=False
            pendiente+=fragmento
            while b'\n' in pendiente and n<max_muestras:
                linea,pendiente=pendiente.split(b'\n',1)
                try: valores=parsear_linea(linea)
                except ValueError:
                    invalidos+=1
                    continue
                if valores is None: continue
                w.writerow([datetime.now(timezone.utc).isoformat(),*valores,origen])
                f.flush()
                n+=1
            if len(pendiente)>256:
                invalidos+=1
                pendiente=b''
                descartando=True
        if pendiente: invalidos+=1  # Línea incompleta al cerrar, nunca se registra.
    return n,invalidos


def capturar(puerto,ruta,max_muestras=100,duracion=60.,baudios=115200):
    import serial
    if puerto is None:
        disponibles=puertos_disponibles()
        if len(disponibles)!=1:
            raise ValueError(f'Indique --puerto; puertos detectados: {disponibles}')
        puerto=disponibles[0][0]
    # Timeout por byte acotado. La apertura puede reiniciar Arduino.
    with serial.Serial(puerto,baudios,timeout=min(1.,duracion)) as s:
        return registrar(s,ruta,max_muestras,duracion,origen='experimental')
