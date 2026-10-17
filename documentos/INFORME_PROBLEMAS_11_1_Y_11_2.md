# Adaptación de los problemas 11.1 y 11.2

## Auditoría previa y alcance

Se revisaron `python/main.py`, `python/metodos.py`, `python/graficas.py`,
`tests/test_metodos.py`, `tests/test_cli.py`, `tests/test_graficas.py`,
`documentos/MODELO.md`, `README.md` y las salidas históricas de resultados y gráficas.

Git mostraba únicamente dos archivos previos sin seguimiento:
`datos/mediciones/awa_agua_01.sesion.json` y
`datos/resultados/awa_agua_01.tb.cursor.json`. Se conservaron sin cambios.
No se hizo commit ni push.

El programa original resolvía únicamente la matriz ahora identificada como 11.2,
con Jacobi, Gauss-Seidel y Gauss-Jordan. Los algoritmos ya soportaban matrices
genéricas, historial k=0, cambios absolutos/relativos y residuos. Se reutilizaron
sin cambiar su implementación ni su criterio de parada.

Antes de modificar se comunicaron estas precisiones:

- La singularidad descrita para el sistema cerrado corresponde al equilibrio
  estacionario. Euler implícito agrega la identidad y produce un sistema no
  singular para un paso temporal: no hay contradicción entre ambos modelos.
- La solución exacta de 11.1 conserva suma 6. Las aproximaciones con parada por
  cambio de 0.001 no conservan exactamente 6; ese defecto se reporta.
- No se localizó `Problema11_Planteamiento_v4.pdf` en el repositorio ni en las
  carpetas de documentos, descargas y temporales consultadas. Se siguieron las
  matrices y requisitos expresos del usuario. No se atribuye revisión al PDF.
- El conteo de pruebas del README estaba desactualizado; se sustituyó por una
  indicación de consultar el total de cada ejecución.

## Archivos modificados

| Archivo | Cambio |
|---|---|
| `python/metodos.py` | Añade `sistema_11_1(alpha, niveles_anteriores)`; conserva las constantes y algoritmos anteriores. |
| `python/main.py` | Selector de problema, parámetros de 11.1, métodos por versión, exportación separada y metadatos del resumen. |
| `python/graficas.py` | Identifica el problema en títulos; incluye el residuo final directo de Gauss-Jordan en la comparación. La función experimental no cambia. |
| `tests/test_metodos.py` | Cuatro pruebas nuevas de matriz, conservación, primeras iteraciones, convergencia, errores, residuos y parámetros inválidos. |
| `tests/test_cli.py` | Cuatro pruebas nuevas de selección, aislamiento, compatibilidad, parámetros y límite de iteraciones. |
| `documentos/MODELO.md` | Deducción temporal de 11.1, distinción de índices, conservación, salidas y compatibilidad de 11.2. |
| `README.md` | Comandos, separación conceptual, resultados y rutas por problema. |

Archivos nuevos: este informe y los ocho artefactos de 11.1 enumerados abajo.

## Cotejo posterior con el PDF v4

Después de la implementación, el equipo añadió
[`Problema11_Planteamiento_v4.pdf`](Problema11_Planteamiento_v4.pdf) a `documentos/`.
Se revisaron íntegramente sus seis páginas mediante:

```bash
pdftotext -layout documentos/Problema11_Planteamiento_v4.pdf -
pdfinfo documentos/Problema11_Planteamiento_v4.pdf
```

Ambos comandos finalizaron con código 0. El cotejo confirma:

| Fuente | Requisito | Correspondencia implementada |
|---|---|---|
| Páginas 1–2 | Problemas independientes; continuidad cerrada en 11.1; Jacobi y Gauss-Seidel | Selector y métodos separados, sin usar ADC como b. |
| Página 3 | Secciones iguales S, conductancia común k, alpha=k·Delta_t/S; matriz de Euler implícito | `sistema_11_1` construye exactamente A(alpha); b son los niveles anteriores. |
| Páginas 3–4 | Ejemplo hipotético alpha=1, b=(3,2,1), suma 6 | Matriz y vector coincidentes; conservación comprobada y defecto de aproximación informado. |
| Páginas 4–5 | 11.2 con A=[[5,-1,0],[-1,5,-1],[0,-1,4]], b=(20,30,25) | Constantes históricas intactas; interpretación académica con k=1, c=(4,3,3), q=(20,30,25). |
| Páginas 4 y 6 | Jacobi y Gauss-Jordan, residuo r=Ah-b y norma infinito | Métodos del selector explícito 11.2, CSV/JSON y gráfica de residuos. |
| Página 6 | Parte experimental separada; calibración no validada | No se cambió el flujo experimental ni se introdujeron alturas físicas. |

