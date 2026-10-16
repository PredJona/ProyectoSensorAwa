"""Publicador HTTP ThingsBoard y validación de URL para QR, sin bloquear captura serial."""
import csv
import hashlib
import http.client
import json
import os
import io
import ipaddress
import re
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timedelta, timezone
from pathlib import Path

from .calibracion import cargar as cargar_calibracion, convertir, validar_puntos
from .comunicacion import parsear_linea, guardar_json_atomico

RAIZ = Path(__file__).resolve().parents[1]
COLUMNAS_CSV = ('timestamp_utc', 't_ms', 'adc1', 'adc2', 'adc3', 'origen')
PLACEHOLDERS = ('TOKEN', 'TU_TOKEN', 'CONTENIDO_CONFIRMADO', 'SERVIDOR', 'EJEMPLO', '<', '>')


def color_provisional_adc(adc):
    """Clasificación provisional idéntica a ColoresNivel.h (cuentas ADC, no altura)."""
    if not isinstance(adc, int) or isinstance(adc, bool) or adc < 0 or adc > 1023:
        return 'apagado'
    if adc < 50:
        return 'verde'
    if adc < 150:
        return 'azul'
    if adc < 300:
        return 'morado'
    return 'rojo'


def _validar_servidor(servidor):
    if not isinstance(servidor, str) or not servidor.strip():
        raise ValueError('Indique la URL base del servidor ThingsBoard (http:// o https://).')
    limpio = servidor.strip().rstrip('/')
    partes = urllib.parse.urlsplit(limpio)
    if partes.scheme not in ('http', 'https') or not partes.netloc:
        raise ValueError('La URL del servidor ThingsBoard debe incluir esquema http(s) y host.')
    if partes.query or partes.fragment:
        raise ValueError('La URL base del servidor no debe contener query ni fragmento.')
    if partes.username or partes.password or partes.path:
        raise ValueError('La URL base no admite credenciales ni rutas.')
    if partes.scheme != 'https' and partes.hostname not in ('localhost','127.0.0.1','::1'):
        raise ValueError('Use HTTPS para proteger el token; HTTP se admite solo en localhost para pruebas.')
    return limpio


def _validar_token(token):
    if not isinstance(token, str) or not token.strip():
        raise ValueError('Se requiere el token de dispositivo ThingsBoard (fuera de Git).')
    limpio = token.strip()
    if not re.fullmatch(r'[A-Za-z0-9._~-]+', limpio):
        raise ValueError('Token de dispositivo inválido.')
    upper = limpio.upper()
    if upper in PLACEHOLDERS or any(p in upper for p in ('TU_TOKEN', 'CONTENIDO_CONFIRMADO', '<', '>')):
        raise ValueError('Sustituya la plantilla por un token real privado.')
    return limpio


def url_endpoint(servidor, token):
    base = _validar_servidor(servidor)
    tok = _validar_token(token)
    return f'{base}/api/v1/{tok}/telemetry'


def url_redactada(servidor):
    base = _validar_servidor(servidor)
    return f'{base}/api/v1/***/telemetry'


def validar_url_dashboard(url, token=None, permitir_local=False):
    """Valida que la URL para el QR sea un dashboard real y no filtre tokens."""
    if not isinstance(url, str) or not url.strip():
        raise ValueError('Indique una URL de dashboard configurada para el QR.')
    limpia = url.strip()
    upper = limpia.upper()
    if any(p in upper for p in PLACEHOLDERS):
        raise ValueError('La URL del dashboard contiene texto de plantilla no confirmado.')
    partes = urllib.parse.urlsplit(limpia)
    if partes.scheme not in ('http', 'https') or not partes.netloc:
        raise ValueError('La URL del dashboard debe usar http:// o https:// con un host válido.')
    if partes.username or partes.password:
        raise ValueError('La URL del dashboard no debe incluir credenciales.')
    if any(k.lower() in ('token','access_token','password','secret')
           for k,_ in urllib.parse.parse_qsl(partes.query)):
        raise ValueError('La URL del dashboard no debe incluir secretos.')
    decodificada=urllib.parse.unquote(limpia)
    ruta_decodificada=urllib.parse.unquote(partes.path).lower()
    if '/api/v1/' in ruta_decodificada or ruta_decodificada.rstrip('/').endswith('/telemetry'):
        raise ValueError('Seguridad: no codifique el endpoint de telemetría ni el token en el QR.')
    if token and token.strip() and token.strip() in decodificada:
        raise ValueError('Seguridad: el token del dispositivo no debe aparecer en la URL del QR.')
    host = (partes.hostname or '').lower()
    local=host.rstrip('.')=='localhost'
    try:
        direccion=ipaddress.ip_address(host)
        local=local or direccion.is_loopback or direccion.is_unspecified
    except ValueError: pass
    if not permitir_local and local:
        raise ValueError('Una URL localhost no es accesible desde teléfonos externos mediante QR.')
    return limpia


