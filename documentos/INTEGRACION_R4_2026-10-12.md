# Integración y prueba real — 12 octubre 2026

Se cargó el firmware principal de UNO R4 WiFi con sensores en A0/A2/A3,
LCD habilitada en 0x27 sobre SDA/A4 y SCL/A5, resolución ADC de 10 bits y
salida CSV a 115200 baudios cada 500 ms. El usuario confirmó el cambio de
conexiones. El agente no inspeccionó visualmente ni movió los cables.

**Actualización posterior de LED:** el usuario asignó LED 1 R2/G3/B4,
LED 2 R7/G6/B5 y LED 3 R10/G9/B8, interpretando el orden de colores anterior.
El firmware ya contiene esos pines; los
canales quedan en LOW hasta medir los límites ADC. Falta verificar el cableado
físico actualizado. La compilación y carga descritas más abajo corresponden a
la versión anterior, con los pines LED aún en -1.

La versión actual compiló para `arduino:renesas_uno:unor4wifi` con salida 0:
59344 bytes de programa y 9020 bytes globales. La suite completa pasó
(36 pruebas, 35 correctas y una omitida por qrcode/OpenCV). En una consulta
anterior no había placa, pero después `arduino-cli board list` detectó el
UNO R4 WiFi en `/dev/ttyACM0`. Se cargó esta versión correctamente: 59352
bytes escritos en 15 páginas. Python recibió 10 muestras CSV válidas, sin
líneas inválidas, con intervalos Arduino de 500 ms. Los ADC fueron S1
994..995, S2 994 y S3 994..995 durante la captura; no se conoce el estado
del agua, por lo que no son puntos de calibración. El archivo local es
[ensayo_r4_led_pines_2026-10-12.csv](../datos/mediciones/ensayo_r4_led_pines_2026-10-12.csv).
La [gráfica ADC del ensayo](../graficas/adc_ensayo_r4_led_pines_2026-10-12.png)
se generó con el módulo Python del proyecto y muestra las tres series cerca
de 994 durante esos diez puntos.
La LCD y los LED aún no se han verificado visualmente.

## Cambios finales

- `arduino/NivelAguaR4/NivelAguaR4.ino`: pines confirmados, LCD habilitada,
  timeout I²C y preparación de RGB de cátodo común.
- `arduino/NivelAguaR4/ColoresNivel.h`: política vacío morado, bajo verde,
  medio amarillo y alto rojo. Requiere límites ADC crecientes medidos por
  sensor. Configuración incompleta/incorrecta produce apagado.
- `LIMITES_ADC_LED` sigue en -1; no se encienden salidas LED. No se inventaron
  alturas, umbrales ni porcentajes.
- Tras recibir los pines, se añadieron pruebas y una protección que rechaza
  asignaciones repetidas, faltantes o que usen A0/A2/A3/SDA/SCL. La conexión
  anterior compartía D4 entre los azules de LED 1 y LED 2. El usuario cambió
  la segunda terna a D5/D6/D7. Véase [CONEXIONES_LED.md](CONEXIONES_LED.md).
- `python/graficas.py`: etiquetas por sensor sin asociar pines que pudieran
  ser incorrectos para capturas anteriores.
- `tests/test_firmware.py`: A0/A2/A3, LCD con borrado de dígitos anteriores,
  colores en fronteras e invalidación de límites sin calibración.
- `documentos/CALIBRACION_CIRCUITO.md` y plantilla CSV vacía: procedimiento
  para registrar alturas y lecturas reales antes de definir los estados.

El sketch previo `arduino/sensores/sensores.ino` y el escáner independiente
se conservan. No se instalaron paquetes ni se modificó la biblioteca LCD.

## Compilación y carga final

Herramientas existentes: arduino-cli 1.5.1, core Renesas UNO 1.6.0,
LiquidCrystal_I2C 2.0.0.

