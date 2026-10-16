Esta carpeta recibirá exclusivamente capturas del circuito con origen
`experimental`. Se guardó la primera captura real en
`ensayo_r4_2026-10-12_2153UTC.csv`: 20 muestras sin líneas inválidas, con
intervalos Arduino de 500 ms, sensores A0/A2/A3. No se documentó la altura
del agua; no es una calibración. La verificación de la versión final está en
`ensayo_r4_2026-10-12_verificacion_final.csv`.

El protocolo de calibración está en `documentos/CALIBRACION_CIRCUITO.md` y el
registro de la sesión exploratoria en `documentos/CALIBRACION_SESION_2026-10-16.md`.
En `.gitignore` se incluyen explícitamente:
- Las 5 capturas históricas del 12 de octubre de 2026.
- Los 10 CSV principales de la sesión `sesion_2026-10-16_01` (`calibracion_sesion_2026-10-16_01_s1_*.csv`, 181 filas / 543 lecturas ADC en total; 7 ensayos resumidos con 140 filas / 420 lecturas ADC y 3 intentos excluidos con 41 filas / 123 lecturas ADC).
- Las 4 capturas de verificación y diagnóstico USB del 16 de octubre de 2026 documentadas en `documentos/DIAGNOSTICO_SERIAL_2026-10-16.md`.

Los nuevos CSV adicionales siguen excluidos por defecto hasta revisar su
procedencia y decidir su publicación. Las lecturas guardadas en estos CSV son
cuentas ADC crudas (0..1023), no alturas calibradas.

Las entradas controladas de tests se generan en carpetas temporales y se marcan
`prueba_controlada`. Nunca presentarlas como resultados experimentales.

