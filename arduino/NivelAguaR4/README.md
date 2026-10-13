# Nivel de agua — Arduino UNO R4 WiFi

Firmware basado en `../sensores/sensores.ino`, que se conserva intacto.
Mantiene tres lecturas consecutivas cada 500 ms con `millis()`, incluido
su desbordamiento de 32 bits. No realiza filtrado ni convierte ADC a altura,
porcentaje o volumen. La calibración física sigue separada en Python.

## Configuración del circuito

| Elemento | Configuración | Evidencia |
|---|---|---|
| Placa | UNO R4 WiFi, `arduino:renesas_uno:unor4wifi` | Reconocida por USB |
| Sensor 1 / 2 / 3 | A0 / A2 / A3, `PINES_SENSORES` | Cambio de cableado confirmado por usuario |
| Alimentación | 5 V y GND común | Indicada por usuario |
| ADC | `analogReadResolution(10)`, 0..1023 | Resolución, no extremos de calibración |
| USB serial | `Serial.begin(115200)` | Captura real con Python |
| Muestreo | `INTERVALO_MS = 500` | Captura con intervalos de 500 ms |
| LCD | Habilitada, dirección `0x27`, SDA/A4 y SCL/A5 | Dirección medida con escáner; lectura visual pendiente |
| LED RGB | Cátodo común; LED 1 R2/G3/B4, LED 2 R7/G6/B5, LED 3 R10/G9/B8 | Grupos de pines confirmados por usuario; comprobar cada color |

El ADC se envía como `tiempo_ms,sensor1,sensor2,sensor3`, seguido de cuatro
enteros por línea con terminador CRLF. El tiempo es `millis()` al comenzar
las tres lecturas consecutivas, no simultáneas. No equivale a hora UTC.
No se espera al monitor serial para arrancar; un receptor tardío puede perder
la cabecera. Python admite datos sin ella y conserva las columnas
`timestamp_utc,t_ms,adc1,adc2,adc3,origen`.
No se mezclan mensajes de diagnóstico ni estados LCD/LED en ese CSV.

## Compilar y cargar

Desde la raíz `Proyecto1`, con core **Arduino UNO R4 Boards** instalado:

```bash
arduino-cli version
arduino-cli core list
arduino-cli board list
XDG_CACHE_HOME=/tmp/proyecto1-r4-cache arduino-cli compile --fqbn arduino:renesas_uno:unor4wifi --build-path /tmp/proyecto1-r4-build arduino/NivelAguaR4
arduino-cli upload --fqbn arduino:renesas_uno:unor4wifi --port /dev/ttyACM0 --input-dir /tmp/proyecto1-r4-build arduino/NivelAguaR4
```

El usuario autorizó continuar con la integración y la prueba. Repetir la carga
solo cuando se quiera ejecutar esta versión, cerrando antes cualquier monitor
o captura. Sustituir el puerto si cambia. Compilar por sí solo no carga nada.
No usar `arduino:avr:uno`; el sketch rechaza placas distintas de UNO R4 WiFi.
En una comprobación anterior la placa no estaba conectada. Después apareció
como `/dev/ttyACM0`, se cargó esta versión con las tres ternas LED y Python
recibió 10 muestras CSV válidas. La respuesta física de LCD, sensores y LED
todavía debe comprobarse en el circuito.
En IDE abrir `NivelAguaR4.ino`, seleccionar UNO R4 WiFi y el puerto detectado.
Las herramientas y bibliotecas utilizadas ya estaban instaladas por usuario;
la caché y los productos de compilación van a `/tmp`.

## LCD

