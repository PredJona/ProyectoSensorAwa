# Diagnóstico LCD I²C

Sketch temporal para la LCD de dirección 0x27 detectada por el escáner del
proyecto. Comprueba si hay respuesta I²C justo al arrancar y 1,5 segundos
después. Si responde, escribe texto fijo en la pantalla. El monitor serie
repite a 115200 baudios los códigos de respuesta: `0` significa ACK.
La comunicación con el módulo I²C no demuestra que el panel LCD muestre
caracteres; contraste, alimentación del panel y conexiones del módulo deben
comprobarse visualmente.

Desde la raíz del repositorio:

```bash
XDG_CACHE_HOME=/tmp/proyecto1-r4-cache arduino-cli compile --fqbn arduino:renesas_uno:unor4wifi --build-path /tmp/proyecto1-lcd-diagnostico-build arduino/DiagnosticoLCD
arduino-cli upload --fqbn arduino:renesas_uno:unor4wifi --port /dev/ttyACM0 --input-dir /tmp/proyecto1-lcd-diagnostico-build arduino/DiagnosticoLCD
arduino-cli monitor --port /dev/ttyACM0 --fqbn arduino:renesas_uno:unor4wifi --config baudrate=115200 --quiet
```

Después de la prueba, volver a cargar `arduino/NivelAguaR4` siguiendo su
README. Este sketch no lee sensores ni ejecuta los indicadores LED.
