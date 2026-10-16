# Resultados comprobados y alcance pendiente de la entrega

La adquisición Arduino–Python y la actualización de la LCD funcionan. Se
obtuvieron datos exploratorios reales del sensor 1 a profundidades comunicadas
por el usuario, pero la conversión ADC–altura no superó las comprobaciones
realizadas. Los sensores 2 y 3 todavía no tienen calibración propia.

**Auditoría posterior de los originales:** el resumen comprende 140 filas de
siete ensayos, cada una con ADC1, ADC2 y ADC3: **140 lecturas por sensor y
420 lecturas ADC en total**. Solo ADC1 tiene altura comunicada. Los diez CSV
principales de la sesión contienen 181 filas; 41 pertenecen a tres intentos
excluidos. Además existen 20 filas de preparación, separadas del resumen.
Véanse [el análisis completo y sus gráficas](ANALISIS_ADC_Y_RGB_2026-10-16.md).

Se detuvieron los ensayos físicos a petición del usuario por cansancio y
proximidad de la entrega («el sábado a las 8»). Este resumen permite aprovechar
la evidencia existente; no equivale a declarar terminado el proyecto completo.

## Evidencia disponible

- Firmware principal UNO R4 WiFi cargado correctamente; A0/A2/A3,
  resolución de 10 bits, USB a 115200, periodo de 500 ms y LCD I²C 0x27.
- Captura posterior a carga: 30 muestras válidas sin líneas inválidas,
  intervalos de 500 ms. El usuario confirmó que la LCD actualiza.
- Capturador Python corregido para no confundir un timeout PySerial con EOF.
  Prueba de regresión observada fallar antes y pasar después de la corrección.
  La suite de esa corrección tuvo 40 casos, 39 aprobados y 1 omitido por QR.
  Con la lógica RGB y el analizador nuevos: 47 casos, 46 aprobados y 1 omitido.
- Métodos académicos y sus pruebas conservados. El modelo, sus tablas y
  gráficas están documentados en [MODELO.md](MODELO.md) y el README.
  Las soluciones académicas no se presentan como alturas medidas del montaje.

## Resultados exploratorios del sensor 1

Altura: longitud vertical sumergida desde la punta inferior hasta la
superficie del agua. La condición seca se registra aparte como inmersión cero.
Las alturas fueron comunicadas por el usuario; su incertidumbre no se midió.
Cada fila resume 20 muestras reales, conservadas sin filtrado ni eliminación
de valores sospechosos. La desviación es muestral (divisor n−1).

| Condición | Inmersión comunicada (mm) | Media ADC | Desviación ADC | Mín.–máx. ADC |
|---|---:|---:|---:|---:|
| Seco | 0 | 7,00 | 0,00 | 7–7 |
| Serie inicial | 10 | 232,65 | 1,04 | 231–235 |
| Serie inicial | 20 | 266,20 | 2,46 | 260–271 |
| Serie inicial | 30 | 279,50 | 0,89 | 278–282 |
| Serie inicial | 40 | 298,10 | 0,91 | 297–300 |
| Comprobación al reducir inmersión | 25 | 283,40 | 0,88 | 282–285 |
| Repetición tras revisar referencia | 25 | 246,80 | 11,40 | 228–261 |

Las medias iniciales aumentan con la profundidad comunicada. Sin embargo,
las dos comprobaciones a 25 mm difieren considerablemente. La segunda muestra
además una tendencia temporal. La dispersión entre condiciones y la incertidumbre
de colocación no se corrigen simplemente promediando más muestras.

La interpolación lineal por tramos, usando únicamente los nodos iniciales,
estimó 32,10 mm en la primera comprobación de 25 mm y 14,22 mm a partir del
ADC medio de la segunda: errores de +7,10 mm y −10,78 mm. La segunda serie
no demuestra una condición estacionaria, por lo que ese error es diagnóstico,
no una caracterización de exactitud estática. Los puntos de comprobación se
mantuvieron fuera del ajuste.

El usuario informó posteriormente que el sensor se movía lateralmente y
verticalmente. No se cuantificó el desplazamiento. Esto impide asegurar que
las profundidades se mantuvieron constantes; no permite atribuir toda la
variación al sensor, a la colocación ni a histéresis. Una desviación pequeña
dentro de un ensayo tampoco garantiza exactitud de la profundidad.

## Conclusión que puede utilizarse en la presentación

> Se implementó y verificó la adquisición de tres canales ADC con Arduino
> UNO R4 WiFi, visualización LCD y registro CSV mediante Python. Se realizó
> una caracterización exploratoria del primer sensor a varias profundidades.
> La comprobación independiente detectó diferencias entre la altura medida
> y la estimada. Durante el ensayo no se aseguró una sujeción que mantuviera
> constante la inmersión; por ello, los datos se conservan como resultados
> preliminares y no se declara validada una conversión a centímetros.
> Las ecuaciones de Jacobi, Gauss-Seidel y Gauss-Jordan se verifican por
> separado sobre el sistema académico suministrado.

## Requisitos aún no satisfechos

La guía inspeccionada sí contempla conversión calibrada e interpretación
física: presentar este resultado parcial no sustituye esos requisitos.
Faltan validar la calibración del sensor 1, medir independientemente los
sensores 2 y 3 y documentar geometría y correspondencia del modelo físico.
No se reutilizará la curva de S1 para los otros sensores.

En una solicitud posterior se autorizó preparar los nuevos rangos ADC de LED
sin completar la calibración. Esa lógica está implementada, probada y compilada,
pero las salidas siguen deshabilitadas por defecto y no se cargó el nuevo
firmware. ThingsBoard sigue siendo una propuesta. El contenido final del QR
y los requisitos exactos de formato deben comprobarse con el encargo docente;
no se presupone que formen parte de esta sesión de calibración.

## Archivos y conservación

- [Registro de USB y carga](DIAGNOSTICO_SERIAL_2026-10-16.md).
- [Bitácora de calibración y defecto corregido](CALIBRACION_SESION_2026-10-16.md).
- [Resumen exacto de siete ensayos](../datos/calibracion/sesion_2026-10-16_01/resumen_preliminar_sensor1_01.csv):
  140 filas con tres canales, identificadores, estadísticas de ADC1, rutas y
  SHA-256 comprobados. La auditoría nueva amplía las estadísticas a ADC2 y ADC3.
- [Índice de sesión](../datos/calibracion/sesion_2026-10-16_01/sesion.json):
  incluye también intentos descartados y motivos de exclusión.
- CSV originales en `datos/mediciones/`; no se sobrescribieron. Varios están
  excluidos de Git por la configuración existente: una entrega debe incluir
  explícitamente los CSV necesarios, además del código y los metadatos.

El resumen estadístico se puede reproducir leyendo cada `csv_origen` del
resumen y calculando `statistics.mean`, `statistics.stdev`, `min` y `max`
sobre `adc1`. Cada SHA-256 identifica el original utilizado. Las predicciones
por muestra y los nodos originales están en los JSON de resultados de validación.
