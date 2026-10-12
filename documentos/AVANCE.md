# Informe de avance real — 12 octubre 2026

Las fases matemáticas y de gráficas están implementadas y ejecutadas.
Arduino, captura y calibración están preparados; la validación física sigue
pendiente. Se trabajó en la carpeta Proyecto1 existente, sin modificar las
guías, sketches o proyectos originales, sin publicar ni hacer push.

## Material y requisitos

Se inventariaron 84 archivos originales y se extrajeron cuatro DOCX y tres
PPTX; se clasificaron los tres PDF como material de otro proyecto. Se revisaron
los ejemplos Python de métodos, QR y Matplotlib y el sketch de lectura ADC.
El ZIP de inventario se inspeccionó sin extraerlo. El alcance de lectura y las
fuentes específicas están en [REQUISITOS.md](REQUISITOS.md); los textos y el
inventario están en [fuentes_extraidas](fuentes_extraidas/).

Se aplicaron tol=0.001, máximo 100, vector inicial cero y norma infinito del
cambio < tol. Ambas guías PROYECTO se conservaron como complementarias; sus
fechas no demuestran cuál versión asignó el docente. Las rúbricas de Gauss y
Doolittle corresponden a otros bancos y su aplicabilidad está pendiente.
El QR de clase usa identificadores, pero falta definir el contenido del QR
de Proyecto 1. Estas decisiones evitan convertir ejemplos en requisitos.

## Archivos implementados

| Archivo / carpeta | Función |
|---|---|
| `python/metodos.py` | Validación, Jacobi, Gauss-Seidel, Gauss-Jordan con pivoteo, historial y exportación |
| `python/main.py` | Terminal: resolver, puertos, capturar, graficar y qr |
| `python/graficas.py` | Cuatro figuras académicas y función temporal ADC/altura |
| `python/comunicacion.py` | Parser estricto, captura USB, fragmentos, timeout, CSV UTC y conservación ante desconexión |
| `python/calibracion.py` | Validación de puntos e interpolación independiente por sensor |
| `python/qr.py` | Generación parametrizada, protección de destinos y lectura opcional |
| `arduino/sensores/sensores.ino` | Lecturas A0/A1/A2, formato CSV y muestreo con millis |
| `tests/` | Tests de matemática, terminal, PNG, calibración y protocolo serial |
| `documentos/` | Fuentes, plan, requisitos, modelo, este avance y registros de ejecución |
| `requirements*.txt`, `.gitignore`, `README.md` | Dependencias, exclusiones y guía de ejecución |

Se generaron cuatro CSV académicos y un resumen JSON en `datos/resultados`.
Las tablas incluyen el vector inicial, todos los barridos, errores absolutos
y relativos cuando están definidos, y residuos. El CSV de Gauss-Jordan
registra cada operación de fila y las matrices aumentadas completas.
No existen capturas reales en `datos/mediciones`.

## Resultados matemáticos

| Método | h1 | h2 | h3 | Actualizaciones | Norma infinito del residuo |
|---|---:|---:|---:|---:|---:|
| Jacobi | 5.769114690 | 8.845967110 | 8.461393363 | 9 | 6.725025e-4 |
| Gauss-Seidel | 5.769203920 | 8.846141764 | 8.461535441 | 6 | 1.221658e-4 |
| Gauss-Jordan | 5.769230769 | 8.846153846 | 8.461538462 | Método directo | 7.105427e-15 |

La referencia exacta `(75/13,115/13,110/13)` satisface Ah=b, verificada con
aritmética Fraction de Python. NumPy coincide con Gauss-Jordan en esta ejecución.
También se verificaron radios espectrales de aproximadamente 0.3 para Jacobi
y 0.09 para Gauss-Seidel, coherentes con la convergencia observada.
La deducción y sus supuestos están en [MODELO.md](MODELO.md).

## Pruebas ejecutadas

