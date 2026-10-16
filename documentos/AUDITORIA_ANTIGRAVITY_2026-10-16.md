# Informe de Auditoría Técnica y Cierre de Software — Proyecto Sensor Awa

- **Fecha:** 16 de octubre de 2026
- **Repositorio:** `ProyectoSensorAwa` (`Proyecto1`)
- **Commit base auditado:** `7cee9b0615304aecc1b51f8f2b4f73e7c2bebdad` (`yanose`), comparado contra `6f6f306`

---

## 1. Resumen ejecutivo y verificación de hipótesis iniciales

Se auditó de forma independiente el estado local y el historial Git del repositorio frente a los ocho puntos levantados en la revisión externa, ejecutando las correcciones verificables en software, pruebas automatizadas, compilación real para Arduino UNO R4 WiFi y consolidación documental sin alterar ningún archivo experimental original.

| # | Hipótesis de auditoría | Severidad | Verificación contra estado local | Acción ejecutada |
|---:|---|---|---|---|
| 1 | Los 10 CSV principales del 16 de octubre están referenciados en JSON pero excluidos por `.gitignore` | **Crítica** | **Confirmado.** Los 10 CSV de `calibracion_sesion_2026-10-16_01_s1_*.csv` y 4 CSV de diagnóstico/verificación del 16 de octubre existen físicamente en `datos/mediciones/` con SHA-256 íntegros, pero `datos/mediciones/*.csv` en `.gitignore` los excluía. | Se añadieron excepciones explícitas (`!datos/mediciones/...`) en [`.gitignore`](../.gitignore) para los 10 CSV principales y los 4 CSV de diagnóstico documentados, tras verificar que no contienen credenciales ni datos privados. |
| 2 | Dos conjuntos de análisis (`analisis_rgb_01` y `analisis_rgb_02`) redundantes | **Media** | **Confirmado.** Ambos directorios tenían idénticos SHA-256 en `auditoria.json`, `estadisticas.csv` y los 7 PNG individuales; solo diferían en el margen superior del título de `comparacion_tres_canales.png`. Ningún documento referenciaba `analisis_rgb_01`. | Se eliminó el duplicado `analisis_rgb_01`, se corrigió el margen de `suptitle` en [`python/graficas.py`](../python/graficas.py) y se regeneró limpiamente `analisis_rgb_02`. |
| 3 | Los JSON y CSV generados contienen rutas absolutas de otra máquina | **Alta** | **Confirmado.** `python/analisis_sesion.py` usaba `Path.resolve()` directamente como cadena en `auditoria.json` y `estadisticas.csv` (`/home/jules/...`). | Se corrigió [`python/analisis_sesion.py`](../python/analisis_sesion.py) para exportar únicamente rutas relativas portables en formato POSIX y resolver entradas desde cualquier directorio de trabajo. |
| 4 | La documentación conserva descripciones antiguas de los límites RGB | **Media** | **Confirmado.** `CALIBRACION_CIRCUITO.md`, `ESTADO_ACTUAL.md` y `arduino/EscanerI2C/README.md` aún mencionaban `LIMITES_ADC_LED=-1` y el color `amarillo` en secciones activas. | Se actualizaron [`README.md`](../README.md), [`CALIBRACION_CIRCUITO.md`](CALIBRACION_CIRCUITO.md), [`ESTADO_ACTUAL.md`](ESTADO_ACTUAL.md) y [`arduino/EscanerI2C/README.md`](../arduino/EscanerI2C/README.md) manteniendo la trazabilidad histórica. |
| 5 | La calibración ADC–altura es exploratoria y no ha superado validación | **Alta (Física)** | **Confirmado.** Solo S1 (`A0`) tiene alturas comunicadas (0, 10, 20, 30, 40 mm y dos validaciones a 25 mm). Las validaciones a 25 mm arrojaron errores de +7,10 mm y −10,78 mm con movimiento del sensor. S2 y S3 no tienen alturas medidas. | Se mantuvo `calibracion_adc1_habilitada: false`, sin extrapolar a S2/S3, y se generó la gráfica [`curva_exploratoria_sensor1.png`](../datos/calibracion/sesion_2026-10-16_01/analisis_rgb_02/curva_exploratoria_sensor1.png) para explicar la discrepancia en la exposición. |
| 6 | La lógica LED está implementada con `NIVEL_AGUA_LED=0` por defecto y sin prueba física | **Media (Eléctrica)** | **Confirmado.** `ColoresNivel.h` implementa 0–49 verde, 50–149 azul, 150–299 morado y 300–1023 rojo. Con `NIVEL_AGUA_LED=0`, `NivelAguaR4.ino` configura D2..D10 en `OUTPUT` `LOW`. | Se evaluó y documentó la diferencia eléctrica entre `OUTPUT LOW` (sumidero activo a 0 V) y alta impedancia (`INPUT`), se añadieron pruebas de las 25 transiciones entre estados RGB sin canales residuales y se compilaron ambas variantes (`NIVEL_AGUA_LED=0` y `1`). |
| 7 | ThingsBoard y el QR todavía no están integrados | **Alta** | **Confirmado.** Solo existía una propuesta documental en `THINGSBOARD_QR_PREPARACION.md` sin código ejecutable de publicación HTTP. | Se implementó [`python/thingsboard.py`](../python/thingsboard.py), el subcomando CLI `thingsboard` en [`python/main.py`](../python/main.py), la validación de URL de dashboard en [`python/qr.py`](../python/qr.py), la plantilla [`plantilla_thingsboard.json`](../datos/calibracion/plantilla_thingsboard.json) y 6 pruebas con servidor HTTP simulado en [`tests/test_thingsboard.py`](../tests/test_thingsboard.py). |
| 8 | La última ejecución documenta 46 pruebas aprobadas y 1 omitida | **Baja (QA)** | **Confirmado.** La línea base ejecutó 47 pruebas (46 aprobadas y 1 omitida por `qrcode`/`cv2` ausentes). | Tras añadir las nuevas pruebas de portabilidad del analizador, transiciones RGB y ThingsBoard HTTP, la suite ejecuta **55 pruebas: 54 aprobadas y 1 omitida** (`0` fallos). |

