Esta carpeta recibirá exclusivamente capturas del circuito con origen
`experimental`. Se guardó la primera captura real en
`ensayo_r4_2026-10-12_2153UTC.csv`: 20 muestras sin líneas inválidas, con
intervalos Arduino de 500 ms, sensores A0/A2/A3. No se documentó la altura
del agua; no es una calibración. La verificación de la versión final está en
`ensayo_r4_2026-10-12_verificacion_final.csv`.

El protocolo de calibración está en `documentos/CALIBRACION_CIRCUITO.md`.
Las cinco capturas históricas presentes se incluyen de forma explícita en Git
para que sus gráficas y registros puedan reproducirse. Los nuevos CSV siguen
excluidos por defecto hasta revisar su procedencia y decidir su publicación.
Las lecturas de estas capturas son cuentas ADC, no alturas ni umbrales LED.

Las entradas controladas de tests se generan en carpetas temporales y se marcan
`prueba_controlada`. Nunca presentarlas como resultados experimentales.
