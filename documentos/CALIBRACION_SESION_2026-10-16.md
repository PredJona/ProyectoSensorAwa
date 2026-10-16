# Sesión de calibración física — 16 octubre 2026

Estado: datos exploratorios del sensor 1 adquiridos en seco y a varias
inmersiones; calibración no validada. Sensores 2 y 3 pendientes de calibración.

**Actualización de cierre parcial:** el usuario informó que no puede mantener
el sensor estable, está cansado y debe entregar el sábado a las 8. Se detienen
los ensayos físicos sin nuevas capturas. Se conserva lo medido como
caracterización exploratoria; la calibración sigue sin validar. Véase
[el resumen para la entrega](RESUMEN_PRELIMINAR_ENTREGA_2026-10-16.md).

El usuario comunicó una longitud de zona sensible del sensor 1 de **4,4 cm
(44 mm)**. La división mínima de la regla sigue pendiente. Esta longitud no
es una altura de inmersión ni un punto de calibración. El usuario confirmó
después el estado seco («ok listo seco»). Se conservarán secos los
componentes y el conector al elegir las alturas húmedas.

## Auditoría y verificación inicial

- `python/comunicacion.py`: captura real a 115200, reconstruye líneas
  fragmentadas, valida cuatro enteros y conserva CSV nuevos mediante modo `x`.
  Mantiene ADC de los tres canales y timestamp UTC. No sustituir este receptor.
- `python/calibracion.py`: valida pares independientes [ADC, altura], exige
  ADC y altura estrictamente crecientes e interpola linealmente sin extrapolar.
  `cargar` exige calibración para los tres sensores. No hay calibración medida
  disponible todavía y no debe construirse un JSON completo con puntos ficticios.
- `python/graficas.py`: representa series ADC o alturas de los tres sensores
  usando la calibración existente. Las curvas ADC-altura y errores de validación
  se prepararán una vez adquiridos los puntos, reutilizando `convertir`.
- `python/main.py`: expone capturar y graficar. No existe asistente automático
  de condiciones ni resumen estadístico por altura. La interacción se realizará
  en esta conversación y los cálculos usarán la biblioteca estándar de Python.
- `datos/calibracion/plantilla_puntos.csv`: plantilla vacía de anotación;
  no es un fichero importable por `calibracion.cargar`.
- Firmware principal: A0/A2/A3, ADC de 10 bits, cuatro enteros a 115200 cada
  500 ms, LCD 0x27 habilitada. No se recompiló ni cargó firmware en esta fase.
- Política LED existente diferente de la propuesta nueva, con límites en -1;
  se deja pendiente hasta terminar la calibración. ThingsBoard también pendiente.

Verificación real: `verificacion_precalibracion_2026-10-16_01.csv`,
10 muestras válidas y 1 línea inválida descartada por el receptor. Se desconoce
el contenido de la línea descartada y no se atribuye una causa sin evidencia.
Los nueve intervalos Arduino fueron 500 ms. ADC observados S1=2, S2=10..11,
S3=2..3. No se conoce la condición física: NO se usan como punto seco.
SHA-256: `6040a706ac52beb8a57f44f83c5d24414f3e0670e080e6451e8b38d48b94dbaa`.

Suite completa: 39 casos en 3.406 s, 38 aprobados, 1 omitido por qrcode/OpenCV
ausentes. Sin cambios a Jacobi, Gauss-Seidel, Gauss-Jordan ni a firmware.

## Procedimiento interactivo

1. Medir la profundidad vertical sumergida desde el extremo inferior del sensor
   hasta la superficie libre del agua, en mm. No equivale automáticamente al
   nivel absoluto de un depósito: haría falta documentar el montaje y su offset.
   Mantener orientación vertical, referencia y agua iguales durante cada serie.
2. Empezar por sensor 1 (A0). Sacar su zona sensible del agua y dejarla seca,
   sin desconectar cables ni mojar componentes/conector. Registrar condición
   seca como referencia de inmersión cero, diferenciándola del primer contacto
   húmedo. No asumir aún que ese punto permitirá interpolar cerca de cero.
3. El usuario confirma estabilidad, condición y unidad antes de cada captura.
   Medirá la longitud utilizable de la zona sensible y la división mínima de
   su regla antes de elegir alturas húmedas. No se presupone longitud del modelo.
4. Capturar 20 muestras por condición con el receptor existente (unos 10 s,
   límite 20 s). Mantener la condición durante toda la captura. Guardar los tres
   canales en el CSV, pero asociar únicamente el sensor ensayado a la altura.