---

## 2. Verificación de integridad de las mediciones (Fase 2)

Se verificaron físicamente los archivos en `datos/mediciones/` sin modificar ningún byte de los originales:

| Ensayo / Archivo | Ruta relativa | Filas de datos | Huella SHA-256 verificada | Estado en `sesion.json` |
|---|---|---:|---|---|
| `s1_seco_01` | `datos/mediciones/calibracion_sesion_2026-10-16_01_s1_seco_01.csv` | 20 | `9ad5912361f1a06619ca6e6c579ecfabb504fd9f50b26368bc7881edc216c446` | Excluido (ráfaga inicial ~2 ms) |
| `s1_seco_02` | `datos/mediciones/calibracion_sesion_2026-10-16_01_s1_seco_02.csv` | 1 | `eb38772564399fb0554645c317133f1e792142ce69b2ceb2e3a724afbe6b960b` | Excluido (incompleto pre-fix timeout) |
| `s1_seco_03` | `datos/mediciones/calibracion_sesion_2026-10-16_01_s1_seco_03.csv` | 20 | `36373b2495652cb4bc9f61e6beb29feeeca9a59647cc92bcdba8e5ebd801cc20` | Incluido en resumen (0 mm seco) |
| `s1_10mm_01` | `datos/mediciones/calibracion_sesion_2026-10-16_01_s1_10mm_01.csv` | 20 | `dba3bfb27c494ccb396d42c60220ccbac38e769ba687e6d708fc84ca16e21656` | Incluido en resumen (10 mm) |
| `s1_20mm_01` | `datos/mediciones/calibracion_sesion_2026-10-16_01_s1_20mm_01.csv` | 20 | `060ce3161571d52bf20b9aad2208648563759181b0422fe6cd8bb2f054030426` | Excluido (salto inicial 40500 ms) |
| `s1_20mm_02` | `datos/mediciones/calibracion_sesion_2026-10-16_01_s1_20mm_02.csv` | 20 | `cf753ac2159b73bfd6bd0058e27554dc0db336a982e85b1baa9f4fb9878299e1` | Incluido en resumen (20 mm) |
| `s1_30mm_01` | `datos/mediciones/calibracion_sesion_2026-10-16_01_s1_30mm_01.csv` | 20 | `0bedf353ad2846e12271c268b0dd1f10f9e5df09bc4786921c62b83386ea1494` | Incluido en resumen (30 mm) |
| `s1_40mm_01` | `datos/mediciones/calibracion_sesion_2026-10-16_01_s1_40mm_01.csv` | 20 | `95f2358ceff711ad79e3b7bc6cc538cbf91937d8f9d73895f70e4dd0592ec19e` | Incluido en resumen (40 mm) |
| `s1_25mm_validacion_01` | `datos/mediciones/calibracion_sesion_2026-10-16_01_s1_25mm_validacion_01.csv` | 20 | `6b1e74d8e6e46ffc896b3790d9f93c4ead2c99629461b16681a240caa0301e1c` | Incluido en resumen (25 mm val. 1) |
| `s1_25mm_validacion_02` | `datos/mediciones/calibracion_sesion_2026-10-16_01_s1_25mm_validacion_02.csv` | 20 | `d74875cbcb812baa4b2819d5b2731e54cd7396122c7a53e36d786c1670295418` | Incluido en resumen (25 mm val. 2) |