def cargar_configuracion(ruta_config=None, servidor=None, token=None, dashboard_url=None):
    """Carga configuración desde archivo privado o variables de entorno sin exponer secretos."""
    datos = {}
    if ruta_config is not None:
        p = Path(ruta_config)
        contenido = json.loads(p.read_text(encoding='utf-8'))
        if not isinstance(contenido, dict):
            raise ValueError('El archivo de configuración debe contener un objeto JSON.')
        datos.update(contenido)
    srv = servidor if servidor is not None else (
        datos.get('servidor') or os.environ.get('THINGSBOARD_URL'))
    tok = token if token is not None else (
        datos.get('token') or os.environ.get('THINGSBOARD_TOKEN'))
    dash = dashboard_url if dashboard_url is not None else (
        datos.get('dashboard_url') or os.environ.get('THINGSBOARD_DASHBOARD_URL'))
    return {
        'servidor': _validar_servidor(srv) if srv else None,
        'token': _validar_token(tok) if tok else None,
        'dashboard_url': dash.strip() if isinstance(dash, str) and dash.strip() else None,
    }


def _portable_csv(ruta_csv):
    p = Path(ruta_csv).resolve()
    try:
        return p.relative_to(RAIZ.resolve()).as_posix()
    except ValueError:
        return p.name


def construir_telemetria_fila(fila, modo='historico', calibracion=None, csv_origen=None):
    """Transforma una fila validada del CSV en un objeto {ts, values} para ThingsBoard."""
    if modo not in ('historico', 'en_vivo'):
        raise ValueError("El modo debe ser 'historico' o 'en_vivo'.")
    if any(k not in fila or fila[k] is None for k in COLUMNAS_CSV) or None in fila:
        raise ValueError('Fila CSV incompleta o con columnas adicionales.')
    t_ms, adc1, adc2, adc3 = parsear_linea(','.join(str(fila[c]) for c in COLUMNAS_CSV[1:5]))
    origen = fila['origen']
    if origen not in ('experimental', 'prueba_controlada'):
        raise ValueError(f'Origen desconocido: {origen}')
    fecha = datetime.fromisoformat(fila['timestamp_utc'])
    if fecha.tzinfo is None or fecha.utcoffset() != timedelta(0):
        raise ValueError('timestamp_utc debe estar en zona horaria UTC.')
    ts_ms = int(round(fecha.timestamp() * 1000))
    adcs = {'adc1': adc1, 'adc2': adc2, 'adc3': adc3}
    valores = {
        'adc1': adc1,
        'adc2': adc2,
        'adc3': adc3,
        't_ms': t_ms,
        'color_adc1': color_provisional_adc(adc1),
        'color_adc2': color_provisional_adc(adc2),
        'color_adc3': color_provisional_adc(adc3),
        'calibracion_valida': False,
        'estado_calibracion': 'ADC sin calibrar; alturas fisicas no habilitadas',
        'origen': origen,
        'modo_transmision': modo,
        'es_tiempo_real': modo == 'en_vivo',
    }
    if csv_origen is not None:
        valores['csv_origen'] = str(csv_origen)
    if calibracion is not None:
        calibracion=_calibracion_validada(calibracion)
        unidad = calibracion['unidad']
        for i in range(1, 4):
            h = float(convertir([adcs[f'adc{i}']], calibracion['sensores'][f'adc{i}'])[0])
            valores[f'altura{i}'] = h
        valores['calibracion_valida'] = True
        valores['estado_calibracion'] = 'Calibracion interpolada dentro de rango'
        valores['unidad_altura'] = unidad
    return {'ts': ts_ms, 'values': valores}


