# Estado actual y cierre de la auditoría correctiva

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
UTC. Sus valores no establecen niveles de agua porque no se anotaron alturas
ni condiciones de ensayo suficientes. La plantilla de calibración está vacía.
Las luces observadas en el montaje no demuestran que el firmware controle
correctamente cada canal de los tres LED RGB. Con `LIMITES_ADC_LED=-1`, la
versión actual ordena apagar los canales; se debe comprobar qué programa
estaba cargado y el cableado antes de interpretar las luces.

| Estado | Funcionalidad y límite de la evidencia |
|---|---|
| Implementado | Tres métodos académicos, CSV y PNG, receptor serial, interpolación por sensor, política LED y LCD. |
| Probado con datos controlados | Métodos, casos límite, parser serial, muestreo, LCD y colores mediante simulación nativa del sketch. |
| Comprobado físicamente o comunicado por el equipo | Placa y escaneo I²C 0x27 registrados; capturas ADC por USB; fotografías del montaje y LCD visible; pruebas de sensores comunicadas por el equipo. |
| Pendiente | Alturas medidas, calibración independiente, respuesta de cada sensor a niveles conocidos, colores RGB por pin y validación del modelo académico frente al circuito. |

## Procedencia y reproducibilidad

Los cinco CSV históricos en `datos/mediciones/` son capturas experimentales
sin altura documentada. La excepción explícita en `.gitignore` permite
conservarlos junto con las gráficas; nuevos CSV permanecen excluidos hasta
revisar su procedencia. No cambiar los datos originales. El archivo
`ensayo_r4_2026-10-12_verificacion_final.metadata.json` conserva la huella
SHA-256 de su CSV; la huella coincide con el archivo disponible.

Las cuatro gráficas académicas se regeneran con `python -m python.main resolver`.
Las gráficas ADC existentes son experimentales en cuentas ADC, no en altura.
El resumen académico usa rutas relativas a la carpeta de salida para evitar
referencias a una computadora concreta. No se ha construido una curva temporal
de altura experimental.

## Modelo y cierre físico pendiente

La matriz A y el vector b son los del ejercicio del profesor. Jacobi y
Gauss-Seidel calculan sus aproximaciones; Gauss-Jordan da la solución de
referencia del sistema. Los residuos verifican las ecuaciones académicas,
no la hidráulica del montaje. Los tubos visibles confirman conexiones de
montaje según el equipo, pero aún faltan geometría, comportamiento del flujo,
unidades y parámetros medidos para relacionar A y b con el circuito.

Prioridad para el equipo:

1. Identificar qué ensayo corresponde a cada fotografía, si el equipo
   conserva esa información; no inferir condiciones a partir de la imagen.
2. Verificar físicamente cada sensor A0/A2/A3 al variar solo su recipiente;
   anotar alimentación, montaje y respuesta observada.
3. Definir el origen y la unidad de altura; medir varias alturas reales con
   regla y lecturas repetidas para cada sensor. Guardar un CSV nuevo por
   condición y completar `datos/calibracion/plantilla_puntos.csv`.
4. Revisar dispersión y monotonicidad; generar el JSON de pares medidos y
   validar interpolación y ausencia de extrapolación en los tres sensores.
5. Definir estados de altura y obtener de las mediciones los tres límites
   ADC por sensor. Comprobar resistencias y cada pin/color RGB. Solo entonces
   configurar `LIMITES_ADC_LED`, compilar y solicitar autorización antes de
   cargar firmware.
6. Medir geometría y comportamiento hidráulico para juzgar si el sistema
   académico puede representar el montaje. Confirmar con el profesor rúbrica,
   necesidad de eliminación de Gauss o Doolittle, función del QR y formato
   de la entrega.

El trabajo delegable sin circuito incluye validar los CSV y pares ADC-altura
que entregue el equipo, generar
gráficas calibradas, comparar mediciones con un modelo físico justificado y
preparar el informe final. Los registros fechados anteriores permanecen
como historia de las etapas de integración.
