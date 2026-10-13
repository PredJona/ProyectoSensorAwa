# Escáner I²C — UNO R4 WiFi

## Resultado real después de corregir el cableado

El usuario confirmó haber realizado el cambio propuesto: sensor 1 A0,
sensor 2 A2, sensor 3 A3; LCD SDA A4 y SCL A5, con alimentación indicada
de 5 V y GND compartido. No hubo inspección visual de los cables por el agente.

El 12 octubre 2026 se reconoció la UNO R4 WiFi en `/dev/ttyACM0`, se compiló
y cargó el escáner autorizado y se abrió el monitor a 115200. **Se detectó
una dirección con ACK: `0x27`**, repetida en seis recorridos completos legibles,
cada uno con **un dispositivo y cero errores I²C**. Hubo caracteres ilegibles
iniciales al abrir el monitor; las lecturas posteriores fueron estables.

Esto verifica comunicación en el bus Wire; para confirmar definitivamente que
el dispositivo es la LCD y que su biblioteca/mapeo funcionan, falta mostrar
texto en pantalla. No verifica los sensores ni los LED.
El monitor se cerró con Ctrl+C. Al terminar esa prueba quedó ejecutándose
el escáner; los archivos del firmware principal no se modificaron durante
el escaneo. Posteriormente se integró y cargó el firmware principal:
[registro de integración](../../documentos/INTEGRACION_R4_2026-10-12.md).
Registro: [ESCANEO_I2C_2026-10-12.txt](../../documentos/ESCANEO_I2C_2026-10-12.txt).

Los apartados de propuesta y preparación siguientes conservan el contexto
previo al cambio de cables y a la integración posterior.

Sketch independiente que usa únicamente `Wire.h` y el core Arduino.
Busca las direcciones de 7 bits **0x01 a 0x7E**, inclusive, y repite cada
tres segundos después de finalizar cada recorrido. Serial: **115200 baudios**.
No modifica los archivos `NivelAguaR4.ino` ni `sensores.ino`.

## Cableado que debe confirmarse

