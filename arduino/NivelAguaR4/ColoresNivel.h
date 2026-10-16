#pragma once
#include <stdint.h>

// Bits de canales RGB: R=1, G=2, B=4. No contienen números de pines.
enum ColorNivel : uint8_t {
  COLOR_APAGADO = 0,
  COLOR_ROJO = 1,
  COLOR_VERDE = 2,
  COLOR_AZUL = 4,
  COLOR_MORADO = 5
};

inline bool pinesLedValidos(const int pines[3][3], const int reservados[5]) {
  for (uint8_t i = 0; i < 3; ++i) {
    for (uint8_t canal = 0; canal < 3; ++canal) {
      const int pin = pines[i][canal];
      // Esta instalación reserva D2..D10 para los nueve canales RGB.
      if (pin < 2 || pin > 10) return false;
      for (uint8_t r = 0; r < 5; ++r) {
        if (pin == reservados[r]) return false;
      }
      for (uint8_t anterior = 0; anterior < i * 3 + canal; ++anterior) {
        if (pin == pines[anterior / 3][anterior % 3]) return false;
      }
    }
  }
  return true;
}

inline uint8_t colorParaAdc(int adc) {
  // Clasificación provisional en cuentas ADC; no expresa altura ni porcentaje.
  if (adc < 0 || adc > 1023) return COLOR_APAGADO;
  if (adc < 50) return COLOR_VERDE;
  if (adc < 150) return COLOR_AZUL;
  if (adc < 300) return COLOR_MORADO;
  return COLOR_ROJO;
}