Se usa **LiquidCrystal_I2C 2.0.0**, de Martin Kubovčík y Frank de Brabander.
API: constructor con dirección y 16×2, `init()`, `backlight()`, `setCursor()`
y `print()`. Hay bibliotecas homónimas con otras API: comprobar autor y versión.
Fuente: [código del mantenedor](https://github.com/markub3327/LiquidCrystal_I2C).

`NIVEL_AGUA_LCD=1` y `NIVEL_AGUA_LCD_DIRECCION=0x27` son ahora los valores
predeterminados. Esta dirección se obtuvo del circuito real con el
[escáner independiente](../EscanerI2C/README.md), no de un ejemplo de clase.
La biblioteca usa Wire: SDA/A4 y SCL/A5. Qwiic pertenece a Wire1 y no se utiliza.
Fuente: [manual UNO R4 WiFi](https://docs.arduino.cc/tutorials/uno-r4-wifi/cheat-sheet/).

La primera fila muestra S1 y S2; la segunda, S3 y `ADC`. Se escriben 16
columnas para borrar dígitos anteriores sin `clear()` en cada muestra.
No se muestran alturas ni porcentajes sin calibración. Si la dirección no
responde al arrancar, continúa la adquisición sin pantalla. El timeout I²C
se fija en 25000 microsegundos; no hay reconexión automática de la LCD.

La biblioteca instalada declara literalmente `architectures=all`; el CLI
emite un aviso sobre Renesas, aunque compila correctamente. No se modificó
la biblioteca para ocultar el aviso. Un ACK y la compilación no sustituyen
la comprobación visual de texto: sigue pendiente que el usuario la confirme.

Para compilar sin LCD, sin editar el archivo:

```bash
XDG_CACHE_HOME=/tmp/proyecto1-r4-cache arduino-cli compile --fqbn arduino:renesas_uno:unor4wifi --build-path /tmp/proyecto1-r4-sin-lcd-build --build-property 'compiler.cpp.extra_flags=-DNIVEL_AGUA_LCD=0' arduino/NivelAguaR4
```

## LED RGB y calibración pendiente

`PINES_LED[3][3]` usa el orden **R, G, B** para cada LED. Los nueve pines
asignados se configuran como salidas y se mantienen en LOW (apagados) mientras
falte la calibración.
`NIVELES_ACTIVOS_LED` usa HIGH para los RGB de cátodo común confirmados.
El usuario indicó resistencias «220»; falta confirmar 220 Ω y una por canal.

La asignación actual es LED 1 R2/G3/B4, LED 2 R7/G6/B5 y LED 3
R10/G9/B8. La [tabla de conexiones](../../documentos/CONEXIONES_LED.md)
registra el orden de colores inferido de la descripción anterior y lo que
falta comprobar visualmente.
`pinesLedValidos()` rechaza conjuntos incompletos, duplicados o que utilicen
los pines de sensores/LCD antes de configurar salidas.

`ColoresNivel.h` implementa la política acordada con canales digitales:
vacío morado (R+B), bajo verde (G), medio amarillo (R+G), alto rojo (R).
No se implementa mezcla PWM ni regulación de brillo.
`LIMITES_ADC_LED[3][3]` contiene los máximos ADC para vacío, bajo y medio
de cada sensor. Los tres límites deben estar en 0..1023 y aumentar
estrictamente; valores superiores al límite de medio se clasifican como alto.
La política requiere que la respuesta ADC aumente con el agua.

Todos los límites siguen en `-1`, sin inventar valores. Con configuración
incompleta o inválida, los colores quedan apagados. Rellenar solo los pines
no activa los avisos: primero medir la calibración.
Antes de asignarlos, comprobar que sean pines válidos, distintos y no
compartidos con A0/A2/A3 ni SDA/SCL ni otro periférico.
El significado de los colores representa la política del proyecto; las alturas
se calculan por separado a partir de puntos medidos en Python.

Protocolo y plantilla: [CALIBRACION_CIRCUITO.md](../../documentos/CALIBRACION_CIRCUITO.md).

## Captura y gráficas

```bash
.venv/bin/python -m python.main capturar --puerto /dev/ttyACM0 --baudios 115200 --muestras 100 --duracion 60 --salida datos/mediciones/ensayo_r4_02.csv
.venv/bin/python -m python.main graficar --csv datos/mediciones/ensayo_r4_02.csv --salida graficas/adc_ensayo_r4_02.png
```

Usar un nombre nuevo por ensayo: no sobrescribe capturas. Python guarda
origen `experimental` para la adquisición real y `prueba_controlada` en tests.
Las gráficas temporales usan la recepción UTC del computador y etiquetas de
sensor sin asumir los pines de capturas históricas.
El sketch anterior sigue disponible a 9600; usar `--baudios 9600` al capturarlo.

## Verificación

```bash
.venv/bin/python -m unittest discover -s tests -v
```

Las pruebas nativas con g++ verifican A0/A2/A3, ADC de 10 bits, CSV,
muestreo y desbordamiento, LCD con filas completas y lógica de colores en
límites y configuraciones inválidas. Usan E/S simulada, no observación física.
La prueba sin LCD se compila explícitamente con `NIVEL_AGUA_LCD=0`.
Se conservan las pruebas Python de recepción, calibración, métodos y PNG.

Se realizó una primera captura real de 20 muestras, sin líneas inválidas,
a intervalos Arduino de 500 ms. ADC observados: sensor 1, 5..10; sensor 2,
6..12; sensor 3, 6..16. No se conoce la altura ni el estado de agua durante
esa captura: no constituye calibración ni valida la respuesta a inmersión.
Registro de integración: [INTEGRACION_R4_2026-10-12.md](../../documentos/INTEGRACION_R4_2026-10-12.md).
