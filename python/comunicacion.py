"""USB UNO R4 a 115200: tiempo_ms,sensor1,sensor2,sensor3; admite cabecera anterior."""
import csv
import io
import json
import time
import os
import tempfile
from datetime import datetime, timezone
from pathlib import Path

CABECERA='tiempo_ms,sensor1,sensor2,sensor3'
CABECERA_LEGACY='t_ms,adc1,adc2,adc3'


def guardar_json_atomico(ruta, contenido):
    """Reemplazo atómico: un fallo deja el diagnóstico/cursor anterior legible."""
    ruta=Path(ruta)
    ruta.parent.mkdir(parents=True,exist_ok=True)
    with tempfile.NamedTemporaryFile(mode='w',dir=ruta.parent,prefix='.'+ruta.name,
                                     suffix='.tmp',encoding='utf-8',delete=False) as f:
        temporal=Path(f.name)
        try:
            json.dump(contenido,f,indent=2,ensure_ascii=False,allow_nan=False)
            f.write('\n')
            f.flush()
            os.fsync(f.fileno())
        except BaseException:
            temporal.unlink(missing_ok=True)
            raise
    try:
        temporal.replace(ruta)
    finally:
        temporal.unlink(missing_ok=True)


def _validar_captura(max_muestras,duracion):
    if not isinstance(max_muestras,int) or isinstance(max_muestras,bool) or max_muestras<=0:
        raise ValueError('max_muestras debe ser un entero positivo.')
    if isinstance(duracion,bool) or not isinstance(duracion,(float,int)) or not 0<duracion<float('inf'):
        raise ValueError('duracion debe ser positiva y finita.')


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


def _intervalo(anterior, actual, recibido_anterior, recibido):
    delta = (actual - anterior) % 2**32
    real = (recibido - recibido_anterior) * 1000
    if actual < anterior and not (anterior > 2**32-2000 and actual < 2000):
        return 'reinicio probable o datos reordenados'
    if not 450 <= delta <= 650:
        return 'salto temporal del contador Arduino'
    if not 350 <= real <= 750 or abs(delta-real) > 150:
        return 'cadencia de recepción incompatible (acumulación o retraso)'
    return None


def registrar(fuente,ruta,max_muestras=100,duracion=60.,origen='experimental',
              sincronizar=None, timeout_sincronizacion=12., timeout_inactivo=3.):
    """Recibe un puerto con read(size) o un archivo binario de prueba.

    Las capturas experimentales siempre sincronizan. Una prueba puede optar
    por flujo crudo (sincronizar=False). La sincronización descarta hasta LF y
    exige cuatro intervalos consecutivos compatibles con 500 ms reales.
    La primera fila registrada es la que confirma esa condición. No hay más
    vaciados después de ella. duracion cuenta desde ese inicio efectivo.
    Una discontinuidad termina la sesión conservando CSV y diagnóstico.
    """
    _validar_captura(max_muestras,duracion)
    if origen not in ('experimental','prueba_controlada'):
        raise ValueError('Origen desconocido.')
    if sincronizar is None:
        sincronizar = origen == 'experimental'
    if origen == 'experimental' and not sincronizar:
        raise ValueError('Una captura experimental requiere sincronización.')
    for valor in (timeout_sincronizacion, timeout_inactivo):
        if isinstance(valor,bool) or not isinstance(valor,(int,float)) or not 0 < valor < float('inf'):
            raise ValueError('Los timeouts deben ser positivos y finitos.')
    if sincronizar and (not hasattr(fuente,'timeout') or fuente.timeout is None or
                        not 0 < fuente.timeout <= .1):
        raise ValueError('La sincronización requiere read con timeout entre 0 y 0.1 s.')
    ruta=Path(ruta)
    ruta.parent.mkdir(parents=True,exist_ok=True)
    n=invalidos=0
    inicio=time.monotonic()
    efectivo = None if sincronizar else inicio
    anterior = None
    racha = 0
    base_sync = None
    transcurrido_arduino = 0
    utc_base = None
    informe = {'version':1, 'origen':origen, 'sincronizacion_requerida':bool(sincronizar),
               'inicio_efectivo_utc':None, 'descartadas_sincronizacion':0,
               'desbordamientos_compatibles':0, 'estado':'sincronizando' if sincronizar else 'crudo'}
    sesion = ruta.with_suffix('.sesion.json')
    if sincronizar and sesion.exists():
        raise FileExistsError(f'El diagnóstico ya existe: {sesion}')
    pendiente=b''
    descartando=bool(sincronizar)
    with ruta.open('x',newline='',encoding='utf-8') as f:
        # Reservar el diagnóstico sin sobrescribir otra sesión.
        if sincronizar:
            with sesion.open('x',encoding='utf-8') as meta:
                json.dump(informe,meta)
        w=csv.writer(f)
        w.writerow(['timestamp_utc','t_ms','adc1','adc2','adc3','origen'])
        f.flush()
        try:
            if sincronizar and hasattr(fuente,'reset_input_buffer'):
                fuente.reset_input_buffer()
            while n<max_muestras:
                ahora = time.monotonic()
                if efectivo is None:
                    if ahora-inicio >= timeout_sincronizacion:
                        raise TimeoutError('No se logró sincronización con datos nuevos a 500 ms.')
                elif ahora-efectivo >= duracion:
                    break
                elif sincronizar and anterior and ahora-anterior[1] >= timeout_inactivo:
                    raise TimeoutError('No llegan datos nuevos; se conserva el CSV parcial.')
                # read(1) permite revisar el plazo incluso con bytes continuos
                # sin LF. readline() reinicia esperas internas y puede bloquear.
                fragmento=fuente.read(1)
                if not fragmento:
                    # PySerial hereda IOBase: un vacío con timeout no es EOF.
                    if isinstance(fuente,io.IOBase) and not hasattr(fuente,'timeout'): break
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
                    recibido = time.monotonic()
                    utc = datetime.now(timezone.utc)
                    try: valores=parsear_linea(linea)
                    except ValueError:
                        invalidos+=1
                        if efectivo is None:
                            anterior=None
                            racha=0
                        continue
                    if valores is None:
                        if sincronizar and efectivo is not None:
                            raise RuntimeError('Cabecera durante captura: reinicio probable del Arduino.')
                        anterior=None
                        racha=0
                        continue
                    if sincronizar:
                        error = _intervalo(anterior[0],valores[0],anterior[1],recibido) if anterior else None
                        if efectivo is None:
                            informe['descartadas_sincronizacion'] += 1
                            if anterior is None or error:
                                racha=0
                                base_sync=(valores[0],recibido)
                            else:
                                racha+=1
                                avance=(valores[0]-base_sync[0]) % 2**32
                                if abs(avance-(recibido-base_sync[1])*1000)>150:
                                    racha=0
                                    base_sync=(valores[0],recibido)
                            anterior=(valores[0],recibido)
                            if racha<4: continue
                            efectivo=recibido
                            utc_base=utc
                            informe['inicio_efectivo_utc']=utc.isoformat()
                            informe['descartadas_sincronizacion']-=1
                            informe['estado']='capturando'
                            guardar_json_atomico(sesion,informe)
                        else:
                            if error: raise RuntimeError(error)
                            transcurrido_arduino+=(valores[0]-anterior[0]) % 2**32
                            if abs(transcurrido_arduino-(recibido-efectivo)*1000)>250:
                                raise RuntimeError('Deriva temporal acumulada incompatible con captura continua.')
                            if abs((utc-utc_base).total_seconds()-(recibido-efectivo))>.25:
                                raise RuntimeError('Salto temporal del reloj UTC del PC.')
                            if valores[0]<anterior[0]:
                                informe['desbordamientos_compatibles']+=1
                        anterior=(valores[0],recibido)
                    w.writerow([utc.isoformat(),*valores,origen])
                    f.flush()
                    n+=1
                if len(pendiente)>256:
                    invalidos+=1
                    pendiente=b''
                    descartando=True
            informe['estado']='finalizada'
        except BaseException as e:
            informe['estado']='interrumpida'
            informe['error']=f'{type(e).__name__}: {e}'
            raise
        finally:
            if pendiente: invalidos+=1
            if sincronizar:
                informe.update(muestras=n,lineas_invalidas=invalidos,
                               segundos_desde_apertura=time.monotonic()-inicio,
                               segundos_captura=time.monotonic()-efectivo if efectivo is not None else 0)
                guardar_json_atomico(sesion,informe)
    return n,invalidos