def _leer_filas_csv(ruta_csv, permitir_prueba_controlada=False, creciendo=False):
    p = Path(ruta_csv)
    with p.open(encoding='utf-8', newline='') as f:
        texto=f.read()
        if creciendo:
            # Un escritor puede estar a mitad de fila. Solo consumir LF completos.
            texto=texto[:texto.rfind('\n')+1]
            if not texto: return []
        reader = csv.DictReader(io.StringIO(texto))
        if tuple(reader.fieldnames or ()) != COLUMNAS_CSV:
            raise ValueError(f'Columnas inválidas en {p}')
        filas = list(reader)
    if not filas and not creciendo:
        raise ValueError(f'CSV vacío sin muestras para publicar: {p}')
    fechas = []
    for fila in filas:
        if None in fila or any(v is None for v in fila.values()):
            raise ValueError(f'Fila malformada en {p}')
        parsear_linea(','.join(fila[c] for c in COLUMNAS_CSV[1:5]))
        if fila['origen'] not in ('experimental', 'prueba_controlada'):
            raise ValueError(f'Origen inválido en {p}')
        if fila['origen'] == 'prueba_controlada' and not permitir_prueba_controlada:
            raise ValueError('No se publican datos de prueba_controlada sin autorización explícita.')
        dt = datetime.fromisoformat(fila['timestamp_utc'])
        if dt.tzinfo is None or dt.utcoffset() != timedelta(0):
            raise ValueError(f'Marca temporal sin UTC en {p}')
        fechas.append(dt)
    epoch_ms=[int(round(f.timestamp()*1000)) for f in fechas]
    if any(b <= a for a,b in zip(epoch_ms,epoch_ms[1:])):
        raise ValueError('Cada muestra debe tener un milisegundo UTC distinto y creciente; '
                         'posible captura acumulada o reloj incorrecto. No se inventan tiempos.')
    return filas


def _hash_filas(filas):
    h = hashlib.sha256()
    for fila in filas:
        linea = ','.join(str(fila[k]) for k in COLUMNAS_CSV) + '\n'
        h.update(linea.encode('utf-8'))
    return h.hexdigest()


