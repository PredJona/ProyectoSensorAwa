# Diagnóstico de carga y serial — 16 octubre 2026

Estado actualizado: firmware principal cargado correctamente y comunicación
serial recuperada tras cambiar cable y reconectar por otra ruta USB.
Captura posterior: 30 muestras válidas, cero inválidas, intervalos de 500 ms.
El usuario confirmó que la LCD continúa actualizando después de la carga.

## Hechos comprobados en esta sesión

- Workspace inspeccionado: `/home/jules/Documentos/proyectoun/metnum/Proyecto1`.
- El aislamiento oculta USB; las comprobaciones físicas se ejecutaron fuera
  del aislamiento con aprobación. No se usó sudo ni se cambiaron permisos.
- `/dev/ttyACM0`: `crw-rw---- root uucp`; el usuario real pertenece a `uucp`.
- `fuser` y `lsof` no mostraron ocupantes del puerto al inspeccionarlo.
- USB: `2341:1002 Arduino SA UNO WiFi R4 CMSIS-DAP`, serie DC5475D0E374.
- Arduino CLI 1.5.1; core arduino:renesas_uno 1.6.0;
  LiquidCrystal_I2C 2.0.0. No se actualizaron herramientas ni puente ESP32-S3.
- El sketch usa A0/A2/A3, LCD 0x27, Serial 115200 y periodo 500 ms.
  Su CSV de cuatro enteros coincide con `python.comunicacion.parsear_linea`.

## Compilación y carga

```sh
XDG_CACHE_HOME=/tmp/proyecto1-r4-cache arduino-cli compile --fqbn arduino:renesas_uno:unor4wifi --build-path /tmp/awa-r4-diag-20261016-build arduino/NivelAguaR4
arduino-cli upload --fqbn arduino:renesas_uno:unor4wifi --port /dev/ttyACM0 --input-dir /tmp/awa-r4-diag-20261016-build --verbose arduino/NivelAguaR4
```

Compilación: salida 0; 59352 bytes de programa y 9020 bytes globales.
Aviso de compatibilidad de arquitectura de LiquidCrystal_I2C, sin error.
Carga: salida 1; salida relevante:

```text
Performing 1200-bps touch reset on serial port /dev/ttyACM0
Set binary mode
Send auto-baud
Set binary mode
No device found on ttyACM0
Failed uploading: uploading error: exit status 1
```

Después del intento, `arduino-cli board list` siguió detectando UNO R4 WiFi
en `/dev/ttyACM0`, con el mismo enlace USB persistente. No se observó otro
puerto en la consulta posterior; no hubo monitorización continua del intento.
La enumeración USB no demuestra respuesta del bootloader. El fallo está
en el establecimiento de comunicación de bossac; su causa última aún no se
ha demostrado. La hipótesis a comprobar es que el reset automático no deja
el microcontrolador en un bootloader accesible.

## Verificación y pendientes

`.venv/bin/python -m unittest discover -s tests -v`: 39 casos,
38 aprobados y 1 omitido por ausencia de qrcode/OpenCV; cero fallos.
No se demostró un defecto del código y no se modificó el firmware ni Python.
No se alteraron mediciones anteriores ni métodos numéricos.

Se requiere pulsar RESET dos veces rápidamente sin desconectar USB, luego
volver a detectar el puerto y cargar el firmware principal ya compilado.
La comunicación serial, captura nueva y observación física de LCD posteriores
a una carga correcta siguen pendientes. No se declara éxito físico.

## Continuación tras «listo» del usuario

- La consulta posterior al RESET mantuvo `/dev/ttyACM0` y el mismo enlace USB.
  `fuser` no mostró ocupantes.
- Se repitió la carga principal con el mismo comando y binario: salida 1,
  `No device found on ttyACM0`, después del touch de 1200 baudios.
- Consulta directa sin reset ni escritura:
  `bossac -d --port=ttyACM0 -U -i`; también terminó con salida 1 y
  `No device found on ttyACM0`.