No se encontraron discrepancias que requieran cambiar matrices, algoritmos o
hipótesis. El PDF no fija los conteos 14/9 ni desarrolla las tablas: los deja
para otros apartados. Esos resultados se obtuvieron ejecutando los algoritmos
con x0=(0,0,0) y tol=0.001, según la solicitud de implementación.
Este cotejo solo actualiza la documentación; no modifica código ni resultados.

## Comportamiento final

- `resolver --problema 11.1`: Jacobi y Gauss-Seidel, alpha=1, b=(3,2,1).
- `resolver --problema 11.2`: Jacobi y Gauss-Jordan, A y b históricos.
- `resolver`: los tres métodos históricos sobre 11.2, con rutas compatibles.
- `--alpha` y `--niveles-anteriores` son exclusivos de 11.1; `--x0` es siempre
  la aproximación inicial del solucionador, no el vector del instante anterior.
- Se validan alpha positivo/finito y representable con dominancia estricta,
  tres niveles finitos no negativos referidos al fondo, y los parámetros
  iterativos mediante las validaciones existentes.
- JSON: origen académico, identificador, modelo, A, b, parámetros, métodos,
  comparación con NumPy, convergencia, residuos y, en 11.1, defecto de suma.
- Los CSV iterativos conservan las columnas existentes: k, h1..h3, errores
  absolutos y relativos por componente, normas infinito y r1..r3.

No se migraron las rutas de 11.2. Como antes, ejecutar en una raíz con resultados
regenera sus salidas académicas. Se usó `--salida` al verificar 11.2 y el comando
original para evitar sobrescribir los históricos. Un CSV antiguo de un método
no seleccionado no se borra; el JSON enumera los métodos realmente ejecutados.

## Resultados numéricos locales

Con x0=(0,0,0), tol=0.001, max_iter=100, sin redondeo interno:

| Problema | Método | h1 | h2 | h3 | Iteraciones | Norma infinito del residuo |
|---|---|---:|---:|---:|---:|---:|
| 11.1 | Jacobi | 2.499085505 | 1.999085505 | 1.499085505 | 14 | 0.000914494741656 |
| 11.1 | Gauss-Seidel | 2.499809480 | 1.999872987 | 1.499936493 | 9 | 0.000254026317126 |
| 11.2 | Jacobi | 5.769114690 | 8.845967110 | 8.461393363 | 9 | 0.000672502500000 |
| 11.2 | Gauss-Jordan | 5.769230769 | 8.846153846 | 8.461538462 | Directo | 7.105427357601002e-15 |

La ejecución compatible conserva Gauss-Seidel en 11.2: 6 iteraciones,
h=(5.769203919600001, 8.84614176382, 8.461535440955), residuo infinito
0.00012216581999524578. Los cuatro CSV históricos regenerados con el comando
original coinciden byte por byte con los almacenados en el repositorio.

11.1 tiene solución exacta (2.5,2,1.5), con A h-b=(0,0,0). NumPy devuelve
(2.5,2,1.5000000000000002). Todas las filas son estrictamente dominantes.
La suma exacta anterior y posterior es 6; para sección igual S, el volumen
total es proporcional a esa suma. Los defectos finales son:

- Jacobi: suma=5.997256515775035, defecto=-0.0027434842249647318.
- Gauss-Seidel: suma=5.999618960524311, defecto=-0.0003810394756893487.

Se verificó `sum(h)-sum(b) = sum(Ah-b)` y la cota
`abs(defecto) <= 3*norma_infinito(residuo)` dentro del redondeo flotante.
Los cambios finales son 0.0009144947416550586 (Jacobi) y
0.0003810394756897928 (Seidel). No se ajustaron artificialmente las soluciones
para forzar conservación. En 11.2 la referencia exacta permanece
(75/13,115/13,110/13).

## Comandos ejecutados

Desde `/home/jules/Documentos/proyectoun/metnum/Proyecto1`:

```bash
.venv/bin/python -m python.main resolver --problema 11.1
.venv/bin/python -m python.main resolver --problema 11.2 --salida /tmp/awa-problemas-v4-wWeCFd/11_2
.venv/bin/python -m python.main resolver --salida /tmp/awa-problemas-v4-wWeCFd/compatible
.venv/bin/python -m python.main resolver --problema 11.1 --alpha 0.5 --niveles-anteriores 4 2 0 --x0 1 1 1 --salida /tmp/awa-problemas-v4-wWeCFd/personalizado --sin-graficas
```

