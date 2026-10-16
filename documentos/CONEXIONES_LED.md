# Asignación de los tres LED RGB

El equipo indicó tres LED RGB de cátodo común y resistencias «220».
Las [fotografías incorporadas](evidencias/LEEME.md) muestran puntos
luminosos. Esa observación no verifica qué canal RGB
corresponde a cada pin ni la respuesta a los niveles de agua.
La política vigente es ADC 0–49 verde, 50–149 azul, 150–299 morado y
300–1023 rojo; sustituye los colores anteriores y no representa alturas.
Falta confirmar la unidad de las resistencias y que haya una por canal
de color. El usuario confirmó que los
grupos de pines actuales son D2/D3/D4, D5/D6/D7 y D8/D9/D10; falta comprobar
visualmente la correspondencia de cada cable con su color.

Pines y colores confirmados por el usuario:

| LED | Rojo (R) | Verde (G) | Azul (B) |
|---|---:|---:|---:|
| 1 | D2 | D3 | D4 |
| 2 | D7 | D6 | D5 |
| 3 | D10 | D9 | D8 |

El usuario confirmó las ternas actuales **D2/D3/D4**, **D5/D6/D7** y
**D8/D9/D10**.
Se conserva el orden de colores indicado antes: LED 1 R/G/B, LED 2 B/G/R,
LED 3 B/G/R. En la segunda terna, D5 es azul, D6 verde y D7 rojo.
La tabla del firmware usa el orden R/G/B para cada LED.

`PINES_LED` contiene esos nueve pines. Al arrancar se configuran como salidas
en LOW, que corresponde a apagado para los RGB de cátodo común indicados.
Los colores permanecen apagados por defecto (`NIVEL_AGUA_LED=0`) hasta
comprobar la seguridad eléctrica. La variante `NIVEL_AGUA_LED=1` implementa
los nuevos intervalos independientes; está compilada, pero no cargada.
El firmware comprueba que los nueve pines estén en D2..D10, completos, distintos
entre sí y no ocupen A0/A2/A3 (sensores) ni SDA/A4 o SCL/A5 (LCD). Una
configuración inválida mantiene los LED apagados. Esta comprobación se probó
con los pines comunicados, además de casos controlados de pines compartidos,
faltantes y ocupados por otros componentes.

## Qué falta responder

1. ¿La correspondencia de colores es R/G/B en D2/D3/D4 y B/G/R en las otras
   dos ternas, como se indicó antes?
2. ¿Cada canal de color tiene su propia resistencia de 220 Ω?
3. ¿Qué corriente circula por cada canal encendido y cuál es la hoja de datos
   del RGB utilizado? Falta comprobar también el cátodo común.

## Revisión eléctrica antes de habilitar

Arduino especifica **8 mA por GPIO** para UNO R4 WiFi; no aplicar los límites
de corriente de UNO R3. Fuente: [datasheet oficial, apartado Pin Current](https://docs.arduino.cc/resources/datasheets/ABX00087-datasheet.pdf).

Se necesitan nueve resistencias independientes, una en serie con cada canal
R/G/B. Una resistencia compartida en el cátodo no limita cada canal de forma
independiente al mezclar morado (R+B). La documentación solo dice «220»;
no prueba ni 220 Ω ni nueve resistencias instaladas.

Cálculo orientativo, **no medición del circuito**: con GPIO de 5 V, caída
directa de LED de 2 V y resistencia nominal de 220 Ω, I≈(5−2)/220=13,6 mA,
superior a 8 mA. Esa caída es un escenario, no un dato confirmado del RGB.
Para dimensionar: R≥(V_GPIO_max−Vf_min)/I_objetivo, contemplando tolerancias.
Como referencia conservadora, 1 kΩ ±5 % limita a menos de 5,8 mA incluso
en el escenario de cálculo de 5,5 V y Vf=0; la corriente real y el brillo
dependen del LED. Confirmar modelo, caída directa, corriente real y límites
agregados del RA4M1 antes de habilitar. Si se necesita más corriente, requiere
etapa de manejo externa diseñada para ello, no elevar la corriente del GPIO.

No se inspeccionaron ni cambiaron resistencias ni conexiones en esta tarea.
No se recomienda activar la variante con LED hasta completar esa revisión.

## Comprobación física posterior

1. Con el circuito sin alimentación, identificar resistencias por canal,
   cátodo común y correspondencia real con la tabla R/G/B.
2. Tras verificar corriente y recibir autorización de carga, usar la variante
   compilada con `NIVEL_AGUA_LED=1`.
3. Comparar ADC del monitor con el color del LED de ese sensor. Cambiar solo
   un sensor cada vez y comprobar independencia, manteniendo los otros dos.
4. Verificar verde, azul, morado y rojo. Los datos existentes no cubren azul;
   no declararlo probado físicamente a partir de las pruebas de software.
5. Vigilar las transiciones en 49/50, 149/150 y 299/300 y comprobar que LCD y
   recepción serial siguen operando. No se garantiza alcanzar cada frontera
   con agua; una prueba física con estímulo controlado requeriría acordarla.

## Parpadeo e histéresis

La regla solicitada es instantánea: no contiene histéresis. En el ensayo de
40 mm, 19 muestras están en morado y una alcanza 300 (rojo), con dos cambios
de color previstos dentro de la serie. Eso demuestra riesgo de conmutación
cerca de 300, no parpadeo físico observado. Como etapa posterior se puede
acordar histéresis por sensor o persistencia durante varias muestras; ambas
introducen estado y cambian las fronteras o el tiempo de reacción. No se
introducen márgenes arbitrarios que alteren los intervalos pedidos.
