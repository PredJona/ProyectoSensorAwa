# Registro de validación correctiva — 14 octubre 2026

Los comandos se ejecutaron desde la raíz de `Proyecto1`. Las rutas `/tmp`
son productos temporales de verificación, no datos del circuito. No se
detectó ni probó una placa física en esta sesión y no se cargó firmware.

## Comandos y resultados

| Comando | Resultado observado |
|---|---|
| `.venv/bin/python -m unittest discover -s tests -v` | Antes: 36 casos, 35 correctos y uno omitido. Después: 39 casos, 38 correctos y uno omitido; sin fallos. La omisión es QR por falta de qrcode/OpenCV. |
| `XDG_CACHE_HOME=/tmp/proyecto1-cierre-cache arduino-cli compile --fqbn arduino:renesas_uno:unor4wifi --build-path /tmp/proyecto1-cierre-build arduino/NivelAguaR4` | Código 0; 59344 bytes de programa y 9020 bytes globales. Aviso de metadatos `architectures=all` de LiquidCrystal_I2C, sin error de compilación. |
| `.venv/bin/python -m python.main resolver` | Código 0. Jacobi: 9 iteraciones, residuo infinito 0.0006725025; Gauss-Seidel: 6, 0.00012216582; Gauss-Jordan: residuo 7.10542736e-15. |
| `.venv/bin/python -m python.main graficar --csv datos/mediciones/ensayo_r4_2026-10-12_2153UTC.csv --salida /tmp/proyecto1-cierre-adc.png` | Código 0; PNG ADC generado y revisado visualmente. |
| `.venv/bin/python -c 'import csv,tempfile,pathlib; from python.graficas import mediciones; d=tempfile.TemporaryDirectory(); files=sorted(pathlib.Path("datos/mediciones").glob("*.csv")); [(mediciones(p,pathlib.Path(d.name)/(p.stem+".png")),print(p.name,sum(1 for _ in csv.DictReader(p.open())))) for p in files]'` | Código 0; los cinco CSV se leyeron y generaron PNG temporales: 6, 20, 10, 10 y 12 muestras respectivamente. |
| `sha256sum datos/mediciones/ensayo_r4_2026-10-12_verificacion_final.csv` | Coincide con `a6cb73316ac89e13c92abe5da34d5fa2478dab7899eff44dc96ac3ec34e0ec11` del metadato histórico. |
| `git -c core.whitespace=cr-at-eol diff --cached --check` | Código 0; comprueba el diff preparado sin tratar los terminadores CRLF originales de los CSV como espacios finales. |

Se inspeccionaron visualmente las cuatro figuras académicas regeneradas:
convergencia, residuos, niveles por iteración y comparación de métodos.
Los ejes conservan la etiqueta de unidades académicas. La gráfica
experimental presenta cuentas ADC sin calibrar y tiempo de recepción UTC;
no se interpreta como altura. El resumen JSON regenerado usa rutas relativas.

## Regresiones y errores reproducidos

Antes de corregir el código, los tests añadidos fallaron como se esperaba:
la validación aceptaba D11 para un canal RGB; `capturar()` abría el puerto
antes de rechazar argumentos inválidos; `timestamp_utc` aceptaba una zona
distinta de UTC; se admitían columnas CSV adicionales; y `resumen.json`
contenía rutas absolutas. La primera ejecución de los tests nuevos tuvo
cinco fallos y dos errores; el test de apertura de puerto se ajustó para
aislar cada caso. Después de las correcciones, la suite completa pasó.
No se modificaron A, b, los métodos numéricos ni los límites ADC LED.

## Capturas históricas conservadas

| CSV en `datos/mediciones/` | SHA-256 |
|---|---|
| `diagnostico_lcd_2026-10-12.csv` | `3edd8fd211c4e0b1acbfe4c6627b336746a5fd0954973c99e18fa6b88d566749` |
| `ensayo_r4_2026-10-12_2153UTC.csv` | `57a4ccc2abac1051b82d66c7f89e623820f06fc6ebc2f4b33b774901b106558a` |
| `ensayo_r4_2026-10-12_verificacion_final.csv` | `a6cb73316ac89e13c92abe5da34d5fa2478dab7899eff44dc96ac3ec34e0ec11` |
| `ensayo_r4_led_pines_2026-10-12.csv` | `2204e358ae6f68d0f2a3b7d8ef5199053d501cecc8f358a177f3465bf70992c0` |
| `prueba_sensor2_estado_inicial_2026-10-12.csv` | `3893922d56a74d06995136641b9a995ef5351c5778925b61fad745bcdb24a6eb` |

Se conservaron los bytes originales y sus huellas; los CSV usan terminadores
CRLF. Son lecturas ADC, no puntos de calibración. Su nombre de archivo no demuestra
la condición física exacta durante la captura.

## Archivos modificados

- Código: `arduino/NivelAguaR4/ColoresNivel.h`, `python/comunicacion.py`,
  `python/graficas.py`, `python/main.py`.
- Pruebas: `tests/test_adquisicion.py`, `tests/test_cli.py`,
  `tests/test_firmware.py`, `tests/test_graficas.py`.
- Resultados y procedencia: `.gitignore`, `datos/calibracion/plantilla_puntos.csv`,
  `datos/mediciones/LEEME.md`, los cinco CSV listados arriba y
  `datos/resultados/resumen.json`.
- Documentación: `README.md`, `arduino/NivelAguaR4/README.md`,
  `documentos/AVANCE.md`, `CALIBRACION_CIRCUITO.md`, `CONEXIONES_LED.md`,
  `DIAGNOSTICO_LCD_2026-10-12.md`, `INTEGRACION_R4_2026-10-12.md`,
  `MODELO.md`, `PLAN.md`, `REQUISITOS.md`, `ESTADO_ACTUAL.md` y este registro.

No existe `documentos/evidencias/` en esta copia. Las fotografías deben
agregarse allí antes de revisarlas y describirlas con evidencia directa.
