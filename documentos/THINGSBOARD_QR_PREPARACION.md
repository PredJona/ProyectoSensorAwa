# ThingsBoard y QR: procedimiento de entrega

**Actualización Cloud:** el equipo ya creó el dispositivo **Sensor Awa - Arduino
UNO R4 WiFi** y el dashboard **Proyecto Sensor de Agua** en `https://thingsboard.cloud`.
La captura física corregida ya se comprobó fuera del sandbox. Usar la
[guía específica de Cloud](SENSOR_AWA_THINGSBOARD_CLOUD.md) para introducir el token
sin eco y completar el dashboard existente conservando su privacidad.
Los pasos genéricos siguientes se conservan como referencia; no crear duplicados.

El software está probado con HTTP local simulado, pseudoterminales y QR decodificado.
Además, se aceptaron **6 muestras reales** en ThingsBoard Cloud mediante cuatro
lotes HTTP 2xx. **El dashboard creado por el equipo todavía no se ha podido
inspeccionar.** La última fila se cotejó con **Latest telemetry** en la cuenta;
faltan los widgets y una URL comprobada desde el teléfono. No se requieren nuevas pruebas
con agua, LED ni cambios de firmware para demostrar los tres ADC.

## Flujo y datos

`Arduino UNO R4 WiFi → USB 115200 → Python → CSV → ThingsBoard HTTP → Dashboard → QR`

Un proceso abre el puerto USB y otro sigue el CSV. La red nunca bloquea el lector
serial. Cada fila conserva `timestamp_utc,t_ms,adc1,adc2,adc3,origen`.

- `timestamp_utc` representa **recepción completa en el PC**, no el instante físico
  de conversión. ThingsBoard recibe ese valor como `ts` en milisegundos Unix UTC.
- `t_ms` conserva `millis()` del Arduino; no se convierte a fecha ni se sustituye
  por el reloj del servidor. El PC debe tener fecha/hora correctas.
- Se publican `adc1`, `adc2`, `adc3`, `t_ms`, `origen`, `csv_origen`, colores
  **provisionales de software**, `calibracion_valida`, `estado_calibracion`,
  `modo_transmision`, `es_tiempo_real` y `edad_recepcion_s`.
- Sin calibración validada se omiten `altura1`, `altura2`, `altura3` y
  `unidad_altura`; no se envían valores ficticios ni `null` como alturas.
  La documentación de la API describe tipos de telemetría concretos; omitir claves
  ausentes evita depender de la aceptación de `null` por una versión del servidor.
- Una calibración opcional requiere `validada: true`, unidad admitida y puntos
  independientes y crecientes para los tres sensores. Cada ADC debe estar dentro
  de su rango, sin extrapolación. La bandera es una declaración del responsable:
  el software no demuestra la validez física. **La calibración exploratoria actual
  no está validada; ejecutar la demostración sin `--calibracion`.**