```bash
XDG_CACHE_HOME=/tmp/proyecto1-r4-cache arduino-cli compile --fqbn arduino:renesas_uno:unor4wifi --build-path /tmp/proyecto1-r4-build arduino/NivelAguaR4
arduino-cli upload --fqbn arduino:renesas_uno:unor4wifi --port /dev/ttyACM0 --input-dir /tmp/proyecto1-r4-build arduino/NivelAguaR4
```

Ambos terminaron con código 0. Tras añadir la protección de pines, la
compilación más reciente usó **59344 bytes de programa** y **9020 bytes de
variables globales**. La carga más reciente escribió 59352 bytes en 15
páginas, 100 %, 3.988 segundos; puerto posterior `/dev/ttyACM0`.
La placa quedó ejecutando esta versión principal, no el escáner. Esta captura
del registro es anterior a la asignación nueva de los nueve pines LED.

La biblioteca emitió el aviso conocido:

```text
WARNING: library LiquidCrystal_I2C claims to run on all architecture(s) and may be incompatible with your current board which runs on renesas_uno architecture(s).
```

Se conserva su metadato `architectures=all`; compilar no demuestra que la
pantalla muestre texto correctamente. Se solicitó confirmación visual al usuario.

## Capturas reales por Python

Se capturaron con el receptor del proyecto, no mediante un simulador.

| Captura | Muestras | Líneas inválidas | Intervalos Arduino | Sensor 1 ADC | Sensor 2 ADC | Sensor 3 ADC |
|---|---:|---:|---:|---|---|---|
| Inicial sensores + LCD, 21:53 UTC | 20 | 0 | 500 ms | 5..10 | 6..12 | 6..16 |
| Verificación de sensores/LCD, 21:58 UTC | 10 | 0 | 500 ms | 9..10 | 9..10 | 1..14 |

Archivos:

- [Primera captura](../datos/mediciones/ensayo_r4_2026-10-12_2153UTC.csv).
- [Gráfica de la primera captura](../graficas/adc_ensayo_r4_2026-10-12_2153UTC.png).
- [Captura de verificación de sensores/LCD](../datos/mediciones/ensayo_r4_2026-10-12_verificacion_final.csv).
- [Metadatos y huellas SHA-256 de esa captura](../datos/mediciones/ensayo_r4_2026-10-12_verificacion_final.metadata.json).

Esos metadatos conservan las huellas del código que se ejecutaba al momento
de la captura; son anteriores a la protección posterior de pines LED.

La primera captura va de 21:53:59.248989 a 21:54:08.785877 UTC. La segunda,
de 21:58:02.078177 a 21:58:06.593163 UTC. Las marcas UTC son de recepción.
Los CSV mantienen `timestamp_utc,t_ms,adc1,adc2,adc3,origen`, con origen
`experimental`. La exclusión Git de CSV ya existía; se conservan localmente.
Los puertos se cerraron automáticamente al terminar las capturas.

La gráfica se abrió y verificó: incluye tres series, eje temporal de recepción
y eje de cuentas ADC sin calibrar. La altura y el estado del agua durante
las capturas no están documentados. Estos rangos son observaciones de esas
capturas; **no son extremos de calibración ni umbrales de los LED**.

## Pruebas automáticas

```bash
.venv/bin/python -m unittest discover -s tests -v
```

Resultado más reciente: **36 casos, 35 aprobados y uno omitido**, sin fallos.
La omisión es `test_qr_roundtrip_real`, por qrcode/OpenCV ausentes.
Las pruebas de LCD y LED usan E/S simulada y datos controlados; no sustituyen
la observación de la pantalla, los colores físicos ni las alturas reales.

## Pendiente de datos físicos

1. Confirmar visualmente S1/S2 en la primera fila y S3/ADC en la segunda.
2. Variar agua de un sensor por vez y verificar el canal correspondiente.
3. Verificar físicamente que LED 2 esté en D5 azul, D6 verde y D7 rojo;
   confirmar las resistencias por canal.
4. Registrar pares ADC-altura independientes por sensor y definir estados.
5. Configurar límites, compilar/cargar y verificar los colores reales.

Se realizaron las acciones independientes que permitían los datos disponibles.
La calibración y la activación física de LED requieren esas mediciones.
