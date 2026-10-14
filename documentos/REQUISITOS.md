# Requisitos comprobados y procedencia

**Actualización posterior:** este inventario describe la inspección original
de material y sus conclusiones en ese momento. El equipo informó después que
la LCD funciona visualmente, los sensores se probaron físicamente, se
observaron distintas lecturas ADC y los tres recipientes están unidos por
tubos. Las [fotografías](evidencias/LEEME.md) se incorporaron y revisaron
posteriormente; la calibración por alturas reales sigue pendiente.
Véase [ESTADO_ACTUAL.md](ESTADO_ACTUAL.md); las filas históricas inferiores no
se deben interpretar como estado vigente del circuito.

Inspección realizada el 12 de octubre de 2026. El inventario reproducible
contiene 84 archivos originales de trabajo: 54 Python, 15 Arduino, 4 DOCX,
3 PPTX, 3 PDF, un ZIP y cuatro documentos de texto/Markdown/troff.
Excluye entornos virtuales, cachés, metadatos de editores y esta implementación.
Se recorrieron también archivos ocultos al inicio; no se encontró AGENTS.md
ni un repositorio Git operativo. `Proyecto1` existía y estaba vacía.

## Fuentes principales

Todas las guías y presentaciones siguientes están en
`QR_CON_FUNCIONES/CLASES Y PROYECTOS/CLASE PROYECTOS  JACOBI_GAUSS-SEIDEL/`.
Los textos íntegros extraídos, metadatos y listas de medios embebidos están
en [fuentes_extraidas](fuentes_extraidas/).

| ID | Archivo | Aplicabilidad y hallazgo |
|---|---|---|
| A | `PROYECTO Banco_Planteamientos_Deduccion_Jacobi_GaussSeidel_Sensores.docx` | Guía específica; problema 11 de compartimentos comunicados, continuidad, conversión calibrada, Jacobi y Gauss-Seidel. Incluye tabla de control de entregas. |
| B | `PROYECTO_Guia_Problemas_Sensores_Jacobi_GaussJordan.docx` | Guía específica; problema 11 con A, b y solución de referencia. Pide Jacobi, Gauss-Jordan, código Arduino/Python, gráficas de sensores/convergencia/error y foto. |
| C | `Banco_Problemas_Eliminacion_Gauss_Gauss_Jordan_Sensores.docx` | Banco de ejercicios; problema 11 tiene la misma A y b. Pide eliminación de Gauss y Gauss-Jordan, cuatro decimales y ofrece rúbrica sugerida. |
| D | `Banco_Problemas_Jacobi_GaussSeidel_Doolittle.pptx` | Banco de clase; Jacobi, Gauss-Seidel y Doolittle. Su problema 11 es de robot, no de nivel. No transferir numeración ni rúbrica automáticamente. |
| E | `Clases Método de Jacobi.pptx` | Explica despejes, vector cero y norma del cambio como máximo de diferencias. Su ejercicio usa tolerancia 0.0001. |
| F | `Clases Método de Gauss-Seidel.pptx` | Actualización inmediata, vector cero y tolerancia 0.0001 en el ejemplo. |

Se extrajo el contenido textual de los cuatro DOCX y las tres presentaciones,
incluyendo texto de tablas. Las fórmulas o capturas embebidas como imágenes no
se sometieron a OCR; las fórmulas implementadas se contrastaron con el texto,
el sistema de B y el código Python de clase.

## Otros materiales revisados

- `SolucionEcuacionesTodosLosMetodosJuntos.py`: referencia de validación,
  Jacobi, Gauss-Seidel, Gauss-Jordan con pivoteo y Doolittle. Usa un sistema
  eléctrico distinto y tolerancia 1e-10 en su demostración. Se reutilizan
  procedimientos, no sus datos ni efectos al importar el archivo.
- `QR_CON_FUNCIONES/CLASES Y PROYECTOS/CLASE QR ENTREGAR/`: revisados
  `LEEME_PRIMERO.txt`, `CrearQr.py`, `lector_qr.py`, `problemas.py`, `main.py`,
  `metodos.py` y ejemplos Spool. El flujo genera QR de `Ejemplo_P01` a
  `Ejemplo_P05`, los lee con OpenCV, selecciona A y b y ejecuta Jacobi,
  Gauss-Seidel y Doolittle. Es evidencia de un procedimiento de clase,
  no de un destino específico para Proyecto 1.
- `Paso01_CrearQR_Codigo.py`: generación básica de los mismos identificadores.
- `QR_CON_FUNCIONES/PROBLEMAS DE PRACTICAS.docx`: diez problemas de clase,
  con balances y advertencias sobre calibraciones académicas; no contiene
  el Problema 11 de esta entrega.
- `PYTHON/LM35_PrecisionExactitud_01.py`: ejemplo de PySerial, estadística
  y Matplotlib para temperatura. No se reutilizan sus muestras como agua.
- `Python projects/estudiofor/Graph/pitGraph1.py`: ejemplo Matplotlib con
  backend Qt. Aquí se usa Agg para guardar PNG sin escritorio.
