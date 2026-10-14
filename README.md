# Proyecto 1 — Métodos Numéricos: nivel de agua

Universidad Tecnológica de Panamá. Problema 11. Implementación académica
verificada; integración física parcial. Todos los archivos originales de
clase se conservan fuera de esta carpeta.

## Ejecutar ahora

Desde la carpeta raíz `metnum`:

```bash
cd Proyecto1
.venv/bin/python -m python.main resolver
.venv/bin/python -m unittest discover -s tests -v
```

El entorno `.venv` de esta sesión ya está preparado. Usa NumPy y PySerial
existentes y Matplotlib del entorno de `10Sep2026` mediante un archivo `.pth`
local. No se instaló nada globalmente. Este enlace depende de esa ubicación;
para otra computadora cree su propio entorno e instale los requisitos:

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
```

En Windows use `.venv\Scripts\python.exe` en lugar de `.venv/bin/python`.
Las pruebas usan `unittest`, incluido en Python; no requieren pytest.
En esta sesión PyPI no es accesible: `qrcode` y OpenCV siguen ausentes.

## Demostración sin hardware

```bash
.venv/bin/python -m python.main resolver --tol 0.001 --max-iter 100 --x0 0 0 0
.venv/bin/python -m python.main resolver --tol 1e-10 --salida /tmp/metnum-precision
.venv/bin/python -m python.main resolver --sin-graficas
```

El programa utiliza exclusivamente `A=[[5,-1,0],[-1,5,-1],[0,-1,4]]` y
`b=[20,30,25]`. Estos son datos académicos del profesor, no lecturas del circuito.
La solución exacta es `(75/13,115/13,110/13)`.

Por defecto para cuando `||h(k)-h(k-1)||∞ < 0.001`, con un máximo de 100 pasos.
No redondea durante el cálculo. Devuelve código de salida 2 si algún método
no cumple el criterio, o si se encuentra una entrada inválida.

Guarda en `datos/resultados/` las tablas `jacobi.csv`, `gauss_seidel.csv`,
`gauss_jordan_operaciones.csv`, `comparacion.csv` y `resumen.json`.
Las tablas incluyen `k=0`, cambios absolutos por componente y en norma infinito,
cambios relativos, componentes del residuo y norma del residuo. Un campo vacío
significa que el error no está definido; nunca se divide entre cero.

En `graficas/` guarda `convergencia.png`, `residuos.png`,
`niveles_iteraciones.png` y `comparacion_metodos.png`. Son figuras académicas
sin unidades físicas asignadas. Cada ejecución vuelve a generar estos archivos
derivados; use `--salida` para conservar una ejecución distinta.

## Arduino y captura real

El firmware actual es [NivelAguaR4.ino](arduino/NivelAguaR4/NivelAguaR4.ino),
para **Arduino UNO R4 WiFi**, FQBN `arduino:renesas_uno:unor4wifi`.
Fija `analogReadResolution(10)` y transmite por USB a **115200 baudios**,
con cabecera `tiempo_ms,sensor1,sensor2,sensor3` y cuatro enteros por línea.
El cableado confirmado es sensor 1 en **A0**, sensor 2 en **A2** y sensor 3
en **A3**, con alimentación indicada de 5 V y GND compartido.
Los canales se leen consecutivamente cada 500 ms, no simultáneamente.
La LCD está habilitada en **0x27**, SDA/A4 y SCL/A5, y el equipo confirmó
visualmente que muestra lecturas. El problema anterior se debió a no identificar
cuándo terminaba la carga del firmware. Los LED RGB tienen la lógica de
colores preparada, pero la versión actual ordena mantener sus canales apagados
porque faltan límites ADC medidos por sensor.

El usuario asignó las ternas D2/D3/D4, D5/D6/D7 y D8/D9/D10; al conservar
los órdenes de color indicados, quedan LED 1 R2/G3/B4, LED 2 R7/G6/B5 y
LED 3 R10/G9/B8.
[Las conexiones LED](documentos/CONEXIONES_LED.md) están anotadas;
el usuario confirmó los tres grupos de pines y falta comprobar visualmente
la correspondencia de cada color. Las luces encendidas visibles en el montaje
no prueban por sí solas el control correcto de los tres RGB. El firmware
rechaza pines LED fuera de D2..D10, repetidos o compartidos con sensores/LCD y mantiene
los canales apagados hasta registrar los límites ADC reales.

Consulte [la guía del firmware](arduino/NivelAguaR4/README.md) para compilar,
cargar, configurar LCD/LED y probar el circuito.
Compilar no carga nada en la placa:

```bash
XDG_CACHE_HOME=/tmp/proyecto1-r4-cache arduino-cli compile --fqbn arduino:renesas_uno:unor4wifi --build-path /tmp/proyecto1-r4-build arduino/NivelAguaR4
```

El [sketch anterior](arduino/sensores/sensores.ino) se conserva intacto como
referencia a 9600 baudios (`t_ms,adc1,adc2,adc3`). Python acepta ambas cabeceras;
para usarlo indique `capturar --baudios 9600` junto con las demás opciones.
La captura actual usa 115200 por defecto y mantiene las columnas guardadas
`timestamp_utc,t_ms,adc1,adc2,adc3,origen` para las gráficas y la calibración.

```bash
.venv/bin/python -m python.main puertos
.venv/bin/python -m python.main capturar --puerto /dev/ttyACM0 --baudios 115200 --muestras 100 --duracion 60 --salida datos/mediciones/ensayo_01.csv
.venv/bin/python -m python.main graficar --csv datos/mediciones/ensayo_01.csv --salida graficas/adc_ensayo_01.png
```

En Windows sustituya el puerto por `COM3` o el que corresponda. Si hay un único
puerto puede omitirse `--puerto`; con varios se exige seleccionarlo.
Cierre el monitor serial del IDE antes de capturar. Abrir el puerto puede
reiniciar UNO. El receptor espera mensajes completos, descarta líneas inválidas
y registra las válidas con hora de recepción UTC y origen `experimental`.
La marca UTC es del computador; no es una medición del instante exacto de ADC.
No sobrescribe CSV existentes. Una desconexión termina con error y conserva
las filas ya escritas; no hay reconexión automática. La duración limita la
espera y una lectura serial puede añadir hasta un timeout al cierre.

## Escáner I²C

Para identificar primero la dirección de la LCD, está disponible el
[escáner I²C independiente](arduino/EscanerI2C/README.md), con su sketch
`arduino/EscanerI2C/EscanerI2C.ino`. Busca de 0x01 a 0x7E mediante Wire y
usa serial a 115200. Compilado para UNO R4 WiFi; la placa se reconoció en
`/dev/ttyACM0`. Tras confirmar el usuario el cambio de cableado (sensor 1 A0,
sensor 2 A2, sensor 3 A3; LCD SDA A4/SCL A5), se cargó el escáner autorizado
y se detectó **un dispositivo en 0x27**, con cero errores en seis recorridos
completos legibles. Hubo caracteres ilegibles iniciales al conectar el monitor;
la salida posterior fue estable. El escáner se conserva como diagnóstico
independiente. Después se cargó el firmware principal con estos pines y LCD
habilitada; el equipo confirmó posteriormente su funcionamiento visual.
Registro: [escaneo real](documentos/ESCANEO_I2C_2026-10-12.txt).

## Calibración pendiente

Se realizaron pruebas físicas de los sensores y se observaron lecturas ADC
diferentes. Los tres recipientes están montados y conectados mediante tubos,
según la actualización del equipo. Ya se registró una primera captura real de 20 muestras sin líneas inválidas,
con intervalos Arduino de 500 ms. No se documentó la altura del agua durante
esa captura, por lo que no se usa como calibración. Véanse el
[registro de integración](documentos/INTEGRACION_R4_2026-10-12.md), la
[gráfica ADC real](graficas/adc_ensayo_r4_2026-10-12_2153UTC.png) y el
[protocolo de calibración](documentos/CALIBRACION_CIRCUITO.md).

Mida por separado para cada sensor varios pares `(ADC,altura)` con una regla.
Mantenga orientación, agua y alimentación consistentes, y registre repeticiones.
Ordene los puntos por ADC y verifique que las alturas aumenten. La conversión
implementada interpola linealmente entre puntos medidos y rechaza lecturas fuera
del rango calibrado. Si la respuesta no es monotónica, revise las mediciones
antes de usar este modelo.

Cree un JSON con una clave `unidad` (`cm`, `mm`, `m` o `%`) y una clave
`sensores`; esta última debe contener `adc1`, `adc2` y `adc3`, cada una con una
lista de al menos dos pares numéricos `[ADC,altura]`. No se entrega un archivo
con coeficientes ficticios. Para porcentaje, documente qué alturas representan
0 % y 100 %; no use automáticamente ADC/1023 como porcentaje de agua.

```bash
.venv/bin/python -m python.main graficar --csv datos/mediciones/ensayo_01.csv --calibracion datos/calibracion_real.json --salida graficas/niveles_ensayo_01.png
```

El CSV original conserva los ADC. Las alturas se calculan para graficar y
también pueden obtenerse con `python.calibracion.convertir`. No se reemplaza
`b` por alturas sin justificar un modelo de balances y sus unidades.

## QR: herramienta preparada, contenido final pendiente

El ejemplo de clase codifica identificadores que seleccionan sistemas de un
diccionario. Ninguna guía de Proyecto 1 define si su QR debe hacer eso o abrir
un informe/enlace. Confirme ese punto antes de producir la imagen de entrega.
Cuando el contenido esté confirmado:

```bash
.venv/bin/python -m pip install -r requirements.txt -r requirements-qr-lectura.txt
.venv/bin/python -m python.main qr --contenido 'CONTENIDO_CONFIRMADO' --salida documentos/qr_proyecto.png --verificar
```

Sustituya el texto por el contenido real. La herramienta genera PNG y una copia
de texto; `--verificar` decodifica con OpenCV y compara exactamente el resultado.
No se ha generado ni validado un QR definitivo en esta ejecución. Tampoco se
implementó selección automática del Problema 11 por QR sin confirmar ese flujo.

## Estructura

```text
Proyecto1/
├── arduino/EscanerI2C/      # diagnóstico independiente del bus Wire
├── arduino/NivelAguaR4/      # firmware UNO R4 WiFi y guía de montaje/pruebas
├── arduino/sensores/sensores.ino  # referencia anterior conservada
├── python/                  # main, metodos, graficas, calibracion, comunicacion, qr
├── tests/                   # unittest: matemática, adquisición, PNG y terminal
├── datos/mediciones/        # capturas reales ADC; calibración física pendiente
├── datos/calibracion/       # plantilla vacía para registrar puntos medidos
├── datos/resultados/        # CSV y JSON académicos
├── graficas/                # cuatro PNG académicos
├── documentos/              # requisitos, modelo, avance, plan y fuentes extraídas
├── requirements.txt
└── requirements-qr-lectura.txt
```

Consulte [requisitos y fuentes](documentos/REQUISITOS.md),
[deducción matemática](documentos/MODELO.md) e
[informe de avance](documentos/AVANCE.md). El
[estado actual](documentos/ESTADO_ACTUAL.md) y el
[registro de validación](documentos/VALIDACION_CORRECTIVA_2026-10-14.md)
separan las conclusiones recientes de los registros históricos.
Para repetir el inventario: `.venv/bin/python documentos/inspeccionar_fuentes.py`.

La próxima actividad física es medir la geometría, comprobar el intercambio
hidráulico entre compartimentos y registrar una calibración independiente para
cada sensor. Existen fotografías del montaje, pero aún deben agregarse a
`documentos/evidencias/` para poder revisarlas y citarlas. No se requiere
repetir la carga del firmware para documentar el funcionamiento ya observado.
