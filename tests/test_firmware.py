"""Ejecuta el sketch con E/S simulada en C++; no verifica el circuito físico."""
import csv
import io
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

from python.comunicacion import registrar

RAIZ=Path(__file__).resolve().parents[1]

ARDUINO_H=r'''
#pragma once
#include <cstdint>
#include <cstdlib>
#include <iostream>
#include <sstream>
constexpr int A0=14, A1=15, A2=16, A3=17, SDA=18, SCL=19;
constexpr int HIGH=1, LOW=0, OUTPUT=1, INPUT=0;
uint32_t reloj=0;
int resolucion=0, siguientePin=0, lecturas=0, salidas=0, encendidos=0;
bool pinesConfigurados[14]={false};
int valoresAdc[3]={0,512,1023};
uint32_t millis() { return reloj; }
void analogReadResolution(int bits) { resolucion=bits; }
void pinMode(int pin, int modo) {
    if (modo!=OUTPUT || pin<2 || pin>10 || pinesConfigurados[pin]) std::abort();
    pinesConfigurados[pin]=true;
    ++salidas;
}
void digitalWrite(int pin, int nivel) {
    if (pin<2 || pin>10 || (nivel!=LOW && nivel!=HIGH)) std::abort();
    if (nivel==HIGH) ++encendidos;
}
int analogRead(int pin) {
    const int pines[3]={A0,A2,A3};
    if (resolucion!=10 || pin!=pines[siguientePin]) std::abort();
    ++lecturas;
    int valor=valoresAdc[siguientePin];
    siguientePin=(siguientePin+1)%3;
    return valor;
}
struct PuertoSerial {
    std::ostringstream datos;
    void begin(unsigned long baudios) { if (baudios!=115200) std::abort(); }
    template<class T> void print(T valor) { datos << valor; }
    template<class T> void println(T valor) { datos << valor << "\r\n"; }
} Serial;
'''