- **Recuentos exactos comprobados:**
  - **181 filas principales** ($181 \times 3 = 543$ lecturas ADC).
  - **140 filas seleccionadas en el resumen preliminar** ($140 \times 3 = 420$ lecturas ADC: 140 de `adc1`, 140 de `adc2` y 140 de `adc3`; **ninguna** es una altura física calibrada validada).
  - **41 filas excluidas** del resumen preliminar ($20 + 1 + 20$).
  - **20 filas de preparación** separadas en 5 archivos `*_preparacion.csv` (4 filas cada uno).
- También se incluyeron en `.gitignore` las 4 capturas de verificación y diagnóstico del 16 de octubre referenciadas en `sesion.json` y `DIAGNOSTICO_SERIAL_2026-10-16.md`:
  - `verificacion_precalibracion_2026-10-16_01.csv` (10 filas, `6040a706ac52...`)
  - `diagnostico_serial_2026-10-16_cable_nuevo_01.csv` (10 filas, `568fd344ecb4...`)
  - `diagnostico_serial_2026-10-16_cable_nuevo_post_carga_01.csv` (30 filas, `f215da0c0265...`)
  - `diagnostico_serial_2026-10-16_post_reset_01.csv` (0 filas de datos, captura vacía documentada, `caed0061ff92...`)

---

## 3. Correcciones en el analizador de sesión y gráficas (Fase 3 y Fase 5)

1. **Eliminación de rutas absolutas (`python/analisis_sesion.py`):**
   - Se introdujo `_portable(path, base_sesion)` para almacenar siempre rutas relativas a la raíz del repositorio (`datos/mediciones/...`, `datos/calibracion/...`) o al directorio de la sesión cuando se ejecuta sobre datos externos en directorios temporales.
   - Se verificó con `grep -rn "/home/" datos/` que no queda ninguna ruta absoluta en `auditoria.json` ni `estadisticas.csv`.
2. **Validación reforzada:**
   - Rechazo explícito de archivos CSV vacíos (solo cabecera sin muestras).
   - Verificación de `muestras_validas` declaradas en los metadatos frente al número real de filas leídas.
   - Detección de archivos CSV duplicados tanto por ruta como por contenido (huella SHA-256 idéntica).