En esta placa, **Wire usa SDA/A4 y SCL/A5**, incluidos los pines de cabecera
rotulados SDA/SCL. El conector Qwiic pertenece a Wire1 y no se escanea aquí.
No se pueden usar A0/A1 como SDA/SCL con este sketch. Fuente:
[manual Arduino UNO R4 WiFi](https://docs.arduino.cc/tutorials/uno-r4-wifi/cheat-sheet/),
contrastado con `variants/UNOWIFIR4/pins_arduino.h` del core instalado.

Confirmar dónde llegan los cables SDA, SCL, VCC y GND de la LCD, su tensión
nominal y masa común. Si un Water Level usa A4, aclarar el cableado antes de
cargar: ese pin está compartido con SDA. No se cambió ninguna conexión.

El usuario confirmó las siguientes conexiones actuales:

| Elemento | Conexión actual |
|---|---|
| Señal sensor 1 | A4 |
| Señal sensor 2 | A2 |
| Señal sensor 3 | A3 |
| LCD SDA | A1 |
| LCD SCL | A0 |
| Alimentación indicada | 5 V y GND compartido |

Este cableado no corresponde al bus Wire del escáner. A4 está ocupado por
el sensor 1. No se ha cargado el escáner ni cambiado las conexiones.

Propuesta pendiente de autorización y ejecución física por el equipo, con la
placa sin alimentación: mover LCD SDA de A1 a A4, LCD SCL de A0 a A5 y la
señal del sensor 1 de A4 a A0. Mantener sensor 2 en A2 y sensor 3 en A3.
Antes de hacerlo, comprobar que A0 queda libre y no lo usa ningún LED u otro
periférico. No mover alimentación ni masas. El resultado propuesto es:

| Elemento | Conexión propuesta |
|---|---|
| Señal sensor 1 | A0 |
| Señal sensor 2 | A2 |
| Señal sensor 3 | A3 |
| LCD SDA | A4 / SDA |
| LCD SCL | A5 / SCL |

Solo tras confirmar la realización de ese cambio se podrá cargar y ejecutar
este escáner sobre Wire. El firmware principal permanece sin modificar:
para la siguiente integración necesitará ajustar sus sensores a A0/A2/A3 si
se adopta esta propuesta. La dirección LCD sigue pendiente de medición.

El usuario también indicó LED RGB de cátodo común, resistencia «220»
(confirmar ohmios y una resistencia por canal) y estados: vacío morado,
bajo verde, medio amarillo, alto rojo. Faltan pines RGB y umbrales medidos.
Estos datos se reservan para la siguiente integración, no para el escáner.

## Comandos en la terminal integrada de VS Code

Ejecutar desde la raíz de `Proyecto1`:

```bash
arduino-cli version
arduino-cli core list
arduino-cli board list
XDG_CACHE_HOME=/tmp/proyecto1-r4-cache arduino-cli compile --fqbn arduino:renesas_uno:unor4wifi --build-path /tmp/proyecto1-escaner-i2c-build arduino/EscanerI2C
```

Cuando el cableado esté confirmado y se vaya a realizar esta prueba,
cerrar monitores del IDE y la captura Python. Cargar el escáner reemplaza el
programa que se ejecuta en la placa; conserva los archivos del firmware
principal en disco. No se cambia el cableado mediante estos comandos.

```bash
arduino-cli upload --fqbn arduino:renesas_uno:unor4wifi --port /dev/ttyACM0 --input-dir /tmp/proyecto1-escaner-i2c-build arduino/EscanerI2C
arduino-cli monitor --port /dev/ttyACM0 --config baudrate=115200
```

`/dev/ttyACM0` es el puerto reconocido en esta sesión. Repetir `board list`
si cambia al reconectar. Salir del monitor con **Ctrl+C**.
No hace falta usar `sudo`, instalar paquetes globales ni cambiar grupos o
permisos del sistema para intentar estos comandos. Si hay un error real,
conservar su texto antes de decidir cómo resolverlo.

## Interpretar el resultado

Anotar exactamente cada línea `Dispositivo I2C encontrado en ...`.
No se asigna una dirección predeterminada a la LCD. Si hay varios dispositivos,
identificar cuál corresponde a la pantalla usando el módulo y el circuito.
Una respuesta ACK confirma una dirección del bus, no el modelo del dispositivo.

`Sin dispositivos detectados.` significa que no hubo ACK durante ese recorrido.
Revisar alimentación, masa, bus y cableado; no demuestra que la LCD esté dañada.
El sketch imprime los códigos de error devueltos por Wire salvo el NACK de
dirección (2), habitual al explorar direcciones sin dispositivo.
En el core Renesas 1.6.0 instalado: 1 = datos demasiado largos, 3 = NACK de datos,
4 = error FSP/controlador, 5 = timeout, 6 = bus sin inicializar.
Se establece un timeout de 25000 microsegundos por transacción.

La prueba automatizada usa un bus simulado y direcciones controladas; sus
salidas **no son direcciones detectadas en la placa real**:

```bash
.venv/bin/python -m unittest discover -s tests -v
```

## Volver al firmware principal

Primero conservar la salida real del escáner y confirmar los pines de sensores,
LCD y LED. La integración y carga del firmware principal se harán después.
Si el firmware principal ya está configurado y se desea restaurarlo, cerrar
el monitor y compilar/cargar explícitamente ese sketch:

```bash
XDG_CACHE_HOME=/tmp/proyecto1-r4-cache arduino-cli compile --fqbn arduino:renesas_uno:unor4wifi --build-path /tmp/proyecto1-r4-build arduino/NivelAguaR4
arduino-cli upload --fqbn arduino:renesas_uno:unor4wifi --port /dev/ttyACM0 --input-dir /tmp/proyecto1-r4-build arduino/NivelAguaR4
```

El principal todavía tiene A0/A1/A2 provisionales y LCD/LED desactivados;
restaurarlo no resuelve las conexiones pendientes.

## Registro previo de preparación — antes de corregir los cables

- `arduino-cli` 1.5.1 instalado; core `arduino:renesas_uno` 1.6.0 instalado.
- La primera detección dentro del aislamiento falló con
  `Cannot START_SYNC: operation not permitted` y
  `Cannot START_SYNC: can't open libusb: Other error`. No era evidencia de
  ausencia de la placa. Al repetir con permiso de acceso USB se reconoció
  **Arduino UNO R4 WiFi**, `/dev/ttyACM0`, FQBN `arduino:renesas_uno:unor4wifi`.
- Compilación del escáner: salida 0; 58164 bytes de programa y 8988 bytes
  de variables globales. No requiere biblioteca LCD.
- Suite completa: 33 pruebas, 32 aprobadas y una omitida por qrcode/OpenCV.
  La prueba del escáner pasó con bus simulado; no usa el USB físico.
- Se comprobaron las huellas SHA-256 de ambos sketches anteriores antes y
  después: permanecen intactos.
- **No se cargó el escáner ni se abrió el monitor**: el cableado confirmado
  usa A4 para un sensor y A1/A0 para SDA/SCL, incompatible con este bus Wire.
  La dirección LCD sigue **sin medir**. El cambio de conexiones propuesto
  requiere autorización y ejecución física por el equipo antes de continuar.
