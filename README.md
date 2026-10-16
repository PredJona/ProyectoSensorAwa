# Proyecto 1 — Métodos Numéricos: Sensor Awa (Nivel de Agua)

Universidad Tecnológica de Panamá — Métodos Numéricos (Problema 11).
Implementación y verificación de métodos numéricos en Python, adquisición experimental con **Arduino UNO R4 WiFi**, análisis estadístico reproducible, lógica de clasificación RGB y publicador HTTP para **ThingsBoard + QR**.

---

## 1. Ejecución rápida y reproducción completa

Desde la carpeta `Proyecto1`:

```bash
# 1. Ejecutar toda la suite de pruebas (55 pruebas: 54 aprobadas, 1 omitida sin qrcode/cv2)
.venv/bin/python -m unittest discover -s tests -v

# 2. Resolver el sistema académico (Jacobi, Gauss-Seidel y Gauss-Jordan) y exportar tablas/gráficas
.venv/bin/python -m python.main resolver

# 3. Regenerar la auditoría estadística y gráficas de la sesión experimental del 16 de octubre
.venv/bin/python -m python.analisis_sesion \
  --sesion datos/calibracion/sesion_2026-10-16_01/sesion.json \
  --salida /tmp/awa-reproduccion-sesion
```

### Instalación en un entorno limpio (otra computadora)

