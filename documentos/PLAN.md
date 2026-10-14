# Plan y decisiones de implementación — 12 octubre 2026

Este plan conserva decisiones históricas de la primera implementación. El
estado actual del circuito, el cableado A0/A2/A3 y el trabajo experimental
pendiente constan en [ESTADO_ACTUAL.md](ESTADO_ACTUAL.md).

Objetivo: completar las fases independientes del circuito del Problema 11,
con los tres métodos solicitados, evidencia numérica y documentación trazable.
La especificación de esta ejecución es el encargo del usuario y los dos
documentos PROYECTO, identificados en REQUISITOS.md.

Arquitectura: aplicación de terminal en la carpeta Proyecto1 existente.
Python 3, NumPy, Matplotlib, PySerial; QR opcional. Los archivos de clase se
conservan. Las mediciones nunca alimentan automáticamente b: se requiere
justificación física. No se crean aplicaciones web ni se publica nada.

## Tareas y comprobación

1. Inspección: inventariar archivos originales, extraer textos OOXML y fechas;
   contrastar guías, rúbricas, QR y ejemplos. Registrar fuentes y pendientes.
2. Matemática: crear primero tests de jacobi(A,b,x0,tol,max_iter),
   gauss_seidel con la misma interfaz y gauss_jordan(A,b,pivot_tol).
   Resultado contiene solución, residuo, historial y estado de convergencia;
   Gauss-Jordan conserva las operaciones y matrices aumentadas.
   Verificar primer paso, solución exacta, NumPy, pivoteo, entradas inválidas,
   no convergencia y errores relativos indefinidos. Ejecutar RED y GREEN.
3. Exportación y gráficas: tests de CSV y PNG; exportar cada iteración,
   operaciones de filas, comparación y resumen JSON; generar error, residuo,
   trayectorias y comparación. La gráfica temporal requiere un CSV real.
4. Adquisición: sketch A0/A1/A2 con millis y CSV; parser estricto de
   t_ms,adc1,adc2,adc3, registro UTC, timeout y conservación ante desconexión.
   Tests con entradas controladas y calibración monotónica de puntos medidos,
   sin extrapolación silenciosa. Compilar para arduino:avr:uno si está disponible.
5. Documentar ejecución, modelo y verificación; preparar generación/lectura QR
   parametrizada sin asignar contenido final. Revisión final y pruebas completas.

## Focos de revisión

División entre cero; pivote final singular; falsa convergencia por límite de
iteraciones; fragmentos seriales; reinicio de millis; calibración fuera de rango;
confusión entre residuo y error; reutilización accidental de datos sintéticos.

## Registro de decisiones

- El usuario pidió inspeccionar e implementar en esta ejecución; se continúa
  dentro de esa autorización, sin introducir aprobaciones de diseño adicionales.
- No hay repositorio Git operativo; no se crean ramas, worktrees ni commits.
- Tolerancia 0.001, máximo 100 y criterio estricto de norma infinito del cambio,
  tomados de la guía específica y del código del profesor.
- Eliminación de Gauss y Doolittle pertenecen a bancos distintos. Se documentan
  como pendientes de confirmar, manteniendo los tres métodos del encargo.
- QR: existe ejemplo de selección por identificador, pero falta instrucción
  específica de Proyecto 1. Se prepara la herramienta sin decidir el contenido.
- El entorno local usa paquetes ya disponibles del sistema y Matplotlib de
  10Sep2026 mediante un .pth dentro de .venv. requirements.txt permite una
  instalación independiente cuando se disponga de red. No se modifica ese entorno.

## Registro de cierre

- Tareas 1–3 completas: inventario, textos, requisitos, métodos, tablas y cuatro
  PNG generados y revisados. Referencia exacta y NumPy verificadas.
- Tarea 4 preparada y probada sin sensores: sketch compilado para UNO;
  parser, captura y calibración probados; no se declara validación física.
- Tarea 5 completa dentro del alcance sin hardware: README, modelo, avance y
  utilidad QR preparada. Contenido definitivo y roundtrip QR pendientes.
- Revisión independiente mediante subagente de solo lectura, según
  requesting-code-review: tres hallazgos importantes, corregidos en una pasada
  con regresiones RED→GREEN. Sin hallazgos menores diferidos.
- Correcciones: leer bytes con plazo entre lecturas; rechazar residuo/escala
  no finitos; proteger imagen y texto QR. Suite final: 29 casos, 28 aprobados,
  1 omitido por dependencias QR. Evidencia en PRUEBAS.txt.
- La verificación física y los datos de calibración no se sustituyen por
  simulaciones. La fase 7 queda pendiente del circuito.