- Se localizaron 15 sketches; el de `16septiembre2026/POTENCIOMETRO` se revisó
  como referencia de `analogRead`, 0..1023 y Serial a 9600. Los demás son
  ejemplos de LM35, LCD, LDR, PIR, servo, DHT22, ultrasónico y LED; ninguno
  contiene adquisición Water Level de tres compartimentos.
- Los tres PDF están en `Python projects/Sofiaproject`: se leyeron sus
  portadas y primeras páginas con `pdftotext`. Corresponden a una guía de
  código y a laboratorio/informe de inventario de Estructuras de Datos I.
  No constituyen requisitos de Métodos Numéricos; no se modificaron. El ZIP
  `Sofiaproject.zip` se inventarió sin extraer ni ejecutar su código.
- No se encontraron fotografías independientes de un circuito Water Level,
  datos experimentales ni calibración del tanque. Los medios de Office son
  recursos embebidos de los documentos, no evidencia del montaje del equipo.

## Requisitos confirmados

| Requisito | Fuente | Implementación / estado |
|---|---|---|
| Variables, unidades, conversión, balances, A y b justificados | A: orientaciones y problema 11; B: indicaciones y problema 11 | MODELO.md; unidades físicas pendientes |
| A y b suministrados; solución 5.769231, 8.846154, 8.461538 | B: problema 11 y soluciones de referencia | metodos.py; comparación independiente NumPy |
| Dominancia diagonal | A y B: orientaciones | Documentada y verificada en resumen.json |
| Inicio cero, tol 0.001 | A: orientaciones; B: indicaciones | Valores predeterminados configurables |
| Máximo 100, salvo otra condición docente | A: orientaciones | Predeterminado 100 |
| Norma infinito del cambio estrictamente menor que tol | E y código metodos.py / Spool | Parada implementada sin redondear |
| Jacobi y Gauss-Seidel, fórmulas y tablas | A: problema 11 | CSV completos, incluyendo k=0 |
| Gauss-Jordan y comparación de residuos | B: problema 11 | Operaciones de filas, matriz reducida y CSV |
| Verificación, convergencia, gráfica y conclusión física | A y B | Cuatro PNG y MODELO.md |
| Arduino, recepción Python y gráfica de sensores | B: entregables | Sketch compilado; receptor y gráfica preparados; falta circuito |
| Foto del montaje y límites de calibración | B: entregables | Pendiente de montaje; protocolo documentado |
| QR | Encargo del usuario; ejemplo de clase | Generador/lector preparados; contenido final pendiente |
| Tests, error relativo y comparación de los tres métodos | Encargo del usuario | Tests automáticos y CSV; distinguir de exigencias textuales del profesor |

## Diferencias, versiones y rúbricas

A tiene metadato `modified=2026-10-07T13:04:14Z`; C tiene
`modified=2026-10-07T23:18:00Z`. B conserva fechas de plantilla de 2013;
no permiten fechar su contenido ni establecer que sea anterior a A. E y F
fueron modificadas el 5 de octubre de 2026. Los nombres de carpetas y fechas
de copia no prueban qué versión asignó el profesor.

No se encontró una instrucción que reemplace A o B para esta entrega. Por eso
se conserva la unión solicitada: Jacobi, Gauss-Seidel y Gauss-Jordan. El valor
0.0001 pertenece a ejemplos E/F; 0.001 aparece explícitamente en ambas guías
PROYECTO y se prioriza. El código QR de clase usa máximo 1000 por defecto;
la guía A especifica 100 y prevalece para Proyecto 1.

C presenta una **tabla de evaluación sugerida**: modelo/variables 20 %,
matriz aumentada 15 %, eliminación de Gauss 25 %, Gauss-Jordan 25 % y
residuo/interpretación 15 %. D tiene otra rúbrica: planteamiento 20 %,
A/b 20 %, Jacobi 15 %, Gauss-Seidel 15 %, Doolittle 15 %, verificación y
presentación 15 %. No hay evidencia suficiente para llamar a alguna la
rúbrica definitiva de Proyecto 1. La tabla de control de A sí incluye
Jacobi, Gauss-Seidel y gráfica/residuo.

Por tanto, confirmar con el profesor si C se aplica a esta entrega (en ese
caso habría que añadir eliminación de Gauss con sustitución regresiva), si
se pide Doolittle y cuál rúbrica se evalúa. Mientras tanto se implementan los
tres métodos autorizados y prioritarios. El formato de cuatro decimales de C
puede usarse al redactar una entrega basada en ese banco, conservando precisión
completa en CSV y cálculos; no se toma como regla global demostrada.

Aunque C sugiere reemplazar b con datos calibrados, esto requiere coherencia
física: en el balance estacionario aquí expuesto b representa caudales fuente,
no las alturas h medidas. No se realiza esa sustitución automáticamente.

## Decisiones pendientes

Contenido y función exacta del QR; rúbrica definitiva y métodos adicionales;
fecha y formato final de entrega; dimensiones/unidades del tanque; conexión
hidráulica real; puntos de calibración; mediciones y foto. Ninguno de esos
datos se ha inventado.