@unittest.skipUnless(shutil.which('g++'),'g++ no disponible: prueba nativa omitida')
class FirmwareTest(unittest.TestCase):
    def test_rechaza_pines_led_compartidos_o_reservados(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)
            cabecera=RAIZ/'arduino/NivelAguaR4/ColoresNivel.h'
            (p/'main.cpp').write_text('#include "'+str(cabecera)+'"\n'+r'''
int main() {
    const int reservados[5]={14,16,17,18,19}; // A0,A2,A3,SDA,SCL de esta placa.
    const int compartidos[3][3]={{2,3,4},{4,5,6},{8,9,10}};
    const int faltantes[3][3]={{2,3,-1},{4,5,6},{8,9,10}};
    const int sensor[3][3]={{2,3,14},{4,5,6},{8,9,10}};
    const int bus[3][3]={{2,3,18},{4,5,6},{8,9,10}};
    const int distintos[3][3]={{2,3,4},{7,6,5},{10,9,8}};
    if (pinesLedValidos(compartidos,reservados)) return 1;
    if (pinesLedValidos(faltantes,reservados)) return 2;
    if (pinesLedValidos(sensor,reservados)) return 3;
    if (pinesLedValidos(bus,reservados)) return 4;
    if (!pinesLedValidos(distintos,reservados)) return 5;
}
''')
            r=subprocess.run(['g++','-std=c++11',str(p/'main.cpp'),'-o',str(p/'pines')],
                             capture_output=True,text=True)
            self.assertEqual(r.returncode,0,r.stderr)
            r=subprocess.run([str(p/'pines')],capture_output=True)
            self.assertEqual(r.returncode,0,r.stderr)

    def test_colores_segun_limites_medidos_y_configuracion_incompleta(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)
            cabecera=RAIZ/'arduino/NivelAguaR4/ColoresNivel.h'
            (p/'main.cpp').write_text('#include "'+str(cabecera)+'"\n'+r'''
int main() {
    // Datos controlados para probar límites; NO calibración del circuito.
    const int limites[3]={10,20,30};
    const int adc[]={0,10,11,20,21,30,31,1023};
    const int colores[]={5,5,2,2,3,3,1,1}; // R=1, G=2, B=4.
    for (int i=0;i<8;++i) if (colorParaAdc(adc[i],limites)!=colores[i]) return 1;
    const int invalidos[][3]={{-1,-1,-1},{20,10,30},{0,0,30},{0,1023,1024}};
    for (const auto& valores : invalidos)
        if (colorParaAdc(25,valores)!=0) return 2;
    if (colorParaAdc(-1,limites)!=0 || colorParaAdc(1024,limites)!=0) return 3;
}
''')
            r=subprocess.run(['g++','-std=c++11',str(p/'main.cpp'),'-o',str(p/'colores')],
                             capture_output=True,text=True)
            self.assertEqual(r.returncode,0,r.stderr)
            r=subprocess.run([str(p/'colores')],capture_output=True)
            self.assertEqual(r.returncode,0,r.stderr)

    def test_muestreo_csv_desborde_y_salidas_desactivadas(self):
        with tempfile.TemporaryDirectory() as d:
            carpeta=Path(d)
            (carpeta/'Arduino.h').write_text(ARDUINO_H)
            sketch=RAIZ/'arduino/NivelAguaR4/NivelAguaR4.ino'
            (carpeta/'main.cpp').write_text(
                '#include "'+str(sketch)+'"\n'+r'''
int main() {
    setup();
    const uint32_t instantes[]={0,499,500,501,999,1000,4294967195u,398,399};
    for (uint32_t instante : instantes) { reloj=instante; loop(); }
    if (lecturas!=12 || salidas!=9 || encendidos!=0) return 2;
    const int esperados[3][3]={{2,3,4},{7,6,5},{10,9,8}};
    for (int led=0;led<3;++led)
        for (int canal=0;canal<3;++canal)
            if (PINES_LED[led][canal]!=esperados[led][canal]) return 3;
    std::cout << Serial.datos.str();
}
''')
            compilacion=subprocess.run(
                ['g++','-std=c++11','-DARDUINO_UNOR4_WIFI','-DNIVEL_AGUA_LCD=0','-I',d,
                 str(carpeta/'main.cpp'),'-o',str(carpeta/'firmware')],
                capture_output=True,text=True)
            self.assertEqual(compilacion.returncode,0,compilacion.stderr)
            ejecucion=subprocess.run([str(carpeta/'firmware')],capture_output=True)
            self.assertEqual(ejecucion.returncode,0,ejecucion.stderr)
            self.assertEqual(ejecucion.stdout,
                b'tiempo_ms,sensor1,sensor2,sensor3\r\n'
                b'500,0,512,1023\r\n1000,0,512,1023\r\n'
                b'4294967195,0,512,1023\r\n399,0,512,1023\r\n')
            destino=carpeta/'control.csv'
            self.assertEqual(registrar(io.BytesIO(ejecucion.stdout),destino,
                             max_muestras=4,origen='prueba_controlada'),(4,0))
            with destino.open() as f: filas=list(csv.DictReader(f))
            self.assertEqual(filas[-1]['t_ms'],'399')
            self.assertEqual(filas[-1]['adc3'],'1023')
            from python.graficas import mediciones
            png=mediciones(destino,carpeta/'control.png')
            self.assertEqual(png.read_bytes()[:8],b'\x89PNG\r\n\x1a\n')

    def test_lcd_027_muestra_tres_adc_y_borra_digitos_anteriores(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)
            (p/'Arduino.h').write_text(ARDUINO_H)
            (p/'Wire.h').write_text(r'''
#pragma once
#include "Arduino.h"
struct Bus {
    void begin() {}
    void setWireTimeout(unsigned int) {}
    void beginTransmission(int direccion) { if (direccion!=0x27) std::abort(); }
    int endTransmission() { return 0; }
} Wire;
''')
            (p/'LiquidCrystal_I2C.h').write_text(r'''
#pragma once
#include "Arduino.h"
#include <string>
struct LiquidCrystal_I2C {
    std::string filas[2]={std::string(16,' '),std::string(16,' ')};
    int fila=0, columna=0;
    bool inicializada=false;
    LiquidCrystal_I2C(int direccion,int columnas,int renglones) {
        if (direccion!=0x27 || columnas!=16 || renglones!=2) std::abort();
    }
    void init() { inicializada=true; }
    void backlight() { if (!inicializada) std::abort(); }
    void setCursor(int c,int f) { columna=c; fila=f; }
    void print(const char* texto) {
        if (!inicializada) std::abort();
        while (*texto && columna<16) filas[fila][columna++]=*texto++;
    }
};
''')
            sketch=RAIZ/'arduino/NivelAguaR4/NivelAguaR4.ino'
            (p/'main.cpp').write_text('#include "'+str(sketch)+'"\n'+r'''
int main() {
    setup(); reloj=500; loop();
    if (lcd.filas[0]!="S1:   0 S2: 512 " || lcd.filas[1]!="S3:1023 ADC     ") return 2;
    valoresAdc[0]=valoresAdc[1]=valoresAdc[2]=1;
    reloj=1000; loop();
    if (lcd.filas[0]!="S1:   1 S2:   1 " || lcd.filas[1]!="S3:   1 ADC     ") return 3;
    if (salidas!=9 || encendidos!=0) return 4;
}
''')
            r=subprocess.run(['g++','-std=c++11','-DARDUINO_UNOR4_WIFI','-I',d,
                              str(p/'main.cpp'),'-o',str(p/'lcd')],
                             capture_output=True,text=True)
            self.assertEqual(r.returncode,0,r.stderr)
            r=subprocess.run([str(p/'lcd')],capture_output=True)
            self.assertEqual(r.returncode,0,r.stderr)