class _SinRedireccion(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def publicar_lote(servidor, token, lote, timeout=5.0, reintentos=3, espera_inicial_s=0.1):
    """Envía un lote JSON por HTTP POST con reintentos ante fallos transitorios."""
    if not isinstance(reintentos, int) or isinstance(reintentos, bool) or reintentos < 1:
        raise ValueError('reintentos debe ser un entero positivo.')
    if isinstance(timeout, bool) or not isinstance(timeout, (int, float)) or not 0 < timeout < float('inf'):
        raise ValueError('timeout debe ser positivo.')
    if isinstance(espera_inicial_s,bool) or not isinstance(espera_inicial_s,(int,float)) or not 0 <= espera_inicial_s < float('inf'):
        raise ValueError('La espera de reintentos debe ser finita y no negativa.')
    endpoint = url_endpoint(servidor, token)
    segura = url_redactada(servidor)
    ultimo_error = None
    cliente=urllib.request.build_opener(_SinRedireccion())
    for intento in range(1, reintentos + 1):
        # Si un reintento envejece un lote, no conservar una etiqueta de vivo.
        envio=[]
        for dato in lote:
            item={'ts':dato['ts'],'values':dict(dato['values'])}
            edad=datetime.now(timezone.utc).timestamp()-dato['ts']/1000
            if item['values'].get('modo_transmision')=='en_vivo' and not 0<=edad<=3:
                item['values'].update(modo_transmision='historico',es_tiempo_real=False)
            item['values']['edad_recepcion_s']=round(edad,3)
            envio.append(item)
        cuerpo=json.dumps(envio,ensure_ascii=False,allow_nan=False).encode('utf-8')
        req = urllib.request.Request(
            endpoint, data=cuerpo, method='POST',
            headers={'Content-Type': 'application/json; charset=utf-8'})
        try:
            with cliente.open(req, timeout=timeout) as resp:
                status = getattr(resp, 'status', 200)
                if 200 <= status < 300:
                    return intento
                raise RuntimeError(f'HTTP {status} inesperado desde {segura}')
        except urllib.error.HTTPError as e:
            codigo = e.code
            e.close()
            if codigo != 429 and codigo < 500:
                raise RuntimeError(
                    f'Rechazo permanente HTTP {codigo} en {segura} (verifique token/ruta).') from None
            ultimo_error = f'HTTP {codigo} en {segura}'

        except (urllib.error.URLError, TimeoutError, OSError, http.client.HTTPException) as e:
            ultimo_error = f'Fallo de conexión hacia {segura} ({type(e).__name__})'
        if intento < reintentos and espera_inicial_s > 0:
            time.sleep(espera_inicial_s * (2 ** (intento - 1)))
    raise ConnectionError(f'No se pudo publicar en {segura} tras {reintentos} intentos ({ultimo_error}).')


def _calibracion_validada(calibracion):
    if calibracion is None: return None
    cal = cargar_calibracion(calibracion) if isinstance(calibracion,(str,Path)) else calibracion
    if (not isinstance(cal,dict) or cal.get('validada') is not True or
        cal.get('unidad') not in ('cm','mm','m','%') or
        not isinstance(cal.get('sensores'),dict) or set(cal['sensores']) != {'adc1','adc2','adc3'}):
        raise ValueError('Calibración no validada: requiere validada=true y puntos independientes de tres sensores.')
    for puntos in cal['sensores'].values(): validar_puntos(puntos)
    return cal


def _identidad(servidor,token,ruta_csv,modo,cal):
    texto=json.dumps([url_endpoint(servidor,token),str(Path(ruta_csv).resolve()),modo,cal],sort_keys=True)
    return hashlib.sha256(texto.encode()).hexdigest()


def _publicar_filas(ruta_csv, filas, servidor, token, modo='historico', ruta_cursor=None,
                 calibracion=None, tamano_lote=20, timeout=5.0, reintentos=3,
                 espera_inicial_s=0.1, seguimiento=False):
    """Publica filas completas de un CSV local sin abrir el puerto serial."""
    if not isinstance(tamano_lote, int) or isinstance(tamano_lote, bool) or tamano_lote <= 0:
        raise ValueError('tamano_lote debe ser un entero positivo.')
    cal = _calibracion_validada(calibracion)
    identidad = _identidad(servidor,token,ruta_csv,modo,cal)
    origen_rel = _portable_csv(ruta_csv)
    enviadas = 0
    cursor_path = Path(ruta_cursor) if ruta_cursor is not None else None
    if cursor_path is not None and cursor_path.exists():
        estado = json.loads(cursor_path.read_text(encoding='utf-8'))
        if not isinstance(estado,dict):
            raise ValueError('Cursor malformado: se esperaba un objeto JSON.')
        if estado.get('configuracion_sha256') != identidad:
            raise ValueError('El cursor corresponde a otro destino o configuración; use un cursor distinto.')
        if estado.get('csv_origen') != origen_rel:
            raise ValueError('El cursor corresponde a otro archivo CSV.')
        prev = estado.get('filas_enviadas')
        if not isinstance(prev,int) or isinstance(prev,bool):
            raise ValueError('Cursor malformado: filas_enviadas debe ser entero.')
        if prev < 0 or prev > len(filas):
            raise ValueError('El cursor excede las filas del CSV actual.')
        if _hash_filas(filas[:prev]) != estado.get('sha256_prefijo'):
            raise ValueError('Las filas ya enviadas cambiaron respecto al cursor guardado.')
        enviadas = prev

    # Validar toda la transformación antes del primer efecto HTTP.
    for fila in filas: construir_telemetria_fila(fila,calibracion=cal)
    sincronizada=False
    if seguimiento:
        sesion=Path(ruta_csv).with_suffix('.sesion.json')
        if sesion.exists():
            meta=json.loads(sesion.read_text(encoding='utf-8'))
            if not isinstance(meta,dict):
                raise ValueError('Diagnóstico de sincronización malformado.')
            sincronizada=(meta.get('version')==1 and
                          meta.get('sincronizacion_requerida') is True and
                          meta.get('inicio_efectivo_utc')==filas[0]['timestamp_utc'] and
                          meta.get('origen')==filas[0]['origen'])
    lotes_enviados = 0
    total = len(filas)
    while enviadas < total:
        fin = min(enviadas + tamano_lote, total)
        lote=[]
        for fila in filas[enviadas:fin]:
            edad=(datetime.now(timezone.utc)-datetime.fromisoformat(fila['timestamp_utc'])).total_seconds()
            vivo=seguimiento and sincronizada and 0<=edad<=3
            dato=construir_telemetria_fila(fila,modo='en_vivo' if vivo else 'historico',
                                         calibracion=cal,csv_origen=origen_rel)
            dato['values']['edad_recepcion_s']=round(edad,3)
            lote.append(dato)
        publicar_lote(servidor, token, lote, timeout=timeout,
                      reintentos=reintentos, espera_inicial_s=espera_inicial_s)
        enviadas = fin
        lotes_enviados += 1
        if cursor_path is not None:
            cursor_path.parent.mkdir(parents=True, exist_ok=True)
            resumen_cursor = {
                'csv_origen': origen_rel,
                'configuracion_sha256': identidad,
                'filas_totales_vistas': total,
                'filas_enviadas': enviadas,
                'sha256_prefijo': _hash_filas(filas[:enviadas]),
                'modo_transmision': modo,
                'calibracion_valida': cal is not None,
                'endpoint_redactado': url_redactada(servidor),
                'actualizado_utc': datetime.now(timezone.utc).isoformat(),
            }
            guardar_json_atomico(cursor_path,resumen_cursor)
    return {
        'csv_origen': origen_rel,
        'filas_totales': total,
        'filas_enviadas': enviadas,
        'lotes_enviados': lotes_enviados,
        'modo_transmision': modo,
        'calibracion_valida': cal is not None,
        'endpoint_redactado': url_redactada(servidor),
    }


def publicar_csv(ruta_csv, servidor, token, modo='historico', ruta_cursor=None,
                 calibracion=None, tamano_lote=20, timeout=5.0, reintentos=3,
                 espera_inicial_s=0.1, permitir_prueba_controlada=False,
                 seguir=False,duracion=60.,intervalo_s=.25):
    """Histórico puntual o seguimiento de CSV completo/parcial sin abrir serial.

    Seguir conserva el cursor entre intentos; pendientes con edad >3 s se
    transmiten como históricos. Un ACK perdido puede repetir el último lote.
    """
    if modo not in ('historico','en_vivo'):
        raise ValueError('Modo de publicación desconocido.')
    if modo == 'en_vivo' and not seguir:
        raise ValueError('El modo en_vivo requiere --seguir; un CSV cerrado se publica como histórico.')
    for valor in (duracion,intervalo_s):
        if isinstance(valor,bool) or not isinstance(valor,(int,float)) or not 0<valor<float('inf'):
            raise ValueError('Duración e intervalo deben ser positivos y finitos.')
    _validar_servidor(servidor)
    _validar_token(token)
    if not isinstance(tamano_lote,int) or isinstance(tamano_lote,bool) or tamano_lote<=0:
        raise ValueError('tamano_lote debe ser un entero positivo.')
    cal=_calibracion_validada(calibracion)
    if ruta_cursor is None:
        ruta_cursor=Path(ruta_csv).with_suffix('.tb.cursor.json')
    if ruta_cursor is not None and Path(ruta_cursor).resolve() in (
            Path(ruta_csv).resolve(),Path(ruta_csv).with_suffix('.sesion.json').resolve()):
        raise ValueError('El cursor debe ser distinto del CSV y su diagnóstico.')
    inicio=time.monotonic()
    resultado={'filas_enviadas':0,'filas_totales':0,'lotes_enviados':0,
               'modo_transmision':modo,'error_red':None,'endpoint_redactado':url_redactada(servidor)}
    lotes=0
    while True:
        if Path(ruta_csv).exists():
            filas=_leer_filas_csv(ruta_csv,permitir_prueba_controlada,creciendo=seguir)
            if filas:
                try:
                    res=_publicar_filas(ruta_csv,filas,servidor,token,modo,ruta_cursor,cal,
                        tamano_lote,timeout,reintentos,espera_inicial_s,seguimiento=seguir and modo=='en_vivo')
                    lotes+=res['lotes_enviados']
                    resultado.update(res,error_red=None,lotes_enviados=lotes)
                except ConnectionError as e:
                    if not seguir: raise
                    resultado['error_red']=str(e)
        elif not seguir:
            raise FileNotFoundError('No existe el CSV indicado.')
        if not seguir or time.monotonic()-inicio>=duracion: break
        time.sleep(min(intervalo_s,max(0,duracion-(time.monotonic()-inicio))))
    if resultado['error_red']:
        raise ConnectionError(resultado['error_red'])
    if resultado['filas_enviadas']==0:
        raise ValueError('No hay filas completas nuevas para publicar durante el seguimiento.')
    return resultado


def capturar_y_publicar(fuente, ruta_csv, servidor, token, max_muestras=100, duracion=60.0,
                        origen='experimental', ruta_cursor=None, calibracion=None,
                        tamano_lote=20, timeout=5.0, reintentos=3, espera_inicial_s=0.1):
    """Registra primero localmente y publica después sin perder el CSV si falla la red."""
    from .comunicacion import registrar
    muestras, invalidos = registrar(fuente, ruta_csv, max_muestras=max_muestras,
                                    duracion=duracion, origen=origen)
    resultado = {
        'muestras_locales': muestras,
        'lineas_invalidas': invalidos,
        'csv_local': _portable_csv(ruta_csv),
        'publicado': False,
        'error_red': None,
    }
    if muestras == 0:
        return resultado
    try:
        pub = publicar_csv(
            ruta_csv, servidor, token, modo='historico', ruta_cursor=ruta_cursor,
            calibracion=calibracion, tamano_lote=tamano_lote, timeout=timeout,
            reintentos=reintentos, espera_inicial_s=espera_inicial_s,
            permitir_prueba_controlada=(origen == 'prueba_controlada'))
        resultado.update(pub)
        resultado['publicado'] = True
    except (ConnectionError, RuntimeError, OSError, ValueError) as e:
        resultado['error_red'] = str(e)
    return resultado