3. **Mejoras gráficas (`python/graficas.py` y `python/analisis_sesion.py`):**
   - Ajuste del rectángulo de `tight_layout(rect=(0, 0, 1, 0.96))` cuando la figura tiene `suptitle`, eliminando el solapamiento entre el título general y el subtítulo `s1_seco_03 · adc2` en `comparacion_tres_canales.png`.
   - Generación automática de `curva_exploratoria_sensor1.png` con los nodos exploratorios de S1 (`0, 10, 20, 30, 40 mm`), sus barras de rango `mín.–máx.` y la discrepancia en las dos validaciones independientes a `25 mm` (`+7,10 mm` y `-10,78 mm`).

---

## 4. Auditoría del firmware RGB y evaluación eléctrica (Fase 4)

1. **Verificación lógica y de fronteras (`arduino/NivelAguaR4/ColoresNivel.h` y `NivelAguaR4.ino`):**
   - `colorParaAdc(adc)` clasifica exhaustivamente: `0..49` → `COLOR_VERDE` (`G=2`), `50..149` → `COLOR_AZUL` (`B=4`), `150..299` → `COLOR_MORADO` (`R+B=5`), `300..1023` → `COLOR_ROJO` (`R=1`), y `<0` o `>1023` → `COLOR_APAGADO` (`0`).
   - Mapeo de pines en orden `R, G, B`: LED 1 `{2, 3, 4}`, LED 2 `{7, 6, 5}` (físico D5=B, D6=G, D7=R), LED 3 `{10, 9, 8}` (físico D8=B, D9=G, D10=R).
   - En `tests/test_firmware.py` se verificaron las $5 \times 5 = 25$ transiciones entre todos los estados de color en cada uno de los tres LED, comprobando ausencia total de canales residuales y funcionamiento simultáneo de Serial (115200) y LCD (`0x27`).
2. **Evaluación eléctrica de `NIVEL_AGUA_LED=0` (`OUTPUT LOW` frente a alta impedancia `INPUT`):**
   - Con `NIVEL_AGUA_LED=0`, el firmware configura los 9 pines `D2..D10` como salidas digitales (`OUTPUT`) con nivel `LOW` (`0 V` activo).
   - Para LED de **cátodo común** conectados a GND, `0 V` en los ánodos garantiza $V_{AK} = 0\text{ V}$ y corriente nula.
   - Sin embargo, `OUTPUT LOW` **no es alta impedancia (`INPUT`)**: el transistor inferior del GPIO en el microcontrolador Renesas RA4M1 conecta activamente el pin a GND. Si en el protoboard existiera por error un LED de **ánodo común** conectado a `+5 V` (o un cortocircuito hacia `+5 V`), el pin en `OUTPUT LOW` actuaría como sumidero de corriente (*sink*), encendiendo el LED y pudiendo superar los **8 mA máximos por GPIO** del UNO R4 WiFi (con $220\;\Omega$ y $V_f \approx 2\text{ V}$, circularían $\approx 13,6\text{ mA}$).
   - Por tanto, se mantiene `NIVEL_AGUA_LED=0` y no se carga nuevo firmware hasta realizar la comprobación física en frío de cátodo común y de las 9 resistencias individuales por canal.

---

## 5. Integración de software ThingsBoard y QR (Fase 6)

Se implementó el módulo [`python/thingsboard.py`](../python/thingsboard.py) y su integración en [`python/main.py`](../python/main.py) y [`python/qr.py`](../python/qr.py):

