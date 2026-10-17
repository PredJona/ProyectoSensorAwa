# Modelo, métodos y verificación

## Dos problemas independientes

La implementación distingue el **11.1**, continuidad de tres vasos cerrados
discretizada con Euler implícito, del **11.2**, sistema estacionario de validación
del profesor. Los datos de ambos ejemplos son hipotéticos y normalizados.
Arduino, LCD, captura CSV y ThingsBoard son la parte experimental compartida;
sus cuentas ADC no alimentan ninguno de estos sistemas académicos.

Esta adaptación fue cotejada con las seis páginas de
[`Problema11_Planteamiento_v4.pdf`](Problema11_Planteamiento_v4.pdf): continuidad,
Euler implícito y ejemplo de 11.1 en páginas 2–4; balances estacionarios, matriz,
vector y comparación de residuos de 11.2 en páginas 4–6. Las matrices y los
métodos coinciden. El PDF deja las tablas y resultados numéricos para apartados
posteriores; los conteos de iteraciones aquí indicados proceden de las ejecuciones
locales con el criterio y parámetros documentados.

## Problema 11.1: un paso temporal de continuidad

Para tres vasos de igual sección constante S, conductancia k común y sin
entradas ni descargas externas, se supone la ley lineal didáctica:

```text
S dh1/dt = -k(h1-h2)
S dh2/dt =  k(h1-h2) - k(h2-h3)
S dh3/dt =  k(h2-h3)
```

Euler implícito evalúa los intercambios en el nuevo instante n+1:

```text
alpha = k Delta_t / S > 0
A(alpha) h^(n+1) = b,        b = h^n

A(alpha) = [[1+alpha, -alpha,          0],
            [-alpha,  1+2alpha,  -alpha],
            [0,       -alpha,   1+alpha]]
```

Es **un paso temporal**, no el equilibrio final de los vasos. Las iteraciones
de Jacobi/Seidel resuelven ese paso; no representan instantes físicos sucesivos.
`--niveles-anteriores` define b, mientras `--x0` es únicamente la aproximación
inicial del solucionador. Se toman niveles no negativos referidos al fondo.
No se han medido S, k ni Delta_t: solo se configura su combinación alpha.

Con alpha=1 y b=(3,2,1), A=[[2,-1,0],[-1,3,-1],[0,-1,2]] y la solución exacta
es (2.5,2,1.5). Por sustitución, A h=(3,2,1). La suma pasa de 6 a 6;
con igual sección S esto conserva el volumen S·sum(h). Cada columna de A suma
1, de modo que para cualquier aproximación el defecto sum(h)-sum(b) equivale
a sum(Ah-b). No se fuerza la suma de los iterados mediante correcciones.

Las filas tienen margen de dominancia estricta igual a 1 para todo alpha>0.
La implementación rechaza valores no positivos, no finitos o tan grandes que
la aritmética flotante pierda ese margen. Los niveles deben ser tres valores
finitos no negativos; no se impone esa restricción física a `--x0`.

Con x0=(0,0,0), tol=0.001 y parada por cambio absoluto infinito:

| Método | Primer vector | Iteraciones | Solución aproximada | Residuo infinito | Suma aproximada |
|---|---|---:|---|---:|---:|
| Jacobi | (1.5, 2/3, 0.5) | 14 | (2.499085505, 1.999085505, 1.499085505) | 9.144947e-4 | 5.997256516 |
| Gauss-Seidel | (1.5, 7/6, 13/12) | 9 | (2.499809480, 1.999872987, 1.499936493) | 2.540263e-4 | 5.999618961 |

La solución exacta conserva la suma exactamente. Las aproximaciones tienen
defectos -0.002743484 y -0.000381039, respectivamente, compatibles con sus
residuos. Una tolerancia de cambio de 0.001 no exige un defecto de suma menor
que 0.001. El resumen JSON informa estas diferencias, sin confundirlas con
incertidumbre de medición ni con pérdida física de agua.

```bash
.venv/bin/python -m python.main resolver --problema 11.1
.venv/bin/python -m python.main resolver --problema 11.1 --alpha 0.5 --niveles-anteriores 4 2 0 --x0 1 1 1 --salida /tmp/awa-11-1-personalizado
```

Las tablas `jacobi.csv`, `gauss_seidel.csv`, `comparacion.csv` y `resumen.json`
se generan en `datos/resultados/11_1/`; las cuatro figuras `convergencia.png`,
`residuos.png`, `niveles_iteraciones.png` y `comparacion_metodos.png` en
`graficas/11_1/`. Los historiales incluyen k=0, cambios absolutos y relativos
por componente y en norma infinito, y el vector residuo en cada iteración.
El resumen identifica problema, origen académico, modelo, parámetros, métodos,
referencia NumPy y conservación. Los cocientes relativos no son porcentajes.

## Problema 11.2 y compatibilidad

Las secciones de balance estacionario y resultados que siguen documentan 11.2.
`resolver --problema 11.2` usa Jacobi y Gauss-Jordan, compara sus residuos y
mantiene A=[[5,-1,0],[-1,5,-1],[0,-1,4]], b=(20,30,25). `resolver` sin selector
conserva además Gauss-Seidel, los cálculos anteriores y las rutas originales:
`datos/resultados/` y `graficas/`. No se elimina el algoritmo Gauss-Seidel.
El CSV de comparación y el JSON enumeran solo los métodos de la ejecución.
Un CSV de Gauss-Seidel de una ejecución anterior puede permanecer en la carpeta.

```bash
.venv/bin/python -m python.main resolver --problema 11.2
.venv/bin/python -m python.main resolver
```

`--salida DIRECTORIO` cambia la raíz de salida, conservando las subrutas.
Como antes, ejecutar sobre una raíz existente regenera sus salidas académicas;
para conservar una ejecución histórica se debe elegir una raíz nueva. Durante
esta adaptación las ejecuciones de 11.2 y del comando original se realizaron
en directorios de verificación separados, preservando los originales.
`--alpha` y `--niveles-anteriores` se rechazan fuera de 11.1.

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