- Se ejecutó el capturador real a 115200, con límite de 20 muestras y duración
  solicitada de 12 segundos. Resultado: salida 2, 0 muestras, 0 líneas inválidas.
  CSV nuevo: `datos/mediciones/diagnostico_serial_2026-10-16_post_reset_01.csv`.
  Es una captura vacía, no evidencia de mediciones válidas.
- Falta confirmar visualmente si el LED integrado L pulsa después del doble
  RESET. Próxima comprobación: entrada manual y consulta directa del bootloader
  antes de cualquier touch automático. No está demostrado que el puente esté
  dañado ni que el doble RESET haya activado el bootloader.

## Continuación con indicación visual de bootloader

El usuario informó LED integrado pulsando suavemente y LCD detenida en una
lectura de 5. Es compatible con bootloader activo; no es observación directa
del agente. La consulta `bossac -d --port=ttyACM0 -U -i`, sin touch automático,
volvió a fallar con `No device found on ttyACM0`. No se realizó otra escritura.

`fuser` y `lsof` no detectaron ocupantes; ModemManager estaba inactivo y su
journal sin entradas recientes. La configuración serial consultada era 115200,
8 bits, sin paridad ni control de flujo. El árbol USB mostró cdc_acm y usbhid.
No aparecieron eventos USB/ttyACM/cdc_acm en los últimos 15 minutos consultados.

Se intentó recuperar la conexión con `usbreset 2341:1002`: imprimió
`can't open [Permission denied]` pese a devolver código 0, por lo que NO se
considera reinicio realizado. El intento puntual autorizado
`sudo -n /usr/bin/usbreset 2341:1002` falló con salida 1:
`sudo: a password is required`. No se solicitó ni manejó la contraseña.

Pendiente: ejecutar ese reinicio USB desde la terminal local del usuario,
volver a detectar el puerto y consultar el bootloader. No hay evidencia para
afirmar corrupción del puente, y no se actualizó su firmware ni se cambiaron
permisos globales. La carga principal y la comunicación siguen sin resolver.

## Después del reinicio USB ejecutado por el usuario

El usuario comunicó `Resetting UNO WiFi R4 CMSIS-DAP ... ok`.
Se volvió a detectar la placa en `/dev/ttyACM0`. La consulta directa bossac
sin reset automático volvió a fallar con salida 1, `No device found`.

Para comprobar si el fallo dependía de los tiempos de bossac se abrió el
puerto con PySerial, acceso exclusivo, DTR/RTS activos, timeout de lectura de
1 segundo y escritura de 2 segundos. A 115200 y a 921600 baudios se enviaron
únicamente `N#` (modo binario) y `V#` (consulta de versión), siguiendo el
protocolo del código oficial de BOSSA. Cada escritura aceptó 2 bytes; las
cuatro lecturas devolvieron `b''`. Se dejó la velocidad en 115200 y se cerró
el puerto. No se enviaron órdenes de borrado, escritura flash ni ejecución.

Fuentes consultadas:
- https://raw.githubusercontent.com/arduino/BOSSA/master/src/Samba.cpp
- https://raw.githubusercontent.com/arduino/uno-r4-wifi-usb-bridge/main/UNOR4USBBridge/UNOR4USBBridge.ino

El fallo no se limita al parser Python ni al tiempo de espera corto de bossac.
No hay evidencia suficiente para decidir entre bloqueo temporal del puente,
problema de firmware o hardware en la comunicación interna. Reiniciar USB no
equivale a cortar la alimentación de la placa. Un ciclo completo de alimentación
requiere intervención del usuario y aclarar si existe otra fuente de energía;
se solicita permiso por la restricción de no cambiar conexiones físicas.
No se ha cargado firmware nuevo ni verificado serial/LCD después de una carga.

## Después de desconectar y reconectar la alimentación USB

El usuario confirmó alimentación exclusivamente USB y reconexión. Linux
registró desconexión a las 01:34:48 y conexión a las 01:34:54 (hora del journal).
La placa reapareció en `/dev/ttyACM0`, mismo identificador persistente. No se
detectaron ocupantes antes de iniciar la carga principal. Durante la enumeración
apareció un error nuevo:

```text
usb 6-1: device descriptor read/64, error -71
```

