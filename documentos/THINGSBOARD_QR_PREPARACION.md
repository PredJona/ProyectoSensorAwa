# Etapa propuesta: ThingsBoard y acceso mediante QR

Estado: propuesta técnica; no se creó un dashboard, no se enviaron datos y
no se generó un QR de destino ficticio. No se necesita cambiar el firmware
para enviar posteriormente las lecturas desde Python.

## Reutilización y separación de tareas

`python.comunicacion.parsear_linea` valida las tramas y `registrar` conserva
ADC y recepción UTC en CSV con vaciado a disco por fila. Ese receptor debe
seguir siendo el único dueño del puerto. Propuesta: un proceso publicador
independiente lee únicamente filas completas ya guardadas, guarda un cursor
persistente y envía lotes. Un fallo de red no bloquea ni descarta la adquisición.
Respetar desconexiones y reinicios; el cursor debe incluir identidad de archivo,
no solo número de fila. Si se reintenta una petición tras respuesta incierta,
usar la misma marca de tiempo; no prometer entrega exactamente una vez.

`python.calibracion.cargar/convertir` servirán para alturas cuando existan
curvas independientes aceptadas. Ahora no se publicarán centímetros ni
porcentajes: la calibración no está validada. `python.graficas.mediciones`
seguirá disponible como respaldo local y evidencia, sin dependencia de red.

## Telemetría propuesta

Usar un dispositivo lógico para la placa con claves `adc1`, `adc2`, `adc3`,
`t_ms`, `calibracion_valida=false` y, si se acuerda, colores ADC provisionales.
Se deben conservar origen, identificador de sesión y versión de clasificación.
Más adelante se añadirán `altura1_mm`, etc., solo para sensores y rangos con
calibración válida; una lectura fuera del dominio no debe extrapolarse ni
reutilizar la altura anterior como si fuera actual.

La [API HTTP oficial de telemetría](https://thingsboard.io/docs/reference/http-api/telemetry/)
acepta POST a `https://SERVIDOR/api/v1/TOKEN/telemetry` y objetos con `ts`
(milisegundos Unix) y `values`, incluidos lotes. Usar `timestamp_utc` del CSV
para `ts`, aclarando que representa recepción por el PC. `t_ms` es el contador
Arduino, no hora Unix. Propuesta: timeout de red acotado, reintentos con espera
creciente y envío desde el cursor, conservando siempre el original local.
Token en configuración privada del publicador; ocultarlo en logs porque forma
parte de la URL del endpoint. No debe aparecer en QR ni repositorio.

## Diseño propuesto del dashboard

Tres tarjetas ADC, una por sensor; gráfica temporal de los tres canales;
indicadores de color con los intervalos provisionales; hora de última lectura
y aviso de datos atrasados/desconectados. Mostrar «ADC sin calibrar» y
«clasificación provisional». Las alturas solo se mostrarán cuando sean válidas.
Separar reproducción de CSV históricos y transmisión en vivo para que una
demostración no parezca adquisición actual. No confundir color calculado por
Python con confirmación del estado físico de un LED.

Para acceso externo, elegir un servidor HTTPS alcanzable desde el teléfono;
`localhost` o una IP privada del portátil no bastan fuera de esa red. Según
la [documentación de dashboards](https://thingsboard.io/docs/user-guide/dashboards/#make-dashboard-public),
el acceso anónimo requiere publicar el dashboard y sus entidades asociadas;
es una decisión de visibilidad que debe autorizarse al configurar la instancia.
Alternativa: URL del dashboard con acceso mediante usuario de consulta.

El QR contendrá solo la URL final de consulta. Reutilizar `python.qr.generar`
y `leer` después de confirmar esa URL y resolver las dependencias qrcode/OpenCV.
Probar acceso desde otro dispositivo, presentación de datos y lectura del QR.
Todavía faltan instancia/URL, credenciales, elección de acceso público o privado,
política de conservación y aprobación de implementación. Nada se publicó.