La API oficial admite lotes `[{"ts": epoch_ms, "values": {...}}]` por
[`POST /api/v1/<token>/telemetry`](https://thingsboard.io/docs/reference/http-api/telemetry/).
Se rechazan CSV con dos muestras en el mismo milisegundo para evitar que coincidan
claves/tiempo y se sobrescriban puntos en el servidor. No se inventan tiempos para
arreglar una captura acumulada: su CSV original permanece intacto.

## Crear el dispositivo y dashboard (manual, en su cuenta)

1. Acceder a la instancia ThingsBoard por HTTPS. En **Entities → Devices** agregar
   un dispositivo llamado `ProyectoSensorAwa`. Copiar su **Access Token** desde sus
   credenciales; es secreto y solo se usa en Python. Véase
   [conexión HTTP oficial](https://thingsboard.io/docs/reference/http-api/getting-connected/).
2. Crear un dashboard llamado `ProyectoSensorAwa — ADC`. Editarlo y crear un
   **entity alias** de entidad única que seleccione ese dispositivo.
3. Agregar una gráfica de serie temporal con ese alias y claves `adc1`, `adc2`,
   `adc3`; unidad `cuentas ADC`, límites 0–1023. Agregar tres tarjetas de último
   valor para esas mismas claves. Seleccionar ventana **tiempo real / últimos
   5 minutos** y, si se ofrece, agregación **None** para ver muestras a 500 ms.
4. Agregar una tabla/indicadores con `t_ms`, `modo_transmision`, `es_tiempo_real`,
   `edad_recepcion_s`, `calibracion_valida` y `estado_calibracion`. No agregar widgets
   de altura física. Guardar el dashboard.
5. Para acceso con cuenta, asignar dashboard y dispositivo a un cliente/usuario
   de lectura y abrir la URL con esa cuenta desde el teléfono. Para acceso anónimo
   de demostración, usar **Make dashboard public / Copy public link** y hacer
   público también el dispositivo subyacente; en Cloud se configuran los grupos
   correspondientes. Esto expone las lecturas: hacerlo solo si es el acceso que se
   desea. El procedimiento depende de la edición; consultar
   [dashboards CE](https://thingsboard.io/docs/user-guide/dashboards/),
   [dispositivos CE](https://thingsboard.io/docs/user-guide/devices/) o
   [dashboards Cloud](https://thingsboard.io/docs/paas/user-guide/dashboards/).
6. Copiar la URL real generada por ThingsBoard. Abrirla en el teléfono (incógnito
   si es pública) y comprobar que aparecen las lecturas. Si el servidor está en
   la Victus, el teléfono debe poder llegar por red a su host/IP; `localhost` en
   el teléfono apunta al propio teléfono. Para datos móviles hace falta una
   instancia accesible desde Internet. No basta con que el PNG del QR se genere.

## Configuración privada fuera del repositorio

Desde la raíz del proyecto, ejecutar este bloque **solo cuando se disponga de los
valores reales**. Solicita el token sin eco y crea un archivo nuevo con permisos
0600; no imprime credenciales ni sobrescribe archivos existentes:

```bash
.venv/bin/python - <<'PY'
import getpass, json, os
from pathlib import Path
from python.thingsboard import cargar_configuracion, validar_url_dashboard
p = Path.home() / '.config/proyectosensorawa/thingsboard.json'
srv = input('URL base HTTPS de ThingsBoard: ').strip()
token = getpass.getpass('Access Token privado del dispositivo: ').strip()
dash = input('URL real del dashboard: ').strip()
cfg = cargar_configuracion(servidor=srv, token=token, dashboard_url=dash)
validar_url_dashboard(cfg['dashboard_url'], token=cfg['token'])
p.parent.mkdir(parents=True, exist_ok=True)
fd = os.open(p, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
with os.fdopen(fd, 'w', encoding='utf-8') as f:
    json.dump(cfg, f, indent=2)
print('Configuración privada creada:', p)
PY
```

También se admiten `THINGSBOARD_URL`, `THINGSBOARD_TOKEN` y
`THINGSBOARD_DASHBOARD_URL`. `.env` **no se carga automáticamente**. Evitar
`--token` en consola para no dejarlo en el historial o lista de procesos.
Se exige HTTPS salvo HTTP en localhost para los servidores de prueba.
No usar un token JWT de usuario en lugar del Access Token del dispositivo.

## Captura y publicación en vivo

Conectar Arduino al USB junto al cargador de la HP Victus. Cerrar el monitor
serial del IDE y cualquier otro lector. Mantener el montaje actual, sin LED.
Los comandos siguientes se ejecutan desde la raíz del proyecto. Usar un nombre
nuevo para cada sesión; los existentes se rechazan.

**Terminal A**, solo adquisición:

```bash
.venv/bin/python -m python.main puertos
.venv/bin/python -m python.main capturar \
  --puerto /dev/ttyACM0 --baudios 115200 \
  --muestras 120 --duracion 65 \
  --timeout-sincronizacion 12 --timeout-inactivo 3 \
  --salida datos/mediciones/demo_usb_01.csv
```

**Terminal B**, iniciar inmediatamente (puede esperar a que se cree el CSV):

```bash
.venv/bin/python -m python.main thingsboard \
  --csv datos/mediciones/demo_usb_01.csv \
  --config "$HOME/.config/proyectosensorawa/thingsboard.json" \
  --modo en_vivo --seguir --duracion 90 \
  --lote 4 --timeout 2 --reintentos 2 \
  --cursor datos/resultados/demo_usb_01.tb.cursor.json
```

El publicador consume únicamente filas terminadas en LF. Un lote puede tener
menos de `--lote`: se envía lo disponible en cada consulta, aproximadamente cada
250 ms. La etiqueta `en_vivo` requiere seguimiento, diagnóstico de sincronización
compatible con la primera fila y edad de recepción entre 0 y 3 segundos al intentar
enviar. Si la red retrasa una fila, se conserva su `ts` y se etiqueta `historico`.
`es_tiempo_real` significa recepción reciente, **no latencia física demostrada**.
Si hay valores muy antiguos, seleccionar en el dashboard la ventana de sus UTC.

Tras terminar la captura:

```bash
.venv/bin/python -m python.main cadencia --csv datos/mediciones/demo_usb_01.csv
```

Debe mostrar `cadencia_compatible: true` y medianas UTC/Arduino próximas a 500 ms.
El informe `demo_usb_01.sesion.json`, junto al CSV, contiene inicio efectivo,
descartes previos, desbordamientos compatibles y motivo de interrupción si existe.
Las condiciones y límites de frescura están en
[AUDITORIA_ADQUISICION_2026-10-16.md](AUDITORIA_ADQUISICION_2026-10-16.md).

## Fallos y recuperación

- Timeout/USB desconectado/reinicio probable: el capturador conserva lo ya escrito
  y termina con código 2 (Ctrl+C: 130). Reconectar físicamente si hace falta y usar
  **otro CSV nuevo**; no se fusionan sesiones a través de un reinicio ni se vacía
  el búfer en una sesión ya activa.
- Red caída/HTTP 429/5xx: reintentos acotados con espera exponencial; en seguimiento
  se vuelve a intentar mientras dure `--duracion`. Si sigue fallando, termina con
  código 2. Reiniciar **el mismo comando de ThingsBoard con el mismo cursor** para
  recuperar pendientes, que viajarán como históricos si ya tienen más de 3 s.
- HTTP 3xx y 4xx excepto 429: rechazo inmediato; comprobar servidor, permisos,
  credenciales y tamaño de lote. No se siguen redirecciones con el token.
- El cursor se guarda después del ACK mediante archivo temporal, `fsync` y
  reemplazo atómico. Verifica SHA-256 del prefijo enviado y configuración
  (CSV/ruta, servidor, dispositivo, modo, calibración) sin guardar el token.
  No reutilizar un cursor para otro destino ni lanzar dos publicadores con el
  mismo cursor. Los cursores de la implementación anterior se rechazan por carecer
  de identidad; conservarlos y revisar el progreso antes de elegir un cursor nuevo.
- Garantía **al menos una vez**: si el servidor recibe y se pierde el ACK, o se
  interrumpe Python antes de guardar el cursor, se puede repetir el último lote.
  `ts` y ADC se conservan, pero reglas/efectos del servidor pueden ejecutarse otra
  vez. No se afirma entrega exactamente una vez. `fsync` del cursor no equivale a
  garantizar persistencia de todo el sistema frente a un corte eléctrico.
- CSV cerrado: usar `--modo historico` sin `--seguir`. Si el CSV aún no ha sido
  enviado, se crea por defecto `<nombre>.tb.cursor.json`; también se puede indicar
  uno explícito. No cambiar de modo con un cursor ya vinculado a `en_vivo`.
  `capturar_y_publicar()` es una utilidad secuencial y publica como histórico;
  la demostración en vivo utiliza los dos procesos anteriores.

Ejemplo histórico para **un CSV nuevo aún no publicado**:

```bash
.venv/bin/python -m python.main thingsboard \
  --csv datos/mediciones/demo_usb_01.csv --modo historico \
  --config "$HOME/.config/proyectosensorawa/thingsboard.json" \
  --cursor datos/resultados/demo_usb_01.historico.cursor.json
```

## QR definitivo

Con `dashboard_url` real ya comprobada desde el teléfono:

```bash
.venv/bin/python -m python.main qr \
  --config "$HOME/.config/proyectosensorawa/thingsboard.json" \
  --salida documentos/qr_dashboard_01.png --verificar
```

Crea PNG y texto de referencia `.contenido.txt`, rechazando destinos existentes.
Genera y decodifica el QR para comparar exactamente el contenido. Rechaza tokens
conocidos (incluidos codificados en URL), endpoints de telemetría, credenciales
en URL, plantillas y direcciones loopback. Esto valida sintaxis/contenido; **no
comprueba que la URL exista, sea pública ni muestre datos**. Eso se verifica con
el teléfono. No se genera un QR definitivo con una URL inventada.

Dependencias opcionales, únicamente en el entorno virtual:

```bash
.venv/bin/python -m pip install 'qrcode[pil]>=7.4' -r requirements-qr-lectura.txt
.venv/bin/python -m unittest discover -s tests -v
```
