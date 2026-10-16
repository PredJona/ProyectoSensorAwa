# Auditoría final de adquisición — 16 de octubre de 2026

## Alcance y estado inicial

Se inspeccionaron Git y los cambios locales antes de editar. El árbol ya contenía
cambios de Antigravity en Python, firmware, documentos y datos, además de gráficos
eliminados de `analisis_rgb_01`. No se restauraron ni eliminaron esas evidencias.
Esta intervención cambia adquisición, publicación, CLI, documentación y pruebas;
no modifica firmware, métodos numéricos ni mediciones. Los tres RGB están retirados
según el equipo; no se conectaron, activaron ni se cargó firmware.

El puerto `/dev/ttyACM0` no está expuesto en este entorno. La confirmación física
previa (USB junto al cargador, 115200, A0/A2/A3 y LCD operativo) procede del equipo;
no se presenta como una nueva verificación física realizada aquí.

## Causa demostrada y causa física no identificada

El receptor anterior validaba números y rangos, pero no continuidad ni cadencia.
Escribía UTC al procesar cada LF. Por tanto, cualquier cola válida se convertía
en una ráfaga de filas aparentemente recién recibidas. No correlacionaba el
avance de `t_ms` con `time.monotonic()` ni establecía un inicio efectivo.

Comprobación de los CSV existentes, exclusivamente en lectura:

| CSV | Filas | Mediana UTC entre filas | Delta Arduino | Resultado |
| --- | ---: | ---: | ---: | --- |
| `verificacion_precalibracion_2026-10-16_01.csv` | 10 | 0,099 ms | 500 ms | Acumulado; no representa cadencia de recepción en vivo |
| `diagnostico_serial_2026-10-16_cable_nuevo_01.csv` | 10 | 500,878 ms | 500 ms | Compatible con recepción continua |

En el primer archivo, UTC mínima/máxima entre filas es 0,083/0,168 ms; en el segundo,
500,483/501,554 ms. Esto confirma el defecto del software y la recepción acumulada.
No localiza dónde quedaron retenidos los bytes ni demuestra su edad física exacta.

**Capas distintas:**

- PySerial 3.5 POSIX, inspeccionado en el entorno instalado, ya llama
  `_reset_input_buffer()` dentro de `Serial.open()`. No es correcto atribuir el
  problema únicamente a que Python olvidó un vaciado al abrir.
