// Prueba independiente de LCD 16x2 I2C para Arduino UNO R4 WiFi.
// Restaurar NivelAguaR4.ino tras el diagnóstico.
#include <Arduino.h>
#include <Wire.h>
#include <LiquidCrystal_I2C.h>

#if !defined(ARDUINO_UNOR4_WIFI)
#error "Seleccione Arduino UNO R4 WiFi (arduino:renesas_uno:unor4wifi)."
#endif

constexpr uint8_t DIRECCION_LCD = 0x27;
LiquidCrystal_I2C lcd(DIRECCION_LCD, 16, 2);
uint8_t respuestaInicial = 255;
uint8_t respuestaTardia = 255;
bool lcdInicializada = false;

uint8_t consultarLcd() {
  Wire.beginTransmission(DIRECCION_LCD);
  return Wire.endTransmission();
}

void setup() {
  Serial.begin(115200);
  Wire.begin();  // UNO R4 WiFi: SDA/A4, SCL/A5.
  Wire.setWireTimeout(25000);
  respuestaInicial = consultarLcd();
  delay(1500);
  respuestaTardia = consultarLcd();

  if (respuestaTardia == 0) {
    lcd.init();
    lcd.backlight();
    lcd.setCursor(0, 0);
    lcd.print("LCD OK 0x27");
    lcd.setCursor(0, 1);
    lcd.print("Prueba de texto");
    lcdInicializada = true;
  }
}

void loop() {
  Serial.print("I2C_0x27_inicio=");
  Serial.print(respuestaInicial);
  Serial.print(",tarde=");
  Serial.print(respuestaTardia);
  Serial.print(",ahora=");
  Serial.print(consultarLcd());
  Serial.print(",lcd_inicializada=");
  Serial.println(lcdInicializada ? 1 : 0);
  delay(3000);
}
