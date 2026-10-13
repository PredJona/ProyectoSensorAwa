"""Escáner con bus simulado: no obtiene direcciones del circuito real."""
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

RAIZ=Path(__file__).resolve().parents[1]


@unittest.skipUnless(shutil.which('g++'),'g++ no disponible')
class EscanerI2CTest(unittest.TestCase):
    def test_rango_completo_ack_nack_y_error_sin_falsos_dispositivos(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)
            (p/'Arduino.h').write_text(r'''
#pragma once
#include <cstdint>
#include <cstdlib>
#include <iostream>
#include <iomanip>
constexpr int HEX=16;
void delay(unsigned long) {}
struct SerialPrueba {
    void begin(unsigned long b) { if (b!=115200) std::abort(); }
    template<class T> void print(T v) { std::cout << v; }
    void print(unsigned int v,int base) {
        if (base!=HEX) std::abort();
        std::cout << std::uppercase << std::hex << v << std::dec;
    }
    template<class T> void println(T v) { print(v); println(); }
    void println() { std::cout << '\n'; }
} Serial;
''')
            (p/'Wire.h').write_text(r'''
#pragma once
#include "Arduino.h"
struct BusPrueba {
    int consultas=0, direccion=0, modo=0;
    void begin() {}
    void setClock(unsigned long hz) { if (hz!=100000) std::abort(); }
    void setWireTimeout(unsigned int us) { if (us==0) std::abort(); }
    void beginTransmission(uint8_t a) {
        if (a!=consultas+1 || a<1 || a>126) std::abort();
        direccion=a; ++consultas;
    }
    uint8_t endTransmission() {
        if (modo==1) return 2;
        if (direccion==1 || direccion==126) return 0;
        return direccion==64 ? 4 : 2;
    }
} Wire;
''')
            sketch=RAIZ/'arduino/EscanerI2C/EscanerI2C.ino'
            (p/'main.cpp').write_text('#include "'+str(sketch)+'"\n'+r'''
int main() {
    setup(); loop();
    if (Wire.consultas!=126) return 2;
    Wire.consultas=0; Wire.modo=1;
    loop();
    return Wire.consultas==126 ? 0 : 3;
}
''')
            r=subprocess.run(['g++','-std=c++11','-DARDUINO_UNOR4_WIFI',
                              '-I',d,str(p/'main.cpp'),'-o',str(p/'escaner')],
                             capture_output=True,text=True)
            self.assertEqual(r.returncode,0,r.stderr)
            r=subprocess.run([str(p/'escaner')],capture_output=True,text=True)
            self.assertEqual(r.returncode,0,r.stderr)
            self.assertIn('Dispositivo I2C encontrado en 0x01',r.stdout)
            self.assertIn('Dispositivo I2C encontrado en 0x7E',r.stdout)
            self.assertIn('Error I2C en 0x40: codigo 4',r.stdout)
            self.assertIn('Dispositivos: 2; errores: 1',r.stdout)
            self.assertIn('Sin dispositivos detectados.',r.stdout)
            self.assertIn('Dispositivos: 0; errores: 0',r.stdout)
            self.assertEqual(r.stdout.count('Dispositivo I2C encontrado'),2)
