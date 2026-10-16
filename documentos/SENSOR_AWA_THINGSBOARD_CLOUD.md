# Sensor Awa — conexión a ThingsBoard Cloud

## Estado comprobado el 16 de octubre de 2026

El equipo confirmó que ya existen en `https://thingsboard.cloud` el dispositivo
**Sensor Awa - Arduino UNO R4 WiFi** y el dashboard **Proyecto Sensor de Agua**.
No se crearon duplicados ni se cambió su privacidad.

- Fuera del sandbox se detectó `/dev/ttyACM0` como
  `UNO WiFi R4 CMSIS-DAP - TinyUSB CDC`. Dentro del sandbox no es visible:
  las comprobaciones anteriores de ausencia de puerto no describían el host.
- Se ejecutó `capturar` a 115200 y se guardaron **6 muestras reales**, sin agua
  añadida, cambios de montaje ni firmware, en
  [diagnostico_cloud_usb_20261016T183859_627964Z.csv](../datos/mediciones/diagnostico_cloud_usb_20261016T183859_627964Z.csv).
  Cero líneas inválidas; recepción UTC mínima/mediana/máxima:
  **500,254 / 501,128 / 504,531 ms**; contador Arduino: **500 ms**.
  Sin discontinuidades. Se excluyeron 544 líneas completas durante preparación;
  este número incluye la racha de comprobación, no significa que todas fueran viejas.
- La captura utiliza vaciado inicial, alineación a LF y cuatro intervalos de
  sincronización. No hay vaciados después del inicio efectivo. La cadencia
  compatible no demuestra una edad física absoluta del ADC; los límites están en
  [la auditoría](AUDITORIA_ADQUISICION_2026-10-16.md).
- Se validaron los 6 payloads reales sin enviarlos: incluyen `adc1`, `adc2`,
  `adc3`, `calibracion_valida=false` y **ninguna altura ni unidad de altura**.
- Una petición HTTPS sin credenciales a la página de Cloud respondió **200**
  a las `2026-10-16T18:39:35Z`. Esto demuestra conectividad, no autenticación,
  recepción de telemetría ni almacenamiento.
- Se preparó `~/.config/proyectosensorawa/thingsboard.json`, permisos **0600**,
  directorio **0700**. El equipo introdujo el token directamente en el archivo
  privado. Está fuera del árbol Git y su valor no aparece en este documento.
  Además, `git check-ignore -v` confirmó la regla `*.local.json` de respaldo para
  archivos locales dentro del proyecto. No se muestra el contenido privado.
- Los 87 archivos previos inventariados de firmware/datos conservan sus SHA-256.
  No se activaron LED ni se modificaron métodos numéricos. El código de
  adquisición e integración se subió en el commit `1e3cfc2`.

### Envío real confirmado

Se hizo una captura nueva de **6 muestras** en el CSV local
`datos/mediciones/cloud_real_20261016T190452_080262Z.csv`, sin líneas inválidas.
El CSV conserva SHA-256
`7bf25852a2fccc3ecd6bc0f810a8718ec8a224dcc29981ab8b9808f991def626`.
El primer UTC coincide con el inicio efectivo de la sincronización. Durante la
preparación se descartaron 460 líneas completas, incluidas las necesarias para
validar la cadencia. Los intervalos de recepción fueron **500,229–503,991 ms**,
mediana **501,834 ms**; `t_ms` avanzó siempre 500 ms. No hubo discontinuidades.

El publicador siguió el CSV y confirmó **6/6 filas en cuatro lotes** hacia
`https://thingsboard.cloud/api/v1/***/telemetry`. Cada lote pasó la comprobación
HTTP **2xx** del cliente; el código exacto de cada respuesta no se registró.
El cursor local de la sesión quedó en seis filas, modo `en_vivo`, con
`calibracion_valida=false`. La transformación usa los UTC del CSV, publica
`adc1`, `adc2`, `adc3` y **no genera ninguna altura**. Las filas que envejecen más
de tres segundos durante el envío se etiquetan como históricas; el ACK por sí
solo no permite confirmar la etiqueta almacenada de cada fila.

El equipo comprobó **Latest telemetry** en la cuenta: la última fila muestra
`adc1=2`, `adc2=0`, `adc3=1`, `calibracion_valida=false` y origen
`cloud_real_20261016T190452_080262Z.csv` a las **14:04:56 de Panamá**. Coincide
con la última fila del CSV (`19:04:56.635995 UTC`). Esto confirma almacenamiento
visible en el dispositivo correcto; no se efectuó una consulta REST de cuenta.

**Pendiente:** configurar los widgets del dashboard privado y comprobar su URL
desde el teléfono. El token de dispositivo autoriza el envío, pero no da acceso
de edición al dashboard. No se ha generado QR final.
Resumen sin credenciales: [VERIFICACION_ENVIO_REAL_2026-10-16.json](VERIFICACION_ENVIO_REAL_2026-10-16.json).

