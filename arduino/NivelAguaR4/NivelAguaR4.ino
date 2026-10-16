// Proyecto 1: adquisición ADC para Arduino UNO R4 WiFi.
// Adaptado de ../sensores/sensores.ino; ese sketch se conserva como referencia.
#include <Arduino.h>
#include "ColoresNivel.h"

#if !defined(ARDUINO_UNOR4_WIFI)
#error "Seleccione Arduino UNO R4 WiFi (arduino:renesas_uno:unor4wifi)."
#endif

// Cableado confirmado por el equipo después de liberar A4 para SDA.
const int PINES_SENSORES[3] = {A0, A2, A3};
const uint32_t INTERVALO_MS = 500;
static_assert(INTERVALO_MS > 0, "El intervalo debe ser positivo.");
uint32_t ultimoMuestreo = 0;

// LCD: SDA/A4, SCL/A5; dirección medida con EscanerI2C el 12 octubre 2026.
// Biblioteca: LiquidCrystal_I2C 2.0.0, Martin Kubovcik / Frank de Brabander.
// Usa Wire (SDA/A4 y SCL/A5 en R4 WiFi), no el conector Qwiic/Wire1.
#ifndef NIVEL_AGUA_LCD
#define NIVEL_AGUA_LCD 1
#endif
#ifndef NIVEL_AGUA_LCD_DIRECCION
#define NIVEL_AGUA_LCD_DIRECCION 0x27
#endif

#if NIVEL_AGUA_LCD
#if NIVEL_AGUA_LCD_DIRECCION < 0x08 || NIVEL_AGUA_LCD_DIRECCION > 0x77
#error "Defina NIVEL_AGUA_LCD_DIRECCION con la dirección I2C real confirmada."
#endif
#include <Wire.h>
#include <LiquidCrystal_I2C.h>
#include <stdio.h>
LiquidCrystal_I2C lcd(NIVEL_AGUA_LCD_DIRECCION, 16, 2);
bool lcdDisponible = false;
#endif

// RGB de cátodo común: canales R, G, B; encendido con HIGH.
// Orden recibido: LED 1 D2/D3/D4 (R/G/B); LED 2 D5/D6/D7 (B/G/R);
// LED 3 D8/D9/D10 (B/G/R). La tabla conserva el orden R/G/B.
const int PINES_LED[3][3] = {{2, 3, 4}, {7, 6, 5}, {10, 9, 8}};
const int PINES_RESERVADOS_LED[5] = {A0, A2, A3, SDA, SCL};
const int NIVELES_ACTIVOS_LED[3] = {HIGH, HIGH, HIGH};
// Activar solo tras verificar cátodo común, resistencias y corriente por canal.
// Compilar con -DNIVEL_AGUA_LED=1 para la prueba física autorizada posterior.
#ifndef NIVEL_AGUA_LED
#define NIVEL_AGUA_LED 0
#endif
#if NIVEL_AGUA_LED != 0 && NIVEL_AGUA_LED != 1
#error "NIVEL_AGUA_LED debe ser 0 o 1."
#endif

void escribirCanalLed(uint8_t indicador, uint8_t canal, bool encendido) {
  if (indicador >= 3 || canal >= 3) return;
  const int pin = PINES_LED[indicador][canal];
  const int activo = NIVELES_ACTIVOS_LED[indicador];
  if (pin < 0 || (activo != HIGH && activo != LOW)) return;
  digitalWrite(pin, encendido ? activo : (activo == HIGH ? LOW : HIGH));
}

void inicializarLeds() {
  // Con NIVEL_AGUA_LED=0 se configuran los 9 pines en OUTPUT LOW (0 V activo),
  // no en alta impedancia (INPUT). Esto mantiene apagados LED de cátodo común
  // a GND, pero drenaría corriente si existiera conexión a +5 V (ánodo común).
  if (!pinesLedValidos(PINES_LED, PINES_RESERVADOS_LED)) return;
  for (uint8_t indicador = 0; indicador < 3; ++indicador) {
    if (NIVELES_ACTIVOS_LED[indicador] != HIGH &&
        NIVELES_ACTIVOS_LED[indicador] != LOW) continue;
    for (uint8_t canal = 0; canal < 3; ++canal) {
      const int pin = PINES_LED[indicador][canal];
      if (pin < 0) continue;
      escribirCanalLed(indicador, canal, false);
      pinMode(pin, OUTPUT);
    }
  }
}


void actualizarLeds(const int lecturas[3]) {
  // Cada canal ADC controla su RGB: verde, azul, morado o rojo.
  if (!pinesLedValidos(PINES_LED, PINES_RESERVADOS_LED)) return;
  for (uint8_t indicador = 0; indicador < 3; ++indicador) {
    const uint8_t color = NIVEL_AGUA_LED ? colorParaAdc(lecturas[indicador])
                                        : static_cast<uint8_t>(COLOR_APAGADO);
    for (uint8_t canal = 0; canal < 3; ++canal) {
      escribirCanalLed(indicador, canal, (color & (1u << canal)) != 0);
    }
  }
}

void inicializarLcd() {
#if NIVEL_AGUA_LCD
  Wire.begin();
  Wire.setWireTimeout(25000);  // Microsegundos; acotar esperas del bus.
  Wire.beginTransmission(NIVEL_AGUA_LCD_DIRECCION);
  if (Wire.endTransmission() != 0) return;  // Sin ACK: continuar adquisición.
  lcd.init();
  lcd.backlight();
  lcdDisponible = true;
#endif
}

void actualizarLcd(const int lecturas[3]) {
#if NIVEL_AGUA_LCD
  if (!lcdDisponible) return;
  char fila[17];
  // Se sobrescriben las 16 columnas para borrar dígitos anteriores sin parpadeo.
  snprintf(fila, sizeof(fila), "S1:%4d S2:%4d ", lecturas[0], lecturas[1]);
  lcd.setCursor(0, 0);
  lcd.print(fila);
  snprintf(fila, sizeof(fila), "S3:%4d ADC     ", lecturas[2]);
  lcd.setCursor(0, 1);
  lcd.print(fila);
#else
  (void)lecturas;
#endif
}

void setup() {
  analogReadResolution(10);  // UNO R4: fijar explícitamente 0..1023.
  Serial.begin(115200);     // USB serial; no Serial1 ni WiFi.
  // No esperar indefinidamente al PC: los periféricos funcionan sin monitor.
  Serial.println("tiempo_ms,sensor1,sensor2,sensor3");
  inicializarLeds();
  inicializarLcd();
}

void loop() {
  const uint32_t ahora = millis();
  // Resta de 32 bits: mantiene la cadencia al desbordarse millis().
  if (static_cast<uint32_t>(ahora - ultimoMuestreo) < INTERVALO_MS) return;
  ultimoMuestreo = ahora;

  // Lecturas consecutivas, no simultáneas; el tiempo marca el inicio del grupo.
  const int lecturas[3] = {analogRead(PINES_SENSORES[0]),
                           analogRead(PINES_SENSORES[1]),
                           analogRead(PINES_SENSORES[2])};
  Serial.print(ahora);
  for (uint8_t i = 0; i < 3; ++i) {
    Serial.print(',');
    if (i < 2) Serial.print(lecturas[i]);
    else Serial.println(lecturas[i]);
  }
  actualizarLcd(lecturas);
  actualizarLeds(lecturas);
}