def capturar(puerto,ruta,max_muestras=100,duracion=60.,baudios=115200,
             timeout_sincronizacion=12.,timeout_inactivo=3.):
    _validar_captura(max_muestras,duracion)
    if isinstance(baudios,bool) or not isinstance(baudios,int) or baudios<=0:
        raise ValueError('baudios debe ser un entero positivo.')
    import serial
    if puerto is None:
        disponibles=puertos_disponibles()
        if len(disponibles)!=1:
            raise ValueError(f'Indique --puerto; puertos detectados: {disponibles}')
        puerto=disponibles[0][0]
    # Timeout por byte acotado. La apertura puede reiniciar Arduino.
    if Path(ruta).exists() or Path(ruta).with_suffix('.sesion.json').exists():
        raise FileExistsError(f'El destino ya existe: {ruta}')
    with serial.Serial(puerto,baudios,timeout=min(.05,duracion),exclusive=True) as s:
        return registrar(s,ruta,max_muestras,duracion,origen='experimental',
                         timeout_sincronizacion=timeout_sincronizacion,timeout_inactivo=timeout_inactivo)


def verificar_cadencia(ruta):
    """Informe de recepción UTC y contador modular; no cambia el CSV."""
    from statistics import median
    with Path(ruta).open(encoding='utf-8',newline='') as f:
        lector=csv.DictReader(f)
        if tuple(lector.fieldnames or ())!=('timestamp_utc','t_ms','adc1','adc2','adc3','origen'):
            raise ValueError('Columnas CSV inválidas para comprobar cadencia.')
        filas=list(lector)
    if any(None in fila or any(v is None for v in fila.values()) for fila in filas):
        raise ValueError('Fila CSV incompleta.')
    if len(filas)<2: raise ValueError('Se necesitan al menos dos muestras para verificar cadencia.')
    fechas=[datetime.fromisoformat(f['timestamp_utc']) for f in filas]
    if any(fecha.utcoffset() is None or fecha.utcoffset().total_seconds()!=0 for fecha in fechas):
        raise ValueError('Las marcas de recepción deben estar en UTC.')
    contadores=[parsear_linea(','.join(f[k] for k in ('t_ms','adc1','adc2','adc3')))[0] for f in filas]
    utc=[(b-a).total_seconds()*1000 for a,b in zip(fechas,fechas[1:])]
    arduino=[(b-a)%2**32 for a,b in zip(contadores,contadores[1:])]
    problemas=[i+2 for i,(a,b) in enumerate(zip(arduino,utc))
               if _intervalo(contadores[i],contadores[i+1],0,b/1000)]
    return {'muestras':len(filas),'recepcion_ms':{'min':min(utc),'mediana':median(utc),'max':max(utc)},
            'arduino_ms':{'min':min(arduino),'mediana':median(arduino),'max':max(arduino)},
            'filas_con_discontinuidad':problemas,'cadencia_compatible':not problemas}