El entorno `.venv` local de esta máquina ya está configurado. Para clonar y reproducir en otra computadora:

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
# Opcional para generar y verificar códigos QR con OpenCV:
.venv/bin/python -m pip install -r requirements-qr-lectura.txt
```

En Windows use `.venv\Scripts\python.exe` en lugar de `.venv/bin/python`. Las pruebas usan `unittest` de la biblioteca estándar.

---

## 2. Estado real del proyecto

| Componente | Estado actual | Evidencia en el repositorio |
|---|---|---|
| **Métodos numéricos** (`jacobi`, `gauss_seidel`, `gauss_jordan`) | **Completado y verificado** | [`python/metodos.py`](python/metodos.py), [`datos/resultados/`](datos/resultados/), [`graficas/`](graficas/) |
| **Firmware Arduino UNO R4 WiFi** (`NivelAguaR4.ino`) | **Compilado y probado** (base cargada en placa; variante RGB lista sin cargar) | [`arduino/NivelAguaR4/`](arduino/NivelAguaR4/), [`tests/test_firmware.py`](tests/test_firmware.py) |
| **Comunicación USB Serial y LCD I²C `0x27`** | **Operativo en hardware real** (115200 baudios, cada 500 ms) | [`documentos/DIAGNOSTICO_SERIAL_2026-10-16.md`](documentos/DIAGNOSTICO_SERIAL_2026-10-16.md) |
| **Datos experimentales y reproducibilidad SHA-256** | **19 CSV originales incluidos en Git y auditados** | [`datos/mediciones/`](datos/mediciones/), [`datos/calibracion/sesion_2026-10-16_01/`](datos/calibracion/sesion_2026-10-16_01/) |
| **Analizador estadístico de sesión** (`analisis_sesion.py`) | **Completado y portable** (rutas relativas, 0 rutas absolutas locales) | [`python/analisis_sesion.py`](python/analisis_sesion.py), [`tests/test_analisis_sesion.py`](tests/test_analisis_sesion.py) |
| **Calibración física ADC → altura** | **Exploratoria en Sensor 1 (no validada); pendiente en Sensores 2 y 3** | [`documentos/CALIBRACION_SESION_2026-10-16.md`](documentos/CALIBRACION_SESION_2026-10-16.md) |
| **LED RGB por sensor** (`ColoresNivel.h`) | **Lógica verificada en software; apagados por defecto (`NIVEL_AGUA_LED=0`)** | [`documentos/CONEXIONES_LED.md`](documentos/CONEXIONES_LED.md) |
| **Integración ThingsBoard y QR** (`thingsboard.py`, `qr.py`) | **Software terminado y probado con servidor HTTP simulado; falta servidor/token real** | [`python/thingsboard.py`](python/thingsboard.py), [`tests/test_thingsboard.py`](tests/test_thingsboard.py) |

---

## 3. Separación conceptual y desarrollo matemático

El proyecto distingue estrictamente cuatro planos que **no deben confundirse ni mezclarse**:

1. **Modelo matemático académico del profesor:**
   Sistema lineal estacionario suministrado en la guía de clase para tres depósitos acoplados:
   $$A = \begin{bmatrix} 5 & -1 & 0 \\ -1 & 5 & -1 \\ 0 & -1 & 4 \end{bmatrix}, \quad b = \begin{bmatrix} 20 \\ 30 \\ 25 \end{bmatrix}, \quad A h = b$$
   La matriz $A$ es estrictamente diagonal dominante ($|5|>1$, $|5|>2$, $|4|>1$), lo que garantiza convergencia global de Jacobi y Gauss-Seidel para cualquier vector inicial $h^{(0)}$. La solución exacta racional es:
   $$h^* = \left(\frac{75}{13},\; \frac{115}{13},\; \frac{110}{13}\right) \approx (5.769230769,\; 8.846153846,\; 8.461538462)\text{ [u. académicas]}$$
   *(Nota: un tanque cerrado sin aportes ni descargas externas tiene matriz laplaciana singular y equilibrio $h_1=h_2=h_3$; por tanto, $A$ y $b$ representan el ejercicio académico con aportes/salidas nominales, no lecturas crudas del ADC).*

2. **Soluciones mediante métodos numéricos** ($h^{(0)}=(0,0,0)$, criterio $\|h^{(k)}-h^{(k-1)}\|_\infty < 0.001$, sin redondeo intermedio):

   | Método | $h_1$ | $h_2$ | $h_3$ | Iteraciones | $\|h^{(k)}-h^{(k-1)}\|_\infty$ | Residuo $\|Ah-b\|_\infty$ | Error vs exacta $\|h-h^*\|_\infty$ |
   |---|---:|---:|---:|---:|---:|---:|---:|
   | **Jacobi** | 5.769114690 | 8.845967110 | 8.461393363 | 9 | $3.9366 \times 10^{-4}$ | $6.7250 \times 10^{-4}$ | $1.8674 \times 10^{-4}$ |
   | **Gauss-Seidel** | 5.769203920 | 8.846141764 | 8.461535441 | 6 | $2.7148 \times 10^{-4}$ | $1.2217 \times 10^{-4}$ | $2.6850 \times 10^{-5}$ |
   | **Gauss-Jordan** | 5.769230769 | 8.846153846 | 8.461538462 | Directo | No aplica | $7.1054 \times 10^{-15}$ | $0.0000$ |

   - Tablas exportadas en [`datos/resultados/`](datos/resultados/): `jacobi.csv`, `gauss_seidel.csv`, `gauss_jordan_operaciones.csv`, `comparacion.csv` y `resumen.json`.
   - Gráficas académicas en [`graficas/`](graficas/): `convergencia.png`, `residuos.png`, `niveles_iteraciones.png` y `comparacion_metodos.png`.

3. **Datos experimentales adquiridos con Arduino:**
   Lecturas enteras de 10 bits (`0..1023` cuentas ADC) muestreadas cada `500 ms` en los tres canales (`A0`, `A2`, `A3`) y registradas con marca de recepción UTC en [`datos/mediciones/`](datos/mediciones/).

4. **Calibración física (aún no validada):**
   Módulo [`python/calibracion.py`](python/calibracion.py) que exige pares `[ADC, altura]` estrictamente crecientes para los tres sensores e interpola linealmente sin extrapolar fuera del dominio medido.

---

## 4. Montaje físico, conexiones y seguridad eléctrica LED

El firmware principal es [`arduino/NivelAguaR4/NivelAguaR4.ino`](arduino/NivelAguaR4/NivelAguaR4.ino) para **Arduino UNO R4 WiFi** (`arduino:renesas_uno:unor4wifi`).

| Componente | Pines en UNO R4 WiFi | Detalles técnicos |
|---|---|---|
| **Sensor 1 / 2 / 3** | `A0` / `A2` / `A3` | Resolución `analogReadResolution(10)` (0..1023), muestreo cada 500 ms, VCC 5 V y GND común |
| **Pantalla LCD 16×2 I²C** | `SDA` (`A4`), `SCL` (`A5`) | Dirección `0x27` confirmada con [`EscanerI2C`](arduino/EscanerI2C/EscanerI2C.ino); muestra `S1`, `S2` y `S3` en cuentas ADC |
| **LED RGB 1 (Sensor 1)** | `R=D2`, `G=D3`, `B=D4` | Orden físico comunicado: D2/D3/D4 = R/G/B |
| **LED RGB 2 (Sensor 2)** | `R=D7`, `G=D6`, `B=D5` | Orden físico comunicado: D5/D6/D7 = B/G/R (mapeado a R/G/B en `PINES_LED`) |
| **LED RGB 3 (Sensor 3)** | `R=D10`, `G=D9`, `B=D8` | Orden físico comunicado: D8/D9/D10 = B/G/R (mapeado a R/G/B en `PINES_LED`) |

### Clasificación RGB provisional (`ColoresNivel.h`) y evaluación eléctrica

| Cuentas ADC (inclusivo) | Color | Canales activos (R/G/B) |
|---|---|---|
| `0 – 49` | Verde | `0 / 1 / 0` |
| `50 – 149` | Azul | `0 / 0 / 1` |
| `150 – 299` | Morado | `1 / 0 / 1` |
| `300 – 1023` | Rojo | `1 / 0 / 0` |
| Fuera de `0..1023` | Apagado | `0 / 0 / 0` |

- **Comportamiento eléctrico con `NIVEL_AGUA_LED=0` (valor por defecto):**
  El firmware configura los nueve pines `D2..D10` como `OUTPUT` y escribe `LOW` (`0 V` activo hacia GND). Esto mantiene apagados los LED de **cátodo común** conectados a GND, pero **no equivale a alta impedancia (`INPUT`)**: si un LED en el protoboard estuviese conectado por error como ánodo común a `+5 V`, un pin en `OUTPUT LOW` drenaría corriente (*current sink*).
- **Límite de corriente del RA4M1:**
  El Arduino UNO R4 WiFi admite como máximo **8 mA por pin GPIO** (con $R = 220\;\Omega$ y $V_f \approx 2\text{ V}$, la corriente sería $\approx 13.6\text{ mA} > 8\text{ mA}$). Por ello `NIVEL_AGUA_LED=0` se mantiene por defecto hasta verificar en frío el cátodo común y las 9 resistencias independientes (recomendado $\ge 1\text{ k}\Omega$ por canal).

Compilación verificada sin cargar a la placa:

```bash
# Variante segura por defecto (NIVEL_AGUA_LED=0): 59304 bytes de programa / 9020 bytes RAM
arduino-cli compile --fqbn arduino:renesas_uno:unor4wifi arduino/NivelAguaR4