Verificación final: **89 pruebas aprobadas**, incluidas las de ingreso y reemplazo
privado de credenciales sintéticas. Registro:
[PRUEBAS_ENVIO_REAL_2026-10-16.log](PRUEBAS_ENVIO_REAL_2026-10-16.log).
La primera ejecución dentro del sandbox no pudo abrir sockets locales; su
[registro](PRUEBAS_ENVIO_REAL_SANDBOX_2026-10-16.log) se conserva. Al repetirla
con acceso a sockets, las 89 pruebas pasaron. Resumen previo sin credenciales:
[VERIFICACION_THINGSBOARD_CLOUD_2026-10-16.json](VERIFICACION_THINGSBOARD_CLOUD_2026-10-16.json).

## Introducir únicamente el token, sin historial ni eco

En una terminal interactiva de la Victus, desde la raíz del proyecto:

```bash
.venv/bin/python -m python.configurar_cloud
```

En ThingsBoard: **Entities → Devices → Sensor Awa - Arduino UNO R4 WiFi →
Manage credentials / Copy Access Token**. Pegar ese valor solo cuando el comando
lo solicite de forma oculta. No pegarlo en el chat, comandos, informes ni logs.
El módulo rechaza entrada sin terminal y se detiene si no puede ocultar el eco.
Guarda mediante archivo temporal privado y reemplazo atómico, fuera del repositorio;
si ya existe un token válido no lo sobrescribe. No usa credenciales de usuario ni
cambia el dashboard. No añadir el token a `.env` ni pasarlo con `--token`.

Una vez completado, basta comunicar **“token guardado”**. No comunicar su valor.

Si se regenera el token del dispositivo en ThingsBoard Cloud (por ejemplo, porque
el anterior apareció en un chat), sustituir el valor local desde la terminal:

```bash
.venv/bin/python -m python.configurar_cloud --reemplazar-token
```

El nuevo token se introduce con eco oculto y el archivo previo permanece intacto
si la entrada falla. La rotación invalida el token anterior; usar un cursor nuevo
para capturas futuras. Si había un envío interrumpido con el cursor anterior,
revisar las filas ya confirmadas antes de reanudarlo con otra credencial.

## Transmisión con el publicador existente

Con el token cargado, abrir dos terminales en la raíz del proyecto. Cerrar otros
lectores del puerto. Elegir un nombre de CSV nuevo en cada sesión.

Terminal A, adquisición local:

```bash
.venv/bin/python -m python.main capturar \
  --puerto /dev/ttyACM0 --baudios 115200 \
  --muestras 12 --duracion 10 \
  --salida datos/mediciones/cloud_en_vivo_01.csv
```

Terminal B, iniciar durante la adquisición (puede esperar a que exista el CSV):

```bash
.venv/bin/python -m python.main thingsboard \
  --csv datos/mediciones/cloud_en_vivo_01.csv \
  --config "$HOME/.config/proyectosensorawa/thingsboard.json" \
  --modo en_vivo --seguir --duracion 30 \
  --lote 4 --timeout 3 --reintentos 2 \
  --cursor datos/resultados/cloud_en_vivo_01.tb.cursor.json
```

Comprobar después:

```bash
.venv/bin/python -m python.main cadencia \
  --csv datos/mediciones/cloud_en_vivo_01.csv
```

No usar `--calibracion`: la actual no está validada. El CSV conserva siempre las
UTC de recepción y `t_ms` por separado. La red trabaja en otro proceso. Si falla,
reiniciar el mismo comando de publicación con el mismo cursor; lo atrasado se
etiqueta como histórico con sus tiempos originales. No borrar ni reiniciar el
cursor para reintentar. Una interrupción tras recibir un lote y antes de confirmar
su ACK puede repetir ese lote; no se promete entrega exactamente una vez.

Para enviar las seis lecturas de diagnóstico ya guardadas, de forma histórica:

```bash
.venv/bin/python -m python.main thingsboard \
  --csv datos/mediciones/diagnostico_cloud_usb_20261016T183859_627964Z.csv \
  --config "$HOME/.config/proyectosensorawa/thingsboard.json" \
  --modo historico --lote 6 --timeout 5 --reintentos 2 \
  --cursor datos/resultados/diagnostico_cloud_usb_20261016T183859_627964Z.tb.cursor.json
```

## Confirmar recepción y almacenamiento

Una salida exitosa del publicador significa ACK HTTP 2xx del endpoint de telemetría.
Para comprobar lo almacenado, entrar en **Entities → Devices → Sensor Awa - Arduino
UNO R4 WiFi → Latest telemetry**: revisar `adc1`, `adc2`, `adc3`, `t_ms` y
`calibracion_valida=false`, con horas coherentes con el CSV. Para el diagnóstico
histórico, seleccionar la ventana temporal de sus UTC en la gráfica.

