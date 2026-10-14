#pragma once
#include <stdint.h>

// Bits de canales RGB: R=1, G=2, B=4. No contienen números de pines.
enum ColorNivel : uint8_t {
  COLOR_APAGADO = 0,
  COLOR_ROJO = 1,
  COLOR_VERDE = 2,
  COLOR_AMARILLO = 3,
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

inline uint8_t colorParaAdc(int adc, const int limites[3]) {
  // Máximos ADC de vacío, bajo y medio, medidos por sensor.
  // Esta política requiere una respuesta creciente con el nivel de agua.
  if (adc < 0 || adc > 1023 || limites[0] < 0 ||
      limites[0] >= limites[1] || limites[1] >= limites[2] ||
      limites[2] > 1023) return COLOR_APAGADO;
  if (adc <= limites[0]) return COLOR_MORADO;
  if (adc <= limites[1]) return COLOR_VERDE;
  if (adc <= limites[2]) return COLOR_AMARILLO;
  return COLOR_ROJO;
}
