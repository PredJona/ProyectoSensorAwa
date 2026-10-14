# Diagnóstico de LCD en blanco — 12 octubre 2026

**Resolución posterior comunicada por el equipo:** la LCD funciona y muestra
lecturas. La interpretación inicial de pantalla en blanco ocurrió porque no
se identificó correctamente cuándo terminaba la carga del firmware. Se
conserva debajo el diagnóstico histórico, sin atribuir la observación visual
al escáner I²C ni a este registro serial.

El usuario informó que la LCD no muestra nada. El firmware principal sí
seguía enviando CSV por USB a 115200: seis muestras válidas, sin líneas
inválidas. En esa captura S1 marcó 464..466, S2 3..4 y S3 3..4; estos
valores difieren de la captura anterior cercana a 994. No se registró el
estado del agua durante ambas capturas, así que no se usan para calibrar.

El escáner I²C independiente encontró de nuevo un único dispositivo en
`0x27` sobre Wire/SDA-A4/SCL-A5, repetidamente y con cero errores. Después
se restauró el firmware principal.

Se preparó y cargó temporalmente `arduino/DiagnosticoLCD/DiagnosticoLCD.ino`.
Compiló para `arduino:renesas_uno:unor4wifi`; el monitor mostró repetidamente:

```text
I2C_0x27_inicio=0,tarde=0,ahora=0,lcd_inicializada=1
```

El código `0` significa que el módulo I²C respondió incluso en la primera
consulta, y el sketch ejecutó `lcd.init()`, `lcd.backlight()` y la escritura
de texto fijo. Esto descarta una ausencia persistente de respuesta I²C y
no apoya la hipótesis de que el módulo solo responda tarde tras el arranque.
La respuesta I²C no demuestra que el panel LCD muestre caracteres.

Pendiente de observación por el usuario: comprobar si se ve el texto
`LCD OK 0x27` / `Prueba de texto`, si hay luz de fondo o si aparecen bloques
oscuros. Si hay luz pero no caracteres, comprobar el ajuste de contraste del
potenciómetro del módulo I²C antes de cambiar código o conexiones.
Posteriormente se restauró `arduino/NivelAguaR4` en la placa para probar el
sensor 2. La observación visual de la pantalla sigue pendiente.
