#include <SoftwareSerial.h>

SoftwareSerial esp8266(2, 3);

long velocidades[] = {9600, 19200, 38400, 57600, 74880, 115200};
int totalVelocidades = 6;

void setup() {
  Serial.begin(9600);
  delay(2000);

  Serial.println("Diagnostico ESP8266 ESP-01");
  Serial.println("Monitor Serial: 9600 baudios");
  Serial.println("TX del ESP -> pin 2 del Arduino");
  Serial.println("RX del ESP -> pin 3 del Arduino con divisor de voltaje");
  Serial.println("--------------------------------------");
}

void loop() {
  for (int i = 0; i < totalVelocidades; i++) {
    long velocidad = velocidades[i];
    esp8266.begin(velocidad);
    delay(500);

    Serial.print("Probando ESP a ");
    Serial.print(velocidad);
    Serial.println(" baudios...");

    esp8266.println("AT");
    leerRespuesta(2500);

    Serial.println("--------------------------------------");
    delay(1000);
  }

  Serial.println("Fin de una vuelta. Repetira las pruebas.");
  delay(3000);
}

void leerRespuesta(unsigned long tiempo) {
  unsigned long inicio = millis();
  bool recibioAlgo = false;

  while (millis() - inicio < tiempo) {
    while (esp8266.available()) {
      char c = esp8266.read();
      Serial.write(c);
      recibioAlgo = true;
    }
  }

  if (!recibioAlgo) {
    Serial.println("Sin respuesta legible.");
  } else {
    Serial.println();
  }
}
