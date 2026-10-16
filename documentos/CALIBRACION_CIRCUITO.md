# Calibración pendiente — tres Water Level

**Actualización 16 octubre:** existen datos exploratorios de S1 con profundidad
variable, sin calibración validada. La lógica RGB solicitada posteriormente
usa intervalos ADC provisionales independientes (verde/azul/morado/rojo) y
`NIVEL_AGUA_LED=0` por defecto hasta revisar seguridad eléctrica. El apartado
histórico de LED al final de este protocolo ya no describe el código vigente.
Detalles: [análisis y cambios](ANALISIS_ADC_Y_RGB_2026-10-16.md).

El circuito usa sensor 1 en A0, sensor 2 en A2 y sensor 3 en A3. LCD en
0x27 sobre SDA/A4 y SCL/A5. Los ADC se conservan siempre sin transformar.
No hay todavía suficientes pares ADC-altura documentados ni umbrales físicos
confirmados. Las pruebas físicas y las lecturas ADC diferentes comunicadas
por el equipo demuestran adquisición, no una calibración completa.

**Para el equipo:** los números D2, D3, D4, etc. identifican cables de los LED.
La calibración consiste en observar qué número ADC entrega cada Water Level
cuando está seco y cuando el agua alcanza alturas conocidas medidas con una
regla. Se hace por separado para los sensores 1, 2 y 3. Esas mediciones
permiten elegir las fronteras entre vacío, bajo, medio y alto. La altura no
puede deducirse de los pines ni de la resolución 0..1023 por sí sola.

La captura inicial con ADC de 5 a 16 no tiene altura ni estado de agua
documentados. No se puede llamarla «vacío» ni usarla como calibración.
Una captura posterior con ADC cercano a 994 en los tres sensores tampoco
tiene estado de agua documentado y no se usa para fijar límites.

## Medir la respuesta de cada sensor

1. Confirmar que la LCD muestra las tres lecturas. Variar el agua de un
   sensor por vez y comprobar que cambia el canal correspondiente.
2. Elegir una unidad y una referencia de altura comunes. Medir con regla
   alturas conocidas; no deducirlas a partir del máximo ADC 1023.
3. Mantener orientación, montaje, agua y alimentación consistentes. Para
   cada sensor, registrar varias lecturas repetidas en cada altura conocida.
   Registrar también la condición seca por separado y el estado del montaje;
   anotar el identificador del CSV de origen de cada conjunto de repeticiones.
4. Repetir con varias alturas que cubran el intervalo que se quiere medir.
   Usar un CSV de captura distinto por condición, anotando a qué altura y
   sensor corresponde. No mezclar condiciones sin anotarlas.
5. Revisar dispersión y monotonicidad: el código actual de interpolación
   requiere ADC y altura crecientes. Si no ocurre, revisar los datos y el
   montaje antes de aplicar ese modelo.

Se entrega [plantilla_puntos.csv](../datos/calibracion/plantilla_puntos.csv)
con campos vacíos: copiar filas para cada altura y sensor. Es una hoja de
anotación; Python no la importa directamente como calibración.
No se completa con datos simulados.

Captura por condición, usando un nombre nuevo cada vez:

```bash
.venv/bin/python -m python.main capturar --puerto /dev/ttyACM0 --baudios 115200 --muestras 20 --duracion 15 --salida datos/mediciones/calibracion_condicion_01.csv
```

Al terminar una condición, anotar en la plantilla altura real, unidad,
sensor, lecturas repetidas, nombre del CSV y condición del montaje. El usuario debe realizar la
medición física; el programa no puede determinar por sí solo la altura.
Para evitar atribuciones erróneas, no reutilizar como puntos de calibración
las capturas históricas que carecen de altura y condición documentadas.

## Preparar la conversión a altura

Con las mediciones revisadas, crear un JSON con `unidad` y `sensores`.
`sensores` debe contener `adc1`, `adc2` y `adc3`, cada uno con al menos dos
pares numéricos `[ADC,altura]` medidos y ordenados estrictamente por ADC.
La altura también debe aumentar. No se proporciona un JSON numérico ficticio.
`python/calibracion.py` interpola linealmente entre puntos y rechaza lecturas
fuera del rango calibrado. No sobrescribe el CSV ADC original.

```bash
.venv/bin/python -m python.main graficar --csv datos/mediciones/ensayo_r4_02.csv --calibracion datos/calibracion_real.json --salida graficas/altura_ensayo_r4_02.png
```

## Establecer los estados de los LED

En la versión vigente del firmware (`arduino/NivelAguaR4/ColoresNivel.h`),
`colorParaAdc(adc)` clasifica cada canal de forma independiente en cuentas ADC
provisionales (sustituyendo el arreglo inicial `LIMITES_ADC_LED` y el color amarillo):

- **0–49**: Verde (canal G)
- **50–149**: Azul (canal B)
- **150–299**: Morado (canales R+B)
- **300–1023**: Rojo (canal R)
- **Fuera de 0..1023**: Apagado

Los nueve pines en `PINES_LED` tienen la asignación: LED 1 R2/G3/B4, LED 2
R7/G6/B5 y LED 3 R10/G9/B8. Por defecto `NIVEL_AGUA_LED=0` mantiene las nueve
salidas en `OUTPUT` con nivel `LOW` (0 V activo para cátodo común, distinto de
alta impedancia). Antes de compilar con `-DNIVEL_AGUA_LED=1` y cargar a la placa,
se debe verificar físicamente el cátodo común, el cableado de cada color y una
resistencia adecuada por canal que respete el límite de 8 mA por GPIO del UNO R4 WiFi.

Queda pendiente probar cambios de color reales en el hardware, incluido el
comportamiento cerca de las fronteras (49/50, 149/150, 299/300); la política
actual no incorpora histéresis.