- Ese vaciado afecta la cola accesible al controlador del sistema. Datos en la
  placa/puente USB o pendientes de entrega pueden llegar después. La documentación
  de [PySerial](https://pyserial.readthedocs.io/en/latest/pyserial_api.html)
  explica límites de los vaciados con USB y posibles cambios DTR/RTS al abrir.
  No se ha localizado experimentalmente qué cola del UNO R4 retuvo esta ráfaga.
- Una apertura puede alterar líneas de control; no se presupone que reinicie
  siempre este UNO R4, ni se fuerza un reset como solución.
- Un reinicio hace retroceder `t_ms` o puede emitir cabecera. No explica por sí solo
  que varios segundos de contador se reciban en milisegundos. Una cabecera o
  retroceso fuera del extremo de 32 bits provoca cierre por reinicio **probable**.
- El desbordamiento es modular en 2³² ms (aprox. 49,71 días). No es un salto a cero
  cualquiera: se exige un cruce cerca del máximo con delta y recepción compatibles
  con 500 ms. El CSV acumulado observado no está cerca de ese extremo.
- Se distinguen explícitamente contador Arduino y tiempo real de recepción. El
  firmware usa `INTERVALO_MS=500`; el código se leyó pero no se cambió.

## Estrategia aplicada

1. Captura experimental exige `read` con timeout positivo ≤100 ms; `capturar` usa
   50 ms y acceso exclusivo POSIX. Archivo existente se rechaza antes de abrir USB.
2. Vaciado explícito inicial y descarte hasta el siguiente LF para no interpretar
   una cola de línea como una medición completa. No se utiliza una espera fija de
   arranque como evidencia de frescura.
3. Descartar datos de preparación hasta observar **cuatro intervalos consecutivos**
   válidos, al menos cinco líneas completas: delta de contador 450–650 ms,
   recepción 350–750 ms y diferencia entre ambos ≤150 ms. El avance total durante
   esa racha también debe concordar con el reloj monotónico dentro de 150 ms.
   Una ráfaga, cabecera o dato inválido reinicia la comprobación.
4. La línea que confirma la condición es la primera fila del CSV. Ese es el inicio
   efectivo; `--duracion` empieza ahí. No se reconstruyen UTC para líneas anteriores.
   El límite de sincronización es independiente (12 s por defecto).
5. Desde ese instante no se vacían colas. Se conservan fragmentos entre timeouts,
   se escriben todas las líneas válidas bajo las condiciones de continuidad y se
   hace `flush` por fila. Bytes vacíos seriales significan timeout, no EOF.
6. Se vigilan intervalos, deriva acumulada Arduino/monotónico ≤250 ms y salto
   UTC/monotónico ≤250 ms. Dato incompatible: no se presenta como nueva muestra,
   termina la sesión y se conserva todo el CSV parcial. No se mezclan reinicios.
7. Silencio activo de 3 s termina con error; un `read` puede sobrepasar un plazo
   por hasta su timeout y el tiempo de planificación del sistema. Líneas de más
   de 256 bytes se descartan hasta LF. No hay espera infinita con la fuente serial
   configurada. Una fuente arbitraria cuyo `read` ignore el timeout no tiene esa
   garantía; la implementación real usa PySerial.
8. El diagnóstico adyacente `.sesion.json` guarda origen, versión, inicio efectivo,
   descartes completos previos, muestras/invalidaciones, cruces compatibles y estado
   final/motivo. Se actualiza atómicamente al iniciar captura y al terminar.
   Un fallo se recupera con un archivo nuevo y una nueva sincronización.

CSV sin cambios de formato:

```text
timestamp_utc,t_ms,adc1,adc2,adc3,origen
```

`registrar` permite flujo sin sincronización solo para `prueba_controlada`, para
mantener los ensayos de parser y archivos artificiales; no existe un bypass para
capturas experimentales. Los datos sintéticos se crean en directorios temporales,
con identificación explícita de prueba. Ninguno se agrega a `datos/mediciones`.

## Garantías y límites de frescura

**Demostrable:** las filas aceptadas, después de una preparación excluida, llegaron
con ritmo y avance compatibles bajo las tolerancias declaradas. Una ráfaga rápida
no se acepta como una serie a 500 ms; esto se prueba incluso con bytes que aparecen
tras el vaciado. La prueba conjunta muestra que HTTP lento/503 no bloquea el lector.
No se pierden filas válidas dentro de una sesión continua que cumple esos límites;
al final solicitado o una anomalía se cierra deliberadamente la sesión.

**No demostrable con el protocolo actual:** edad absoluta del ADC, latencia fija
anterior a la recepción o que una cola antigua no esté entregándose deliberadamente
a 500 ms. No hay reloj UTC de placa, identificador de arranque ni handshake con
nonce. Sin cambiar firmware (prohibido en este trabajo), dos flujos con iguales
números y cadencia son indistinguibles. Un reset justo cerca del desbordamiento
puede imitarlo; por eso se registra `desbordamientos_compatibles`, no una prueba
inequívoca de uptime. Retrocesos también pueden indicar reordenamiento/corrupción.

Las tolerancias son un criterio de aceptación conservador para esta demostración,
no un certificado de tiempo real duro ni prueba de ausencia de colas en todo USB.
Una pausa del SO, disco lento o pérdida de muestras puede cerrar la sesión aunque
la placa siga midiendo. Se preservan los datos aceptados y se informa el fallo.
`flush()` protege ante errores de proceso/red, no garantiza sobrevivir a cualquier
corte de energía. No se cambia la UTC histórica ni se corrigen CSV previos.

## ThingsBoard, pruebas y operación

Se corrigieron etiquetas de vivo sin evidencia, alturas `null` sin calibración,
cursores no vinculados al dispositivo y escritura no atómica. Se implementó
seguimiento de filas completas con cursor persistente y clasificación por edad
(incluso al reintentar). Se validan UTC y milisegundos únicos para evitar pérdida
de puntos en ThingsBoard. HTTPS remoto, redirecciones rechazadas y errores sin
secretos; el token no se guarda en el cursor ni en el QR.

La suite incluye acumulación residual del USB, 500 ms normales, fragmentos,
timeouts, ausencia de datos nuevos, desconexión, nueva sesión tras fallo,
reinicio, cruce modular, reloj UTC, HTTP 400/401/403/404/405/413/307/429/503,
reintentos y recuperación con ACK incierto, corrupción/cambio de prefijo del
cursor, cambio de dispositivo/modo, calibración inválida y fuera de rango,
filas incompletas mientras crece el CSV, seguridad de URL/token y QR real
con generación/decodificación. Las simulaciones C++ del firmware solo se ejecutan
en el PC; no cargan firmware ni activan pines físicos.

Registro final de ejecución:
[PRUEBAS_ADQUISICION_2026-10-16.log](PRUEBAS_ADQUISICION_2026-10-16.log).
La revisión independiente final identificó un bypass de validación QR con espacios
antes de la URL; se reprodujo, se normalizó el contenido antes de elegir la ruta
de generación y la regresión pasó. No identificó defectos críticos demostrables
en sincronización o cursor. Las 81 pruebas finales pasan sin errores ni omisiones.
El [informe de verificación](VERIFICACION_ADQUISICION_2026-10-16.json) registra
versiones, hashes del código verificado y SHA-256 de los 87 archivos previos de
firmware/datos, idénticos al inventario tomado antes de editar.
Comandos de captura, seguimiento HTTP, recuperación, configuración del dashboard
y QR: [THINGSBOARD_QR_PREPARACION.md](THINGSBOARD_QR_PREPARACION.md).