Comando: `.venv/bin/python -m unittest discover -s tests -v`, desde Proyecto1.
Resultado final: **29 casos, 28 aprobados y 1 omitido, sin fallos**.
La prueba omitida es `test_qr_roundtrip_real`: qrcode y OpenCV no están
instalados y PyPI no es accesible en este entorno. Eso no constituye una
verificación del QR final. El registro completo está en [PRUEBAS.txt](PRUEBAS.txt).

Los casos ejecutados comprueban convergencia y referencia independiente,
primer paso de cada método, tolerancia, vector inicial, error y residuo,
relativos indefinidos, singularidad y pivotes pequeños, dimensiones y números
inválidos, no convergencia, CSV, exportación por terminal y PNG.
La adquisición se prueba con bytes controlados y, adicionalmente, con
PySerial real sobre un pseudo terminal del sistema operativo; esto no usa
sensores físicos. Se comprueban tramas fragmentadas, datos fuera de rango,
timeout, desconexión y protección de archivos, interpolación y rechazo de
extrapolación. Las gráficas de prueba temporal se generan en directorios
temporales con origen `prueba_controlada`, no como mediciones del circuito.

La revisión independiente de código encontró tres problemas que se reprodujeron
con tests antes de corregirse: lectura serial continua sin newline, aceptación
de residuos desbordados de Gauss-Jordan y sobrescritura del texto lateral QR.
Sus tres pruebas fallaron antes de la corrección y pasaron después. La lectura
ahora comprueba el plazo entre bytes; la verificación rechaza números no
finitos; ambos destinos del QR se protegen. No quedan hallazgos pendientes
de esa revisión.

El sketch se compiló con:

```bash
XDG_CACHE_HOME=/tmp/metnum-cache arduino-cli compile --fqbn arduino:avr:uno --build-path /tmp/metnum-arduino-build arduino/sensores
```

Resultado: 2020 bytes de programa y 212 bytes de variables globales, con el
core AVR instalado. Registro: [COMPILACION_ARDUINO.txt](COMPILACION_ARDUINO.txt).
No se cargó en una placa ni se ensayó físicamente. El comando para listar
puertos se ejecutó y no devolvió puertos disponibles en esta sesión.

## Figuras generadas

- [convergencia.png](../graficas/convergencia.png): cambio entre iteraciones.
- [residuos.png](../graficas/residuos.png): norma del residuo.
- [niveles_iteraciones.png](../graficas/niveles_iteraciones.png): trayectorias h1, h2 y h3 en ambos métodos iterativos.
- [comparacion_metodos.png](../graficas/comparacion_metodos.png): soluciones de los tres métodos.

Se verificó su generación con tests y se inspeccionaron visualmente sus ejes,
títulos, leyendas y legibilidad. Todos los valores mostrados son académicos.
La función de mediciones está preparada; no se generó una figura experimental.

## Ejecución y pendientes

Desde `metnum`, ejecutar:

```bash
cd Proyecto1
.venv/bin/python -m python.main resolver
.venv/bin/python -m unittest discover -s tests -v
```

El entorno virtual local reutiliza paquetes disponibles; no se instalaron
dependencias globales. [README.md](../README.md) explica cómo crear un entorno
independiente, cambiar parámetros, capturar datos, calibrar y generar el QR.

Pendientes físicos: confirmar si los compartimentos se comunican realmente,
medir geometría y origen de alturas, cargar el sketch, calibrar cada sensor,
registrar capturas, producir la curva temporal, fotografiar el montaje y
formular conclusiones experimentales. No basta el residuo académico para
validar la exactitud de sensores.

Pendientes documentales: confirmar rúbrica, necesidad de eliminación de Gauss
o Doolittle, contenido/función QR y formato final de entrega. No hay un enlace
publicado ni un QR definitivo. Las hipótesis de aportes y salidas del modelo
académico no prueban que esos elementos existan en el montaje.

La siguiente tarea recomendada es obtener del equipo un esquema con dimensiones
y conexiones hidráulicas, y confirmar con el profesor rúbrica y QR. Con el
circuito disponible, iniciar la calibración independiente de los tres sensores.