5. Guardar metadatos independientes: sensor/pin, altura medida, unidad, fecha
   UTC, condición y observaciones del usuario, fuente CSV y SHA-256, número
   esperado/recibido de muestras, líneas inválidas, periodos Arduino, media,
   desviación estándar muestral (n-1), mínimo y máximo. Si hay interrupción o
   cambio físico, conservar los datos y marcar el ensayo incompleto o dudoso.
6. Repetir varias alturas húmedas que cubran la zona utilizable y repeticiones
   de condiciones. Elegir valores concretos solo después de medir el sensor.
   Reservar alturas medidas distintas de los nodos para validación independiente.
7. Repetir el procedimiento completo para sensores 2 y 3. Mantener las
   condiciones de los demás sensores documentadas; no asumir igual respuesta.

## Análisis cuando existan mediciones

Revisar las series temporales antes de resumirlas: dispersión, tendencia,
saturación y valores sospechosos; no eliminar muestras automáticamente.
Comparar medias en orden de altura, incluida la separación respecto a su
dispersión. La media de 20 muestras correlacionadas no implica 20 observaciones
independientes ni sustituye repeticiones físicas.

Si ADC y altura no aumentan estrictamente o hay saturación, no forzar el
validador ni ordenar ADC para ocultar el problema. Repetir puntos o restringir
el dominio útil. Revisar si la condición seca y las húmedas requieren dominios
separados. No extrapolar.

Construir una curva por sensor con medias ADC y alturas medidas aceptadas,
usando `python.calibracion.convertir`. Error de validación = altura estimada
menos altura de regla; informar sesgo, MAE, RMSE y máximo absoluto en mm.
Los errores cero en nodos interpolados no son validación independiente.
Conservar puntos reservados fuera del ajuste y documentar incertidumbre de
regla, orientación, agua, estabilidad, repetibilidad e histéresis ascenso/descenso.

Exportar curvas, puntos, estadísticas, predicciones y errores en archivos nuevos
reproducibles junto con los CSV originales. No avanzar a LED ni ThingsBoard
hasta revisar y validar los tres sensores.

## Sensor 1 seco: adquisición y corrección demostrada

El primer intento `s1_seco_01` recibió 20 muestras juntas en unos 2 ms:
no se puede asegurar que correspondan a la condición recién confirmada.
Se conserva el CSV y su primer metadato, con una revisión que lo excluye de
calibración. Después de drenar la cola, `s1_seco_02` terminó con una sola
muestra en 0,20 s pese a solicitar 20 s: también se conserva y excluye.

Defecto reproducido: PySerial hereda `io.IOBase`; `registrar` interpretaba el
primer timeout sin bytes como EOF de archivo. Se añadió una prueba con PySerial
y un pseudoterminal Linux que envía dos tramas separadas por timeouts.
Falló antes de la corrección (0 muestras en lugar de 2) y pasó después.
La condición EOF ahora distingue fuentes con atributo `timeout`.
Suite completa: 40 pruebas en 3.510 s, 39 aprobadas y 1 omitida por QR.
No se modificó el firmware ni los métodos numéricos.

El intento `s1_seco_03` conservó 883 bytes de arranque durante un drenado de
2 s y capturó 20 muestras actuales en 9.819 s, cero líneas inválidas.
Los 19 intervalos Arduino fueron 500 ms. Metadatos, estadísticas y SHA-256
se conservan en `datos/calibracion/sesion_2026-10-16_01/s1_seco_03.json`.
Los CSV originales no se sobrescribieron. Las siguientes condiciones deben
drenar el arranque y verificar también el intervalo de recepción UTC para
evitar asociar datos acumulados a una altura nueva.

## Sensor 1 a 10 mm (1 cm)

El usuario respondió «ya» a las instrucciones de colocar S1/A0 vertical con
10 mm sumergidos. Se registró esa confirmación de altura; la resolución de
la regla todavía no fue comunicada. Tras conservar 4488 bytes de arranque,
se recibieron 20 muestras en 9.719 s, cero líneas inválidas y 19 intervalos
Arduino de 500 ms. Intervalo UTC entre primera y última recepción: 9.519 s.

ADC1: promedio 232.65, desviación estándar muestral 1.03999, mínimo 231,
máximo 235. La media aumenta respecto a los 7 ADC de la referencia seca.
Hay un leve aumento dentro del ensayo (termina en 235); con una sola serie
no puede atribuirse a absorción, movimiento o deriva. Se conserva toda la
serie sin filtrar. Hacen falta más alturas y repeticiones físicas antes de
validar monotonicidad y estimar errores independientes de interpolación.

