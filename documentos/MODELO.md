# Modelo, métodos y verificación

## Variables y sensores

| Variable | Compartimento | Canal | Magnitud |
|---|---|---|---|
| h1 | 1 | A0 | Altura del agua respecto de un origen común |
| h2 | 2 | A2 | Altura del agua respecto de ese origen |
| h3 | 3 | A3 | Altura del agua respecto de ese origen |

El sensor mide una respuesta eléctrica que Arduino convierte a cuentas ADC
(enteros 0..1023). No mide directamente centímetros. La función de calibración
de cada canal transforma esas cuentas en alturas o porcentajes. Las alturas
físicas requerirán una unidad común, un cero definido y calibración medida.
En el sistema suministrado no se especifica unidad: los resultados se rotulan
en unidades académicas, nunca como cm o porcentajes reales.

## Continuidad y balance de volumen

Supongamos compartimentos con sección horizontal constante S_i, agua
incompresible, sin evaporación apreciable, y altura uniforme en cada uno.
Entonces V_i=S_i h_i y conservación del volumen da:

```text
S1 dh1/dt = q1 − q12 − q10
S2 dh2/dt = q2 + q12 − q23 − q20
S3 dh3/dt = q3 + q23 − q30
```

q_i es aporte externo, q_ij es caudal firmado entre compartimentos y q_i0
una salida hacia una referencia hidráulica. Se adopta, únicamente como
aproximación didáctica lineal, q12=g12(h1−h2), q23=g23(h2−h3), y
q_i0=k_i(h_i−h0), con conductancias positivas constantes. No hay conexión
directa 1–3. Esta ley supone un régimen de resistencia aproximadamente lineal
o una linealización justificada alrededor de un estado de trabajo. Un orificio
libre puede obedecer una ley no lineal; la relación lineal no es universal.

En régimen estacionario dh_i/dt=0. Tomando h0=0 como referencia:

```text
(k1+g12) h1 − g12 h2                 = q1
−g12 h1 + (k2+g12+g23) h2 − g23 h3 = q2
                 −g23 h2 + (k3+g23) h3 = q3
```

Un conjunto de parámetros **supuestos y normalizados, no experimentales**, que
reproduce los datos del profesor es g12=g23=1, (k1,k2,k3)=(4,3,3) y
(q1,q2,q3)=(20,30,25). Esto produce:

```text
5h1 − h2       = 20
−h1 + 5h2 − h3 = 30
     −h2 + 4h3 = 25

A = [[ 5, −1,  0],    h = [h1, h2, h3]^T,    b = [20,30,25]^T
     [−1,  5, −1],
     [ 0, −1,  4]]
```

Los términos diagonales suman conductancias de intercambio y de salida; los
no diagonales negativos representan el nivel vecino en una diferencia de
alturas. El cero expresa ausencia de acoplamiento directo. b contiene aportes
externos y, si h0 no es cero, términos de frontera k_i h0. En unidades físicas,
A tendría dimensiones de caudal/altura y b de caudal. La guía entrega valores
normalizados sin especificar esa escala; no se asignan unidades SI inventadas.

Las entradas/salidas q_i y k_i son hipótesis para interpretar el sistema
académico, **no componentes confirmados del circuito construido**. Los sensores
observan h_i; no generan A ni b. Para afirmar que este modelo representa el
tanque real habrá que confirmar geometría, conexiones, condiciones de frontera,
caudales y parámetros, o deducir un modelo apropiado al montaje disponible.

## Si el tanque real es cerrado y solo comunica los compartimentos

Sin aportes ni salidas, q_i=q_i0=0. El sistema dinámico es:

```text
S1 dh1/dt = −g12(h1−h2)
S2 dh2/dt =  g12(h1−h2) − g23(h2−h3)
S3 dh3/dt =  g23(h2−h3)
```

Al sumar, d(V1+V2+V3)/dt=0. En equilibrio y con conexiones abiertas
h1=h2=h3. La matriz estacionaria de intercambio tiene filas cuya suma es cero;
es singular sin la restricción del volumen total. Con secciones constantes,
el nivel común es V_total/(S1+S2+S3), respecto del origen elegido.
Por tanto, los tres niveles distintos de la solución académica no representan
el equilibrio de un tanque cerrado comunicado. La demostración numérica y la
observación física deben presentarse con esa limitación explícita.

## Dominancia y métodos iterativos

Las filas satisfacen 5>1, 5>2 y 4>1: A es estrictamente diagonal dominante.
Jacobi y Gauss-Seidel convergen para este sistema desde cualquier vector inicial
finito en aritmética exacta. Se usa h^(0)=(0,0,0) y máximo 100 iteraciones.

Jacobi calcula las tres componentes con el vector anterior:

```text
h1(k+1) = [20 + h2(k)] / 5
h2(k+1) = [30 + h1(k) + h3(k)] / 5
h3(k+1) = [25 + h2(k)] / 4
```