- **No contienda del puerto serial y resiliencia local:** la captura serial sigue siendo exclusiva de `python.comunicacion`; `publicar_csv` lee filas completas ya volcadas al CSV local, y `capturar_y_publicar` garantiza que el CSV local quede guardado en disco aunque el servidor HTTP no responda.
- **Telemetría honesta:** publica `adc1`, `adc2`, `adc3`, `t_ms`, colores provisionales (`color_adc1..3`) y marca explícitamente `"calibracion_valida": false` y `"altura1..3": null` cuando no se suministra una calibración validada de los tres sensores.
- **Separación histórico vs en vivo:** cada trama incluye `"modo_transmision": "historico" | "en_vivo"` y `"es_tiempo_real": false | true`. Se rechaza por defecto publicar archivos con `origen == "prueba_controlada"`.
- **Reintentos y cursor persistente:** reintenta ante errores de red o HTTP `5xx`/`429` con espera exponencial, falla de inmediato ante HTTP `400/401/403/404`, y guarda un cursor JSON con huella SHA-256 del prefijo enviado para reanudar sin duplicar lotes.
- **Protección de credenciales y QR seguro:** el token nunca se imprime en consola ni errores (`.../api/v1/***/telemetry`), `.gitignore` excluye `.env`, `*.local.json` y `*.token`, y `validar_url_dashboard` impide codificar en el QR URLs con `/api/v1/`, `localhost`, plantillas sin confirmar o el token del dispositivo.

---

## 6. Evidencia de pruebas y compilación independiente (Fase 8)

1. **Suite completa de pruebas unitarias e integración:**
   - Comando: `.venv/bin/python -m unittest discover -s tests -v`
   - Resultado: **55 pruebas ejecutadas en ~6,3 s — 54 aprobadas (`OK`), 1 omitida (`test_qr_roundtrip_real` por ausencia de paquetes `qrcode` y `cv2` en el entorno sin acceso a PyPI), 0 fallos, 0 errores.** Código de retorno: `0`.
2. **Resolución numérica del sistema académico:**
   - Comando: `.venv/bin/python -m python.main resolver`
   - Salida:
     - `Jacobi: h=[5.76911469  8.84596711  8.461393363], iteraciones=9, converge=True, ||r||inf=0.0006725025`
     - `Gauss-Seidel: h=[5.76920392  8.846141764 8.461535441], iteraciones=6, converge=True, ||r||inf=0.00012216582`
     - `Gauss-Jordan: h=[5.769230769 8.846153846 8.461538462], iteraciones=None, converge=True, ||r||inf=7.10542736e-15`
   - Código de retorno: `0`.
3. **Compilación real para Arduino UNO R4 WiFi (`arduino:renesas_uno:unor4wifi`):**
   - Variante por defecto (`NIVEL_AGUA_LED=0`): **59 304 bytes** de programa (22%), **9 020 bytes** de RAM dinámica (27%). Código de retorno: `0`.
   - Variante con LED habilitados (`-DNIVEL_AGUA_LED=1`): **59 352 bytes** de programa (22%), **9 020 bytes** de RAM dinámica (27%). Código de retorno: `0`.
4. **Reproducción limpia del análisis experimental en directorio temporal:**
   - Comando: `.venv/bin/python -m python.analisis_sesion --sesion datos/calibracion/sesion_2026-10-16_01/sesion.json --salida <dir_temporal>`
   - Salida: `CSV principales: 181 filas; resumen: 140 filas, 420 lecturas ADC.` Código de retorno: `0`.
   - Comparación `diff -rq` contra `datos/calibracion/sesion_2026-10-16_01/analisis_rgb_02`: idénticos byte a byte y 0 rutas absolutas locales.

---

## 7.Archivos modificados y añadidos en esta intervención