# Variante con LED habilitados (NIVEL_AGUA_LED=1): 59352 bytes de programa / 9020 bytes RAM
arduino-cli compile --fqbn arduino:renesas_uno:unor4wifi \
  --build-property 'compiler.cpp.extra_flags=-DNIVEL_AGUA_LED=1' arduino/NivelAguaR4
```

---

## 5. Resultados experimentales y estadísticas (Sesión 16 de octubre de 2026)

Todos los CSV experimentales están incluidos en [`datos/mediciones/`](datos/mediciones/) y verificados mediante SHA-256 en [`datos/calibracion/sesion_2026-10-16_01/sesion.json`](datos/calibracion/sesion_2026-10-16_01/sesion.json):

| Conjunto de datos | Archivos CSV | Filas | Lecturas ADC (3 canales/fila) | Descripción |
|---|---:|---:|---:|---|
| **Principales de la sesión** | 10 | 181 | 543 | Todos los ensayos registrados del sensor 1 |
| **Incluidos en resumen preliminar** | 7 | 140 | 420 | 140 lecturas por sensor (solo S1 tiene inmersión comunicada; **0 alturas calibradas**) |
| **Excluidos del resumen** | 3 | 41 | 123 | `s1_seco_01` (20, ráfaga 2 ms), `s1_seco_02` (1, timeout previo), `s1_20mm_01` (20, salto 40,5 s) |
| **Preparación (separados)** | 5 | 20 | 60 | 4 muestras previas por condición húmeda |

### Resumen estadístico del Sensor 1 (`A0`) en los 7 ensayos seleccionados

| Ensayo | Inmersión comunicada | $n$ | Media ADC1 | Desv. muestral ($s$) | Mín.–Máx. | Rango | IQR | Cambio mitad final−inicial | Rol |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---|
| `s1_seco_03` | 0 mm (seco) | 20 | 7.00 | 0.00 | 7–7 | 0 | 0.00 | 0.00 | Referencia seca provisional |
| `s1_10mm_01` | 10 mm | 20 | 232.65 | 1.04 | 231–235 | 4 | 1.00 | +1.50 | Nodo exploratorio |
| `s1_20mm_02` | 20 mm | 20 | 266.20 | 2.46 | 260–271 | 11 | 2.25 | +1.80 | Nodo exploratorio |
| `s1_30mm_01` | 30 mm | 20 | 279.50 | 0.89 | 278–282 | 4 | 1.00 | +0.80 | Nodo exploratorio |
| `s1_40mm_01` | 40 mm | 20 | 298.10 | 0.91 | 297–300 | 3 | 2.00 | +1.40 | Nodo exploratorio |
| `s1_25mm_validacion_01` | 25 mm (descenso) | 20 | 283.40 | 0.88 | 282–285 | 3 | 1.00 | −1.00 | Validación reservada (predice **32.10 mm**, error **+7.10 mm**) |
| `s1_25mm_validacion_02` | 25 mm (repetición) | 20 | 246.80 | 11.40 | 228–261 | 33 | 19.50 | +16.60 | Validación inestable (predice **14.22 mm**, error **−10.78 mm**) |

- **Artefactos generados y verificados** en [`datos/calibracion/sesion_2026-10-16_01/analisis_rgb_02/`](datos/calibracion/sesion_2026-10-16_01/analisis_rgb_02/):
  - `auditoria.json` y `estadisticas.csv` (30 combinaciones ensayo/canal, rutas relativas portables).
  - `comparacion_tres_canales.png` (panel 7 ensayos × 3 canales).
  - `curva_exploratoria_sensor1.png` (curva interpolada de nodos S1 y discrepancia en las dos validaciones de 25 mm).
  - 7 gráficas individuales `adc_s1_*.png`.

---

## 6. Adquisición en vivo, ThingsBoard y QR

### Captura serial y graficación local

```bash
.venv/bin/python -m python.main puertos
.venv/bin/python -m python.main capturar --puerto /dev/ttyACM0 --baudios 115200 --muestras 100 --duracion 60 --salida datos/mediciones/ensayo_nuevo.csv
.venv/bin/python -m python.main cadencia --csv datos/mediciones/ensayo_nuevo.csv
.venv/bin/python -m python.main graficar --csv datos/mediciones/ensayo_nuevo.csv --salida graficas/adc_ensayo_nuevo.png
```

### Publicación HTTP a ThingsBoard y generación de QR

La captura ahora exige sincronización inicial con cuatro intervalos compatibles
con 500 ms reales y conserva un diagnóstico `.sesion.json`. No se registran las
líneas previas de preparación. Los reinicios probables, saltos temporales y silencio
terminan la sesión conservando el CSV parcial. La cadencia no demuestra la edad
física absoluta; véase la [auditoría de adquisición](documentos/AUDITORIA_ADQUISICION_2026-10-16.md).

Guardar servidor HTTPS, token y URL del dashboard **fuera del repositorio** en
`$HOME/.config/proyectosensorawa/thingsboard.json`. Para seguir la captura desde
otra terminal:

```bash
.venv/bin/python -m python.main thingsboard \
  --csv datos/mediciones/ensayo_nuevo.csv \
  --config "$HOME/.config/proyectosensorawa/thingsboard.json" \
  --modo en_vivo --seguir --duracion 90 \
  --cursor datos/resultados/ensayo_nuevo.tb.cursor.json
