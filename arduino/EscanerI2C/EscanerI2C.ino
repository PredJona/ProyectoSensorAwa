// Diagnóstico independiente. No contiene el firmware de adquisición.
// UNO R4 WiFi: Wire usa SDA/A4 y SCL/A5, no A0/A1 ni Qwiic/Wire1.
// Confirmar que esos pines están destinados al bus antes de cargar.
#include <Arduino.h>
#include <Wire.h>

#if !defined(ARDUINO_UNOR4_WIFI)
#error "Seleccione Arduino UNO R4 WiFi (arduino:renesas_uno:unor4wifi)."
#endif

void imprimirDireccion(uint8_t direccion) {
  Serial.print("0x");
  if (direccion < 0x10) Serial.print('0');
  Serial.print(static_cast<unsigned int>(direccion), HEX);
}

void setup() {
  Serial.begin(115200);
  Wire.begin();
  Wire.setClock(100000);
  Wire.setWireTimeout(25000);  // Timeout por transacción, en microsegundos.
}

void loop() {
  Serial.println("Escaneo Wire: SDA/A4, SCL/A5; direcciones 0x01..0x7E");
  unsigned int encontrados = 0;
  unsigned int errores = 0;

  for (uint8_t direccion = 0x01; direccion <= 0x7E; ++direccion) {
    Wire.beginTransmission(direccion);
    const uint8_t resultado = Wire.endTransmission();

    if (resultado == 0) {
      Serial.print("Dispositivo I2C encontrado en ");
      imprimirDireccion(direccion);
      Serial.println();
      ++encontrados;
    } else if (resultado != 2) {
      // Código 2: NACK, ninguna respuesta; es normal al buscar direcciones.
      Serial.print("Error I2C en ");
      imprimirDireccion(direccion);
      Serial.print(": codigo ");
      Serial.println(static_cast<unsigned int>(resultado));
      ++errores;
    }
  }

  if (encontrados == 0) Serial.println("Sin dispositivos detectados.");
  Serial.print("Dispositivos: ");
  Serial.print(encontrados);
  Serial.print("; errores: ");
  Serial.println(errores);
  Serial.println("Un ACK identifica una direccion; confirmar que sea la LCD.");
  Serial.println();
  delay(3000);  // Repite para permitir abrir el monitor después del arranque.
}
