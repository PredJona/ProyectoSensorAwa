# Asignación de los tres LED RGB

El equipo indicó tres LED RGB de cátodo común y resistencias «220».
También acordó los colores: vacío morado, bajo verde, medio amarillo y alto
rojo. Falta confirmar la unidad de las resistencias, que haya una por canal
de color y los límites medidos de nivel. El usuario acaba de confirmar que los
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
Los colores permanecen apagados porque los límites ADC de cada sensor siguen
sin medir y `LIMITES_ADC_LED` conserva -1.
El firmware comprueba que los nueve pines estén completos, sean distintos
entre sí y no ocupen A0/A2/A3 (sensores) ni SDA/A4 o SCL/A5 (LCD). Una
configuración inválida mantiene los LED apagados. Esta comprobación se probó
con los pines comunicados, además de casos controlados de pines compartidos,
faltantes y ocupados por otros componentes.

## Qué falta responder

1. ¿La correspondencia de colores es R/G/B en D2/D3/D4 y B/G/R en las otras
   dos ternas, como se indicó antes?
2. ¿Cada canal de color tiene su propia resistencia de 220 Ω?
3. ¿Qué lecturas ADC corresponden, por sensor, a agua ausente y a alturas
   conocidas? [Protocolo de calibración](CALIBRACION_CIRCUITO.md).

Los pines no aportan las fronteras entre vacío/bajo/medio/alto. Esas se
obtienen mediante las mediciones de cada sensor. Los ADC observados en las
primeras capturas no tienen altura ni estado de agua documentado y no se usan
como umbrales.
