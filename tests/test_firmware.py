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
int nivelesPin[14]={0};
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
    nivelesPin[pin]=nivel;
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
    const int fueraDelMontaje[3][3]={{2,3,11},{7,6,5},{10,9,8}};
    if (pinesLedValidos(fueraDelMontaje,reservados)) return 6;
}
''')
            r=subprocess.run(['g++','-std=c++11',str(p/'main.cpp'),'-o',str(p/'pines')],
                             capture_output=True,text=True)
            self.assertEqual(r.returncode,0,r.stderr)
            r=subprocess.run([str(p/'pines')],capture_output=True)
            self.assertEqual(r.returncode,0,r.stderr)

    def test_colores_adc_provisionales_todos_los_valores_y_fronteras(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)
            cabecera=RAIZ/'arduino/NivelAguaR4/ColoresNivel.h'
            (p/'main.cpp').write_text('#include "'+str(cabecera)+'"\n'+r'''
#include <climits>
int main() {
    // Máscaras literales R=1, G=2, B=4; cuentas ADC, NO alturas.
    const int adc[]={0,49,50,149,150,299,300,1023};
    const int colores[]={2,2,4,4,5,5,1,1};
    for (int i=0;i<8;++i) if (colorParaAdc(adc[i])!=colores[i]) return 1;
    for (int v=0;v<=49;++v) if (colorParaAdc(v)!=2) return 2;
    for (int v=50;v<=149;++v) if (colorParaAdc(v)!=4) return 3;
    for (int v=150;v<=299;++v) if (colorParaAdc(v)!=5) return 4;
    for (int v=300;v<=1023;++v) if (colorParaAdc(v)!=1) return 5;
    const int invalidos[]={INT_MIN,-1024,-1,1024,65535,INT_MAX};
    for (int valor : invalidos) if (colorParaAdc(valor)!=0) return 6;
    if (COLOR_AZUL!=4) return 7;
}
''')
            r=subprocess.run(['g++','-std=c++11',str(p/'main.cpp'),'-o',str(p/'colores')],
                             capture_output=True,text=True)
            self.assertEqual(r.returncode,0,r.stderr)
            r=subprocess.run([str(p/'colores')],capture_output=True)
            self.assertEqual(r.returncode,0,r.stderr)

    def test_led_habilitados_independientes_transiciones_y_adc_invalidos(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)
            (p/'Arduino.h').write_text(ARDUINO_H)
            sketch=RAIZ/'arduino/NivelAguaR4/NivelAguaR4.ino'
            (p/'main.cpp').write_text('#include "'+str(sketch)+'"\n'+r'''
bool comprobar(const int colores[3]) {
    const int pines[3][3]={{2,3,4},{7,6,5},{10,9,8}};
    for (int led=0;led<3;++led)
        for (int canal=0;canal<3;++canal)
            if (nivelesPin[pines[led][canal]]!=((colores[led]>>canal)&1)) return false;
    return true;
}
int main() {
    setup();
    const int apagados[3]={0,0,0};
    if (!comprobar(apagados)) return 1;
    const int entradas[][3]={{49,50,150},{300,149,299},{150,300,0},
                            {1023,1023,1023},{-1,1024,-5},{0,50,300}};
    const int colores[][3]={{2,4,5},{1,4,5},{5,1,2},{1,1,1},{0,0,0},{2,4,1}};
    for (int i=0;i<6;++i) {
        actualizarLeds(entradas[i]);
        if (!comprobar(colores[i])) return 2+i;
    }
    // Recorrer cada frontera en ambos sentidos para cada LED, manteniendo los otros.
    const int limites[]={49,50,149,150,299,300,299,150,149,50,49};
    const int esperados[]={2,4,4,5,5,1,5,5,4,4,2};
    for (int led=0;led<3;++led)
        for (int j=0;j<11;++j) {
            int adc[3]={0,50,300}, color[3]={2,4,1};
            adc[led]=limites[j]; color[led]=esperados[j];
            actualizarLeds(adc);
            if (!comprobar(color)) return 20+led;
        }
    reloj=500; loop();
    std::cout << Serial.datos.str();
}
''')
            r=subprocess.run(['g++','-std=c++11','-DARDUINO_UNOR4_WIFI',
                              '-DNIVEL_AGUA_LCD=0','-DNIVEL_AGUA_LED=1','-I',d,
                              str(p/'main.cpp'),'-o',str(p/'led')],capture_output=True,text=True)
            self.assertEqual(r.returncode,0,r.stderr)
            r=subprocess.run([str(p/'led')],capture_output=True)
            self.assertEqual(r.returncode,0,r.stderr)
            self.assertEqual(r.stdout,b'tiempo_ms,sensor1,sensor2,sensor3\r\n500,0,512,1023\r\n')

    def test_led_deshabilitados_por_defecto_apagan_todos_los_colores(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)
            (p/'Arduino.h').write_text(ARDUINO_H)
            sketch=RAIZ/'arduino/NivelAguaR4/NivelAguaR4.ino'
            (p/'main.cpp').write_text('#include "'+str(sketch)+'"\n'+r'''
int main() {
    setup();
    const int entradas[][3]={{0,50,150},{300,1023,49},{-1,1024,150}};
    for (const auto& adc : entradas) actualizarLeds(adc);
    for (int pin=2;pin<=10;++pin) if (nivelesPin[pin]!=LOW) return 1;
}
''')
            r=subprocess.run(['g++','-std=c++11','-DARDUINO_UNOR4_WIFI','-DNIVEL_AGUA_LCD=0',
                              '-I',d,str(p/'main.cpp'),'-o',str(p/'apagados')],capture_output=True,text=True)
            self.assertEqual(r.returncode,0,r.stderr)
            r=subprocess.run([str(p/'apagados')],capture_output=True)
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
    if (salidas!=9 || (!NIVEL_AGUA_LED && encendidos!=0)) return 4;
    if (NIVEL_AGUA_LED) {
        // Con ADC=1, los tres canales verdes deben estar encendidos.
        for (int pin=2;pin<=10;++pin)
            if (nivelesPin[pin]!=((pin==3 || pin==6 || pin==9) ? HIGH : LOW)) return 5;
    }
}
''')
            for enabled in (0,1):
                with self.subTest(led_habilitados=enabled):
                    r=subprocess.run(['g++','-std=c++11','-DARDUINO_UNOR4_WIFI',
                                      f'-DNIVEL_AGUA_LED={enabled}','-I',d,
                                      str(p/'main.cpp'),'-o',str(p/'lcd')],
                                     capture_output=True,text=True)
                    self.assertEqual(r.returncode,0,r.stderr)
                    r=subprocess.run([str(p/'lcd')],capture_output=True)
                    self.assertEqual(r.returncode,0,r.stderr)
