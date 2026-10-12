// Arduino UNO: A0 -> compartimento 1, A1 -> 2, A2 -> 3.
// Todos los sensores: 5 V y GND comunes. Sin calibración inventada.
const unsigned long INTERVALO_MS = 500;  // Modificar antes de cargar.
unsigned long ultimoMuestreo = 0;

void setup() {
  Serial.begin(9600);
  Serial.println("t_ms,adc1,adc2,adc3");
}

void loop() {
  const unsigned long ahora = millis();
  // La resta unsigned sigue funcionando cuando millis() desborda.
  if (ahora - ultimoMuestreo < INTERVALO_MS) return;
  ultimoMuestreo = ahora;
  const int adc1 = analogRead(A0);
  const int adc2 = analogRead(A1);
  const int adc3 = analogRead(A2);
  Serial.print(ahora);
  Serial.print(','); Serial.print(adc1);
  Serial.print(','); Serial.print(adc2);
  Serial.print(','); Serial.println(adc3);
}