Los cuatro comandos finalizaron con código 0. El caso personalizado produjo
A=[[1.5,-0.5,0],[-0.5,2,-0.5],[0,-0.5,1.5]], b=(4,2,0) y referencia
(3.333333333,2,0.666666667), independiente de x0=(1,1,1).
Jacobi convergió en 9 iteraciones y Gauss-Seidel en 3.

```bash
.venv/bin/python -m python.main resolver --problema 11.1 --alpha 0 --salida /tmp/awa-problemas-v4-wWeCFd/invalido --sin-graficas
```

Rechazado como corresponde, código 2: `alpha debe ser positiva y finita.`
Las pruebas verifican que los parámetros inválidos no generan archivos.

```bash
.venv/bin/python -m unittest tests.test_metodos tests.test_cli tests.test_graficas -v
.venv/bin/python -m unittest discover -s tests -v
git diff --check
```

- Pruebas focalizadas: 33 ejecutadas, 33 aprobadas, 0 fallidas, 0 omitidas.
- Suite completa: **98 ejecutadas, 98 aprobadas, 0 fallidas, 0 errores,
  0 omitidas**, en 25.923 s; salida `OK`, código 0.
- La suite incluye servidores HTTP locales simulados y pseudoterminales;
  se ejecutó con permiso para sockets locales, sin publicar en Cloud.
- Las nuevas pruebas se ejecutaron antes de implementar: detectaron el
  constructor y opciones CLI faltantes; después del cambio pasaron.
- `git diff --check`: sin incidencias.
- Se inspeccionaron visualmente la gráfica de niveles de 11.1 y la de
  residuos de 11.2, además de verificar la generación PNG en las pruebas.

## Rutas de entrega

Raíz del repositorio: `/home/jules/Documentos/proyectoun/metnum/Proyecto1`.

11.1, archivos nuevos dentro de esa raíz:

```text
datos/resultados/11_1/jacobi.csv
datos/resultados/11_1/gauss_seidel.csv
datos/resultados/11_1/comparacion.csv
datos/resultados/11_1/resumen.json
graficas/11_1/convergencia.png
graficas/11_1/residuos.png
graficas/11_1/niveles_iteraciones.png
graficas/11_1/comparacion_metodos.png
```

11.2, salidas nuevas de verificación (temporales, pueden desaparecer al limpiar `/tmp`):

```text
/tmp/awa-problemas-v4-wWeCFd/11_2/datos/resultados/jacobi.csv
/tmp/awa-problemas-v4-wWeCFd/11_2/datos/resultados/gauss_jordan_operaciones.csv
/tmp/awa-problemas-v4-wWeCFd/11_2/datos/resultados/comparacion.csv
/tmp/awa-problemas-v4-wWeCFd/11_2/datos/resultados/resumen.json
/tmp/awa-problemas-v4-wWeCFd/11_2/graficas/convergencia.png
/tmp/awa-problemas-v4-wWeCFd/11_2/graficas/residuos.png
/tmp/awa-problemas-v4-wWeCFd/11_2/graficas/niveles_iteraciones.png
/tmp/awa-problemas-v4-wWeCFd/11_2/graficas/comparacion_metodos.png
```

Las salidas del comando compatible están bajo
`/tmp/awa-problemas-v4-wWeCFd/compatible/datos/resultados/` y
`/tmp/awa-problemas-v4-wWeCFd/compatible/graficas/`.
Las salidas históricas permanecen en `datos/resultados/` y `graficas/` del
repositorio sin alterar. No se cambió su estructura.

## Integridad y pendientes

Se compararon SHA-256 de 112 archivos originales: todos los archivos existentes
en `arduino/`, `datos/`, `graficas/` y los módulos `comunicacion.py`,
`thingsboard.py`, `qr.py`, `calibracion.py`, `configurar_cloud.py`.
**Cero modificaciones o eliminaciones** entre esos archivos, incluidos los
dos archivos sin seguimiento que ya existían. Solo se añadieron los ocho
artefactos académicos de 11.1 dentro de esas carpetas.

Pendiente documental resuelto: se cotejó el PDF v4 después de su incorporación,
sin discrepancias con la especificación matemática implementada.
La calibración ADC–altura sigue sin validar y no forma parte de esta adaptación.
No se modificaron firmware, pines, LCD, USB, capturas, ThingsBoard, QR ni LED.
No se leyeron ni revelaron credenciales, ni se realizó push.