CSV: `datos/mediciones/calibracion_sesion_2026-10-16_01_s1_10mm_01.csv`.
Estadísticas, confirmación de condición y SHA-256:
`datos/calibracion/sesion_2026-10-16_01/s1_10mm_01.json`.
Los otros canales también se conservaron, pero no se asignan a alturas.
Siguiente condición propuesta: S1 a 20 mm, manteniendo orientación y agua;
esperar 15 segundos antes de confirmar estabilidad y capturar.

## Sensor 1 a 20 mm (2 cm)

El usuario confirmó «ya» después de las instrucciones de colocar S1 a 2 cm.
El primer intento `s1_20mm_01` tuvo 20 muestras y cero inválidas, pero un salto
de 40500 ms entre las dos primeras marcas Arduino; quedó marcado dudoso y
excluido de la curva en el índice de sesión. Se preservan CSV y metadatos,
sin eliminar la primera fila ni atribuir una causa definitiva al salto.

Se pidió mantener el sensor a 2 cm y se repitió: drenado de 2 s, cuatro
tramas de preparación guardadas aparte y después 20 muestras principales.
El intento `s1_20mm_02` recibió cero líneas inválidas, los 19 intervalos
Arduino de 500 ms y 9.521 s entre primera y última recepción UTC.

ADC1: media 266.20, desviación estándar muestral 2.46235, mínimo 260,
máximo 271. Es mayor que a 10 mm (232.65), con más dispersión. Se conservó
la secuencia completa, incluida la caída transitoria hasta 260; su causa no
está demostrada. La condición sigue pendiente de validación y repetición
física al finalizar la serie, antes de aceptar el modelo.

CSV: `datos/mediciones/calibracion_sesion_2026-10-16_01_s1_20mm_02.csv`.
Metadatos: `datos/calibracion/sesion_2026-10-16_01/s1_20mm_02.json`.
Siguiente condición propuesta: S1 a 30 mm, esperar 15 s y confirmar.
Para próximas capturas se conservarán también cuatro tramas de preparación
antes de las 20 principales y se revisará la continuidad temporal.

## Sensor 1 a 30 mm (3 cm)

El usuario respondió «ya» tras las instrucciones de colocar S1 a 3 cm y
esperar 15 s. Se drenó el arranque durante 2 s (1958 bytes conservados) y se
guardaron cuatro muestras de preparación antes del ensayo principal.

Se capturaron 20 muestras válidas, cero inválidas, en 10.021 s. Los 19
intervalos Arduino fueron 500 ms; entre primera y última recepción UTC
transcurrieron 9.520 s. ADC1: media 279.50, desviación estándar muestral
0.88852, mínimo 278, máximo 282. Se conserva el valor 282 y toda la serie
sin filtrar ni eliminar observaciones.

Las medias disponibles son crecientes: seco 7.00, 10 mm 232.65,
20 mm 266.20 y 30 mm 279.50. Eso aún no valida el modelo: faltan el tramo
superior, repeticiones y alturas de comprobación independientes.

CSV: `datos/mediciones/calibracion_sesion_2026-10-16_01_s1_30mm_01.csv`.
Metadatos: `datos/calibracion/sesion_2026-10-16_01/s1_30mm_01.json`.
Siguiente condición propuesta: S1 a 40 mm, únicamente si el agua permanece
dentro de la zona sensible medida y por debajo de componentes/conector;
esperar 15 s antes de confirmar. No se presupone margen seguro si el montaje
real no permite esa profundidad sin mojar la electrónica.

## Sensor 1 a 40 mm (4 cm)

El usuario confirmó «ya» tras las instrucciones de inmersión de 4 cm y de
mantener componentes y conector secos. Tras drenar el arranque 2 s (4571 bytes
conservados) y guardar cuatro tramas de preparación, se capturaron 20 muestras
válidas, cero inválidas. Captura de 10.020 s, 9.519 s entre primera y última
recepción UTC y 19 intervalos Arduino de 500 ms.

ADC1: media 298.10, desviación estándar muestral 0.91191, mínimo 297,
máximo 300. Se conserva la ligera variación temporal y toda la serie sin
filtrar. Las medias de la serie creciente son:

| Inmersión comunicada | Media ADC1 |
|---|---:|
| Seco, 0 mm | 7.00 |
| 10 mm | 232.65 |
| 20 mm | 266.20 |
| 30 mm | 279.50 |
| 40 mm | 298.10 |

