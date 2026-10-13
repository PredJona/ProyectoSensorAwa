Esta carpeta recibirá exclusivamente capturas del circuito con origen
`experimental`. Se guardó la primera captura real en
`ensayo_r4_2026-10-12_2153UTC.csv`: 20 muestras sin líneas inválidas, con
intervalos Arduino de 500 ms, sensores A0/A2/A3. No se documentó la altura
del agua; no es una calibración. La verificación de la versión final está en
`ensayo_r4_2026-10-12_verificacion_final.csv`.

El protocolo de calibración está en `documentos/CALIBRACION_CIRCUITO.md`.
La exclusión Git de los CSV ya existía; estos archivos permanecen localmente.

Las entradas controladas de tests se generan en carpetas temporales y se marcan
`prueba_controlada`. Nunca presentarlas como resultados experimentales.