.venv/bin/python -m python.main qr \
  --config "$HOME/.config/proyectosensorawa/thingsboard.json" \
  --salida documentos/qr_dashboard_01.png --verificar
```

Publica `adc1`, `adc2`, `adc3` con UTC de recepción y conserva `t_ms` separado.
Sin calibración validada se omiten alturas. Las filas atrasadas se publican como
históricas con su UTC original. Un CSV cerrado utiliza `--modo historico`.
La red trabaja en otro proceso y el cursor permite recuperar pendientes.
**Dispositivo, dashboard y QR definitivo siguen requiriendo configuración real.**
Las instrucciones completas para crearlos, acceso desde teléfono y recuperación
están en [ThingsBoard y QR](documentos/THINGSBOARD_QR_PREPARACION.md).

---

## 7. Procedimiento de demostración para la exposición

1. **Demostración matemática y numérica (sin hardware):**
   Ejecutar `.venv/bin/python -m python.main resolver` y mostrar las tablas en `datos/resultados/comparacion.csv` junto con las 4 figuras en `graficas/` (`convergencia.png`, `residuos.png`, `niveles_iteraciones.png`, `comparacion_metodos.png`), explicando por qué Gauss-Seidel converge en 6 iteraciones frente a 9 de Jacobi y cómo Gauss-Jordan obtiene la solución exacta $(75/13, 115/13, 110/13)$.
2. **Demostración del análisis experimental reproducible:**
   Ejecutar `.venv/bin/python -m python.analisis_sesion --sesion datos/calibracion/sesion_2026-10-16_01/sesion.json --salida /tmp/demo_sesion` y presentar `comparacion_tres_canales.png` y `curva_exploratoria_sensor1.png`, explicando la diferencia entre las 420 lecturas ADC resumidas (140 por canal) y por qué la discrepancia en 25 mm (+7,10 mm y −10,78 mm por movimiento del sensor) impidió dar por validada la calibración.
3. **Verificación automatizada de calidad (QA):**
   Ejecutar `.venv/bin/python -m unittest discover -s tests -v` (suite completa con pseudoterminales, simulación nativa C++, servidores HTTP locales y QR; [registro final](documentos/PRUEBAS_ADQUISICION_2026-10-16.log)).

---

## 8. Documentación detallada y pendientes físicos

- **Informe de auditoría integral:** [`documentos/AUDITORIA_ANTIGRAVITY_2026-10-16.md`](documentos/AUDITORIA_ANTIGRAVITY_2026-10-16.md)
- **Modelo matemático y deducción:** [`documentos/MODELO.md`](documentos/MODELO.md)
- **Análisis ADC y clasificación RGB:** [`documentos/ANALISIS_ADC_Y_RGB_2026-10-16.md`](documentos/ANALISIS_ADC_Y_RGB_2026-10-16.md)
- **Bitácora de calibración exploratoria:** [`documentos/CALIBRACION_SESION_2026-10-16.md`](documentos/CALIBRACION_SESION_2026-10-16.md)
- **Diagnóstico y recuperación USB Serial:** [`documentos/DIAGNOSTICO_SERIAL_2026-10-16.md`](documentos/DIAGNOSTICO_SERIAL_2026-10-16.md)
- **Conexiones y revisión eléctrica de LED RGB:** [`documentos/CONEXIONES_LED.md`](documentos/CONEXIONES_LED.md)
- **Integración ThingsBoard y QR:** [`documentos/THINGSBOARD_QR_PREPARACION.md`](documentos/THINGSBOARD_QR_PREPARACION.md)
- **Resumen preliminar de entrega:** [`documentos/RESUMEN_PRELIMINAR_ENTREGA_2026-10-16.md`](documentos/RESUMEN_PRELIMINAR_ENTREGA_2026-10-16.md)

### Alcance de la entrega actual

Los LED RGB y sus resistencias fueron retirados por el equipo; no se requiere
activarlos ni modificar firmware. La calibración exploratoria sigue sin validar,
por lo que la demostración usa cuentas ADC. No se repiten mediciones con agua.
El equipo ya creó dispositivo y dashboard en ThingsBoard Cloud; se comprobó la
captura corregida en el USB real (6 muestras, mediana 501,128 ms). Falta introducir
el token privado y verificar envío, vista del dashboard y URL desde el teléfono.
Continuar con [Sensor Awa en Cloud](documentos/SENSOR_AWA_THINGSBOARD_CLOUD.md).
La generación y lectura
de QR de prueba ya se verifican en el entorno virtual.