La enumeración continuó y se registraron interfaces HID y cdc_acm. Se reintentó
la carga principal con el binario previamente compilado. Tras el touch de 1200
baudios se inició bossac, pero quedó en `tty_wait_until_sent`, sin salida de
escritura completada. Se terminaron únicamente los procesos de este intento
(bossac PID 32503 y CLI PID 32032) con SIGTERM; la sesión salió con código 143.
No hay evidencia de carga exitosa ni de verificación del contenido de flash.

La documentación del kernel relaciona errores EPROTO con fallos del dispositivo,
su firmware o el cable; este evento aislado no permite atribuir una causa única:
https://cdn.kernel.org/doc/html/latest/driver-api/usb/error-codes.html

Se repitió la suite completa: 39 casos en 3.444 s, 38 aprobados y 1 omitido
por qrcode/OpenCV ausentes. Ningún cambio al firmware, parser o métodos.
Siguiente prueba propuesta: cambiar una sola variable del enlace USB (primero
otro puerto directo del PC con el mismo cable), previa autorización por la
restricción de conexiones físicas. La captura válida y LCD posterior a carga
siguen pendientes.

## Recuperación tras cambio de cable

El usuario confirmó el cambio de cable y conexión. El journal mostró además
un cambio de ruta de `usb 6-1` (controlador 09:00.3) a `usb 8-1`
(controlador 09:00.4). Por tanto, no se aisló exclusivamente la variable cable.
El error de descriptor `-71` apareció también en la nueva conexión antes de
enumerar correctamente; no impidió las operaciones exitosas posteriores.

Antes de cargar se obtuvieron 10 muestras válidas, cero inválidas, en
`datos/mediciones/diagnostico_serial_2026-10-16_cable_nuevo_01.csv`.
Se cargó el firmware principal previamente compilado con Arduino CLI, usando
un límite externo de 45 segundos. Esta vez el touch automático funcionó y
bossac respondió:

```text
version()=Arduino Bootloader (SAM-BA extended) 2.0 [Arduino:IKXYZ]
Connected at 921600 baud
Write 59360 bytes to flash (15 pages)
100% (15/15 pages)
Done in 4.022 seconds
reset()
New upload port: /dev/ttyACM0 (serial)
```

Salida de carga 0. No se hizo una verificación independiente byte a byte de
flash; sí se verificó el funcionamiento serial del firmware tras la carga.

Se abrió `arduino-cli monitor` con baudrate=115200, DTR/RTS activos.
Hubo una ráfaga inicial ilegible; luego se observaron tramas estables como
`34076,3,34,4` y `34576,3,33,3`. Se cerró mediante timeout deliberado a los
7 segundos (salida 124, cierre esperado del monitor).

Captura posterior con el receptor Python del repositorio:

```sh
.venv/bin/python -m python.main capturar --puerto /dev/ttyACM0 --baudios 115200 --muestras 30 --duracion 20 --salida datos/mediciones/diagnostico_serial_2026-10-16_cable_nuevo_post_carga_01.csv
```

Salida 0: 30 muestras, 0 líneas inválidas. Los 29 intervalos `t_ms` fueron
exactamente 500 ms. Rangos ADC: S1 2..4, S2 18..24, S3 1..3. No se conoce
la altura ni el estado del agua, por lo que no son datos de calibración.
SHA-256 del CSV:
`f215da0c02659469ebafc04ee08210be3528d80a61c63a84ee8b27f04c06353f`.

Conclusión: carga y comunicación recuperadas con la nueva conexión física,
sin modificar software ni actualizar el ESP32-S3. La causa específica entre
cable, contacto, puerto/controlador o estado transitorio no queda demostrada.
El usuario confirmó después de esta carga que la LCD sí actualiza las lecturas
(«aa si si actualiza»). Esta verificación visual fue comunicada por el usuario,
no observada directamente por el agente ni deducida de las pruebas simuladas.
Quedan comprobadas la carga principal, la recepción serial con el parser real
y la actualización de la LCD. No se realizaron pruebas nuevas de inmersión ni
calibración física durante este diagnóstico.