Gauss-Seidel aprovecha inmediatamente las componentes actualizadas:

```text
h1(k+1) = [20 + h2(k)] / 5
h2(k+1) = [30 + h1(k+1) + h3(k)] / 5
h3(k+1) = [25 + h2(k+1)] / 4
```

Los primeros vectores son Jacobi (4,6,6.25) y Gauss-Seidel (4,6.8,7.95).
El índice k=0 se conserva en las tablas, pero no cuenta como una actualización.

Siguiendo la guía A y el código de clase, se detiene con:

```text
e_abs(k) = ||h(k) − h(k−1)||∞ < 0.001
r(k) = A h(k) − b
```

El cambio por componente es |h_i(k)−h_i(k−1)|. Se registra además el cambio
relativo por componente dividido entre |h_i(k)|, cuando h_i(k)≠0, y el cambio
relativo global e_abs/||h(k)||∞ cuando su denominador es distinto de cero.
Estos relativos son cocientes, no porcentajes, y no gobiernan la parada.
No hay cambio definido en k=0; tampoco relativo cuando el denominador es cero.
Se exportan como campos vacíos. Los cálculos conservan precisión flotante.

El residuo mide satisfacción de las ecuaciones; el cambio mide la diferencia
entre iteraciones. Ninguno es automáticamente el error verdadero de la solución.
Aquí sí puede calcularse una diferencia independiente frente a NumPy y frente
a las fracciones exactas. Una parada por cambio no garantiza para cualquier
matriz un residuo menor que tol: ambos se informan por separado.

## Gauss-Jordan

El programa construye [A|b], elige en cada columna el mayor pivote absoluto
disponible debajo de la diagonal, intercambia filas si hace falta, divide la
fila pivote y elimina esa columna de todas las otras filas. Conserva cada
operación y la matriz aumentada resultante en CSV. Es un método directo;
sus operaciones no se cuentan como iteraciones de convergencia.

El umbral de pivote es `pivot_tol * max(abs(A))`, con `pivot_tol=1e-12`;
se controla también la última columna pivote. No se divide entre pivotes nulos
o menores que ese umbral. La verificación final evalúa el residuo escalado por
`||A||∞ ||h||∞ + ||b||∞` con margen de 100 veces el épsilon de máquina.
El pivoteo mejora la robustez, pero no certifica que toda matriz esté bien
condicionada. NumPy se usa solo como referencia independiente, no para realizar
Gauss-Jordan ni los pasos iterativos.

## Solución y comprobación exacta

La matriz reducida es [I|h] con h=(75/13,115/13,110/13). Sustituyendo:

```text
(5·75 − 115)/13        = 260/13 = 20
(−75 + 5·115 − 110)/13 = 390/13 = 30
(−115 + 4·110)/13      = 325/13 = 25
```

Así Ah=b exactamente; en coma flotante queda un residuo de redondeo.
Con los parámetros del profesor la ejecución produce:

| Método | h1 | h2 | h3 | Iteraciones | Cambio final ∞ | Residuo ∞ |
|---|---:|---:|---:|---:|---:|---:|
| Jacobi | 5.769114690 | 8.845967110 | 8.461393363 | 9 | 3.936600e-4 | 6.725025e-4 |
| Gauss-Seidel | 5.769203920 | 8.846141764 | 8.461535441 | 6 | 2.714796e-4 | 1.221658e-4 |
| Gauss-Jordan | 5.769230769 | 8.846153846 | 8.461538462 | No aplica | No aplica | 7.105427e-15 |

Gauss-Seidel requiere menos actualizaciones en este caso porque utiliza los
valores nuevos en el mismo barrido. Esto no demuestra menor tiempo para toda
matriz. Gauss-Jordan da una referencia directa con residuo de redondeo.
La discrepancia máxima frente a NumPy es aproximadamente 1.867362e-4 para
Jacobi y 2.684963e-5 para Gauss-Seidel; ambos están dentro de 0.001 en este caso.
No se interpreta ninguna de estas diferencias como precisión del sensor.

## Gráficas y medición futura

Las figuras de convergencia comparan cambios y residuos en escala logarítmica;
las de niveles muestran las aproximaciones, y las barras comparan soluciones.
La gráfica temporal solo se genera al proporcionar un CSV de adquisición.
Sin calibración presenta cuentas ADC; con calibración presenta la unidad
declarada. El tiempo se obtiene de UTC de recepción para tolerar reinicios o
desbordamiento de millis, con la limitación temporal ya indicada.

Los tests de esa función utilizan datos controlados temporales con origen
`prueba_controlada`; la figura los identifica como no experimentales.
Hay gráficas experimentales de cuentas ADC sin calibrar, obtenidas de capturas
reales. No hay todavía curvas de altura física ni una validación experimental
de la matriz académica A y el vector b para este montaje.
