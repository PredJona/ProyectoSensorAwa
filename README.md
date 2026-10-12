# Proyecto 1 — Métodos Numéricos: nivel de agua

Universidad Tecnológica de Panamá. Problema 11. Implementación académica
verificada; integración física pendiente. Todos los archivos originales de
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

## Arduino y captura real, cuando esté disponible

Abra `arduino/sensores/sensores.ino` en Arduino IDE, seleccione Arduino UNO y
el puerto adecuado, y cargue el sketch. Conecte señales a A0, A1 y A2 según
el número de compartimento, con alimentación 5 V y GND compartidos.
El intervalo se cambia en `INTERVALO_MS` (500 ms inicialmente).
El sketch no requiere LCD ni otras bibliotecas.

La salida serial a 9600 baudios tiene cabecera `t_ms,adc1,adc2,adc3`, seguida
de cuatro enteros por línea. `t_ms` es el contador Arduino y los ADC están en
0..1023. Los tres canales se leen consecutivamente, no simultáneamente.

```bash
.venv/bin/python -m python.main puertos
.venv/bin/python -m python.main capturar --puerto /dev/ttyACM0 --muestras 100 --duracion 60 --salida datos/mediciones/ensayo_01.csv
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

## Calibración pendiente

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
├── arduino/sensores/sensores.ino
├── python/                  # main, metodos, graficas, calibracion, comunicacion, qr
├── tests/                   # unittest: matemática, adquisición, PNG y terminal
├── datos/mediciones/        # todavía sin capturas reales
├── datos/resultados/        # CSV y JSON académicos
├── graficas/                # cuatro PNG académicos
├── documentos/              # requisitos, modelo, avance, plan y fuentes extraídas
├── requirements.txt
└── requirements-qr-lectura.txt
```

Consulte [requisitos y fuentes](documentos/REQUISITOS.md),
[deducción matemática](documentos/MODELO.md) e
[informe de avance](documentos/AVANCE.md).
Para repetir el inventario: `.venv/bin/python documentos/inspeccionar_fuentes.py`.

La próxima actividad física es medir la geometría y confirmar la comunicación
entre compartimentos, cargar el sketch y registrar una calibración independiente
para cada sensor. La fotografía del montaje y las conclusiones experimentales
solo se completan después de hacerlo.