- **Modificados:**
  - [`.gitignore`](../.gitignore): inclusión controlada de los 14 CSV experimentales/diagnósticos del 16 de octubre y exclusión de `.env`, `*.local.json`, `*.token`.
  - [`python/analisis_sesion.py`](../python/analisis_sesion.py): rutas relativas portables, soporte de ejecución desde cualquier directorio, validación de CSV vacíos/incompletos/duplicados por SHA-256 y generación de `curva_exploratoria_sensor1.png`.
  - [`python/graficas.py`](../python/graficas.py): margen superior automático en `_guardar` cuando existe `fig._suptitle`.
  - [`python/main.py`](../python/main.py): integración del subcomando `thingsboard` y soporte de `--config` en `qr`.
  - [`python/qr.py`](../python/qr.py): adición de `generar_dashboard` con validación de seguridad de URL.
  - [`arduino/NivelAguaR4/NivelAguaR4.ino`](../arduino/NivelAguaR4/NivelAguaR4.ino): documentación técnica del estado eléctrico `OUTPUT LOW` con `NIVEL_AGUA_LED=0`.
  - [`tests/test_analisis_sesion.py`](../tests/test_analisis_sesion.py): pruebas de portabilidad de rutas, ejecución desde otro directorio de trabajo y rechazo de CSV vacíos, incompletos o duplicados.
  - [`tests/test_firmware.py`](../tests/test_firmware.py): pruebas exhaustivas de las 25 transiciones entre estados RGB sin canales residuales y verificación de `OUTPUT LOW`.
  - [`README.md`](../README.md), [`datos/mediciones/LEEME.md`](../datos/mediciones/LEEME.md), [`arduino/NivelAguaR4/README.md`](../arduino/NivelAguaR4/README.md), [`arduino/EscanerI2C/README.md`](../arduino/EscanerI2C/README.md), [`documentos/ANALISIS_ADC_Y_RGB_2026-10-16.md`](ANALISIS_ADC_Y_RGB_2026-10-16.md), [`documentos/CALIBRACION_CIRCUITO.md`](CALIBRACION_CIRCUITO.md), [`documentos/CONEXIONES_LED.md`](CONEXIONES_LED.md), [`documentos/ESTADO_ACTUAL.md`](ESTADO_ACTUAL.md), [`documentos/THINGSBOARD_QR_PREPARACION.md`](THINGSBOARD_QR_PREPARACION.md): consolidación documental y eliminación de contradicciones antiguas.
  - [`datos/calibracion/sesion_2026-10-16_01/analisis_rgb_02/`](../datos/calibracion/sesion_2026-10-16_01/analisis_rgb_02/): regenerado sin rutas absolutas y con `curva_exploratoria_sensor1.png` (eliminando el directorio redundante `analisis_rgb_01`).
- **Añadidos:**
  - [`python/thingsboard.py`](../python/thingsboard.py): cliente HTTP de telemetría ThingsBoard con cursor persistente, reintentos, separación histórico/en vivo y validación de URL QR.
  - [`tests/test_thingsboard.py`](../tests/test_thingsboard.py): suite de pruebas con servidor HTTP local simulado.
  - [`datos/calibracion/plantilla_thingsboard.json`](../datos/calibracion/plantilla_thingsboard.json): plantilla sin credenciales para configuración local.
  - [`documentos/AUDITORIA_ANTIGRAVITY_2026-10-16.md`](AUDITORIA_ANTIGRAVITY_2026-10-16.md): este informe de auditoría.

---

## 8. Limitaciones actuales y próximos pasos concretos

1. **Calibración física pendiente de fijación mecánica:** los datos del sensor 1 demuestran respuesta creciente en la serie inicial (0 a 40 mm), pero las dos comprobaciones a 25 mm (+7,10 mm y −10,78 mm) evidencian inestabilidad por sujeción manual. Faltan además las curvas de los sensores 2 y 3.
2. **Revisión eléctrica previa a encender LED RGB:** antes de cargar en la placa el binario compilado con `-DNIVEL_AGUA_LED=1`, verificar con multímetro y sin alimentación que los tres LED son de cátodo común a GND y que existen 9 resistencias independientes que limitan la corriente de cada canal a $\le 8\text{ mA}$.
3. **Publicación en servidor ThingsBoard real y QR final:** cuando se disponga de la URL de la instancia ThingsBoard y del token del dispositivo, completar `datos/calibracion/thingsboard.local.json`, ejecutar `.venv/bin/python -m python.main thingsboard` y generar el PNG del código QR con `.venv/bin/python -m python.main qr --config`.