CSV: `datos/mediciones/calibracion_sesion_2026-10-16_01_s1_40mm_01.csv`.
Metadatos: `datos/calibracion/sesion_2026-10-16_01/s1_40mm_01.json`.
Medias estrictamente crecientes; no se presupone linealidad global ni
validación del tramo seco-húmedo. Resolución de regla todavía pendiente.

Antes de capturar, se reserva la siguiente condición de 25 mm (2,5 cm) como
validación independiente: no se usará para construir los nodos iniciales.
Se llegará desde 40 mm reduciendo la inmersión. Su error reflejará también
posible efecto de dirección/histéresis y no debe atribuirse exclusivamente
a la interpolación. Se solicitará esperar 15 s y confirmar la altura.

## Sensor 1: validación independiente a 25 mm descendiendo

El usuario respondió «ya» a las instrucciones de bajar la inmersión de
40 a 25 mm. Tras drenado de 2 s y cuatro tramas de preparación, se capturaron
20 muestras válidas, cero inválidas, en 10.021 s. Los 19 intervalos Arduino
fueron 500 ms; intervalo UTC primera-última de 9.519 s.

ADC1: media 283.40, desviación estándar muestral 0.88258, mínimo 282,
máximo 285. Este punto quedó reservado fuera de los nodos del ajuste.
Se usó `python.calibracion.convertir` con nodos iniciales de 0, 10, 20,
30 y 40 mm, sin modificar esa función ni extrapolar. El nodo seco es
provisional y no afecta al tramo utilizado en esta comprobación.

Resultado: altura desde ADC medio 32.0968 mm frente a 25 mm comunicados;
sesgo +7.0968 mm, MAE 7.0968 mm, RMSE 7.1118 mm, máximo absoluto 7.9570 mm.
Son errores de un único ensayo de 20 lecturas correlacionadas; no describen
exactitud global ni incertidumbre de la regla, cuya resolución sigue pendiente.

La media ADC a 25 mm descendiendo supera la de 30 mm ascendiendo (279.50).
Se observa inconsistencia entre series: la curva inicial no queda validada
para uso en mediciones calibradas. No se atribuye la causa a histéresis,
humedad, deriva o error de colocación sin nuevas comprobaciones; tampoco se
incorpora el punto reservado al ajuste para ocultar el error.

CSV y metadatos conservados con identificador `s1_25mm_validacion_01`.
Resultados reproducibles con nodos y predicciones por lectura:
`datos/calibracion/sesion_2026-10-16_01/s1_validacion_25mm_01_resultados.json`.
Próximo paso: solicitar verificación física de la referencia de 25 mm y una
repetición con mayor espera en esa misma altura antes de avanzar de sensor.

## Sensor 1: repetición a 25 mm tras revisar la referencia

El usuario respondió «ya» a la solicitud de revisar la referencia y esperar
60 s. Se interpretó como listo para capturar; el agente no verificó físicamente
el tiempo de espera ni recibió respuesta sobre la división mínima de la regla.

Ensayo `s1_25mm_validacion_02`: 20 muestras válidas, cero inválidas, 19
intervalos Arduino de 500 ms, 9.521 s entre primera y última recepción.
Media ADC1 246.80, desviación estándar muestral 11.39991, rango 228..261.
Secuencia completa:
`228,237,231,229,229,233,244,252,251,251,251,249,249,252,255,257,260,261,258,259`.
Se observa una tendencia ascendente, sin meseta estable durante todo el ensayo.

Con los nodos originales, el ADC medio produciría 14.2176 mm frente a los
25 mm comunicados (error -10.7824 mm). Calculando por muestra: sesgo
-10.6099 mm, MAE 10.6099 mm, RMSE 11.0377 mm, máximo absoluto 15.2061 mm.
Estas cifras son diagnósticas: la serie no representa una condición estacionaria
demostrada, por lo que no se usa para afirmar exactitud estática del sensor.
No se eliminan las muestras iniciales para fabricar una meseta.

Los datos originales, estadísticas y predicciones se preservan. La calibración
de S1 sigue sin habilitarse. Antes de otra captura, se requiere aclarar si el
sensor se sostiene con la mano o queda sujeto verticalmente, y estabilizar
su posición respecto a una superficie de agua quieta. No se demuestra aún
si la variación se debe a movimiento, respuesta transitoria u otra causa.
No se avanza a sensores 2/3, LED ni ThingsBoard durante esta comprobación.
