# Estado actual y cierre de la auditoría correctiva

**Actualización del 16 de octubre:** la sesión USB quedó resuelta y se
adquirieron ensayos exploratorios con los tres canales, con alturas comunicadas
solo para sensor 1. La calibración sigue sin validar por profundidad variable.
La política RGB actual del repositorio es 0–49 verde, 50–149 azul, 150–299
morado, 300–1023 rojo; sustituye `LIMITES_ADC_LED`. Está probada y compilada,
pero no cargada y con `NIVEL_AGUA_LED=0` por defecto hasta revisar resistencias.
Véase [ANALISIS_ADC_Y_RGB_2026-10-16.md](ANALISIS_ADC_Y_RGB_2026-10-16.md).
Las referencias a límites en -1 y ausencia de ensayos de los apartados siguientes
describen el estado previo, no la implementación vigente del repositorio.

## Alcance de la evidencia

El firmware principal de UNO R4 WiFi usa A0/A2/A3, ADC de 10 bits,
USB a 115200 baudios y LCD I²C 16×2 en 0x27. El equipo confirmó que la
LCD muestra lecturas: la aparente falla anterior se debió a no reconocer
cuándo terminó la carga del firmware. El equipo también informó pruebas
físicas de los tres sensores, lecturas ADC diferentes y tres recipientes
montados con tubos. Las dos [fotografías recibidas](evidencias/LEEME.md)
están incorporadas y se revisaron visualmente: muestran los tres recipientes,
tubos, LCD con caracteres y puntos luminosos. No se asignan a esas fotos
fechas, alturas, lecturas ni condiciones de inmersión.

Las capturas CSV locales conservan cuentas ADC reales y horas de recepción
UTC. En la sesión del 16 de octubre (`datos/calibracion/sesion_2026-10-16_01/`)
se adquirieron 10 ensayos principales del sensor 1 (181 filas / 543 lecturas ADC;
7 ensayos resumidos con 140 filas / 420 lecturas ADC y 3 intentos excluidos con
41 filas), más 5 archivos de preparación (20 filas). Las alturas comunicadas
para S1 (0, 10, 20, 30, 40 mm y dos validaciones a 25 mm) mostraron discrepancia
en 25 mm (+7,10 mm y −10,78 mm) y movimiento físico del sensor, por lo que la
conversión ADC–altura se mantiene como exploratoria y no validada.
Las luces observadas en fotografías previas no demuestran el control de los
tres LED RGB; con `NIVEL_AGUA_LED=0` por defecto, el firmware mantiene los
nueve pines D2..D10 en `OUTPUT` `LOW`.

| Estado | Funcionalidad y límite de la evidencia |
|---|---|
| Implementado | Tres métodos académicos (`jacobi`, `gauss_seidel`, `gauss_jordan`), CSV y PNG académicos, receptor serial, interpolación por sensor, analizador reproducible de sesión (`analisis_sesion.py`), publicador HTTP ThingsBoard con cursor y reintentos (`thingsboard.py`), validador de URL QR (`qr.py`), política LED RGB (`ColoresNivel.h`) y LCD (`0x27`). |
| Probado con datos controlados | Suite ampliada: sincronización serial con reloj virtual y pseudoterminal a 500 ms reales, HTTP simulado con recuperación/cursor, prueba conjunta de red lenta y QR generado/decodificado. Véase [registro final](PRUEBAS_ADQUISICION_2026-10-16.log). Las compilaciones reales de variantes citadas anteriormente son evidencia previa; en esta intervención no se compila/carga firmware a la placa. |
| Comprobado físicamente o comunicado por el equipo | Placa UNO R4 WiFi y escaneo I²C `0x27`; recuperación USB y carga del firmware base; 10 ensayos exploratorios de S1 y verificaciones del 16 de octubre; fotografías del montaje y LCD visible. |
| Comprobación actual de Cloud | Captura nueva en `/dev/ttyACM0`: 6 muestras reales, mediana UTC 501,834 ms, sin discontinuidades. Se aceptaron 6/6 filas en cuatro lotes HTTP 2xx; la última fila coincide con **Latest telemetry** vista por el equipo. Configuración privada fuera de Git. Véase [verificación real](VERIFICACION_ENVIO_REAL_2026-10-16.json) y [procedimiento Cloud](SENSOR_AWA_THINGSBOARD_CLOUD.md). |
| Pendiente para esta entrega | Completar widgets del dashboard y verificar su URL en el teléfono para generar el QR. Dispositivo y dashboard ya creados por el equipo. La demostración usa ADC sin alturas; los RGB fueron retirados por el equipo. |

## Procedencia y reproducibilidad

En `datos/mediciones/` se versionan explícitamente mediante excepciones en
`.gitignore` 19 archivos CSV experimentales verificados con SHA-256:
- Las 5 capturas históricas del 12 de octubre de 2026.
- Los 10 CSV principales de la sesión `sesion_2026-10-16_01` (`calibracion_sesion_2026-10-16_01_s1_*.csv`).
- Las 4 capturas de verificación y diagnóstico serial del 16 de octubre de 2026.

Los datos originales nunca se sobrescriben. El analizador
`python -m python.analisis_sesion` verifica estructura, orden temporal UTC y
huellas SHA-256, y exporta estadísticas y gráficas usando únicamente rutas
relativas portables (sin rutas absolutas de la máquina local), incluyendo la
curva exploratoria y discrepancia de validación en
`datos/calibracion/sesion_2026-10-16_01/analisis_rgb_02/curva_exploratoria_sensor1.png`.

Las cuatro gráficas académicas se regeneran con `python -m python.main resolver`.
El resumen académico y la auditoría de sesión usan rutas relativas portables.

## Modelo y cierre físico pendiente

La matriz A y el vector b son los del ejercicio del profesor. Jacobi y
Gauss-Seidel calculan sus aproximaciones; Gauss-Jordan da la solución directa
de referencia del sistema. Los residuos verifican las ecuaciones académicas,
no la hidráulica del montaje. Los tubos visibles confirman conexiones de
montaje según el equipo, pero aún faltan geometría, comportamiento del flujo,
unidades y parámetros medidos para relacionar A y b con el circuito.

Para la entrega actual no se repiten mediciones con agua ni se activan LED.
La calibración física sigue fuera de validación; no se publican alturas.
El capturador sincroniza antes del inicio efectivo y conserva sesiones parciales
ante fallos. La causa de aceptar ráfagas y sus límites de frescura se documentan en
[AUDITORIA_ADQUISICION_2026-10-16.md](AUDITORIA_ADQUISICION_2026-10-16.md).
Configurar credenciales fuera del repositorio y seguir el procedimiento de
[THINGSBOARD_QR_PREPARACION.md](THINGSBOARD_QR_PREPARACION.md).