La API de consulta usa autorización de cuenta con permisos de lectura y el UUID
del dispositivo. El endpoint es
`GET /api/plugins/telemetry/DEVICE/{deviceId}/values/timeseries?keys=adc1,adc2,adc3,t_ms,calibracion_valida`.
El Access Token del dispositivo para publicar no sustituye esa autorización.
No se solicitan usuario/contraseña ni se imprimen cabeceras de autenticación.
Si no hay credenciales de consulta autorizadas, la comprobación se hace en la UI.
Referencia: [API REST oficial](https://thingsboard.io/docs/reference/rest-api/).

## Completar el dashboard existente, conservándolo privado

No hay una sesión autenticada de cuenta ni API autorizada de edición en este
entorno. Realizar estos pasos en ThingsBoard Cloud, sin publicar el dashboard:

1. **Dashboards → Proyecto Sensor de Agua → Edit**. Abrir **Entity aliases → Add
   alias**. Nombre `Sensor Awa`, filtro **Single entity**, tipo **Device**, seleccionar
   **Sensor Awa - Arduino UNO R4 WiFi** y guardar el alias.
2. **Add widget → Cards → Value card**. Datasource **Entity alias → Sensor Awa**;
   una clave de telemetría `adc1`. Etiqueta `Sensor 1 — A0`, unidad `ADC`, decimales
   `0`. En Appearance activar **Date**, con fecha/hora de la última actualización.
   Duplicar para `adc2` / `Sensor 2 — A2` y `adc3` / `Sensor 3 — A3`.
3. En cada tarjeta: **Appearance → Value → Color settings → Function**. En el cuerpo
   de la función `f(value)` introducir:

   ```javascript
   if (value === null || value === undefined || value === '') return '#757575';
   var adc = Number(value);
   if (!isFinite(adc) || adc < 0 || adc > 1023) return '#757575';
   if (adc < 50) return '#2E7D32';
   if (adc < 150) return '#1565C0';
   if (adc < 300) return '#7B1FA2';
   return '#C62828';
   ```

   Son rangos provisionales ADC: verde 0–49, azul 50–149, morado 150–299,
   rojo 300–1023. No representan alturas. La fecha de cada tarjeta sirve de
   indicador de última actualización, sin crear una marca de tiempo ficticia.
4. **Add widget → Charts → Time series chart**. Usar el alias `Sensor Awa` y claves
   `adc1`, `adc2`, `adc3`. Ventana **Realtime / Last 5 minutes**; agregación **None**;
   eje Y `cuentas ADC`, rango 0–1023. Colores de las series distintos para identificar
   canales; el color por rango corresponde a las tarjetas.
5. Añadir una tabla de últimos valores si se desea inspeccionar `t_ms`,
   `calibracion_valida`, `modo_transmision`, `es_tiempo_real`, `edad_recepcion_s` y
   `color_adc1..3`. No añadir indicadores de centímetros. Guardar los cambios.
6. Abrir el dashboard desde el teléfono autenticado con una cuenta que tenga acceso.
   No utilizar **Make public**, **Public group** ni cambiar permisos para este flujo.
   Una URL privada puede ser el destino del QR: el teléfono necesitará iniciar sesión.
   El acceso anónimo requeriría autorización expresa adicional.

Fuentes: [aliases Cloud](https://thingsboard.io/docs/paas/user-guide/aliases/),
[Value card Cloud](https://thingsboard.io/docs/paas/reference/widgets/cards/value-card/),
[widgets](https://thingsboard.io/docs/user-guide/widgets/) y
[dashboards Cloud](https://thingsboard.io/docs/paas/user-guide/dashboards/).
Las etiquetas pueden variar con el idioma y la versión de la interfaz.

## URL y QR, solo después de verificar la vista

Copiar la URL real del dashboard después de abrirlo. Comprobar en el teléfono
con la cuenta autorizada que aparecen los datos. No basta la pantalla de login.
La URL no debe contener tokens ni credenciales. Guardarla en el archivo privado:

```bash
.venv/bin/python - <<'PY'
import json
from pathlib import Path
from python.comunicacion import guardar_json_atomico
from python.thingsboard import validar_url_dashboard
p = Path.home() / '.config/proyectosensorawa/thingsboard.json'
cfg = json.loads(p.read_text())
url = input('URL del dashboard ya comprobada en el teléfono: ').strip()
cfg['dashboard_url'] = validar_url_dashboard(url, token=cfg.get('token'))
guardar_json_atomico(p, cfg)
print('URL de visualización guardada; configuración privada no mostrada.')
PY
.venv/bin/python -m python.main qr \
  --config "$HOME/.config/proyectosensorawa/thingsboard.json" \
  --salida documentos/qr_sensor_awa_cloud_01.png --verificar
```

El módulo existente genera y decodifica el PNG, y comprueba el contenido. El QR
solo contendrá la URL del dashboard; nunca la de telemetría ni el Access Token.
La accesibilidad y el contenido visible requieren la verificación del teléfono.
No se ha generado todavía un QR definitivo porque falta la URL real comprobada.
