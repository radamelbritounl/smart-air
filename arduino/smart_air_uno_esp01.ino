#include <SoftwareSerial.h>

SoftwareSerial esp8266(2, 3);

const int MQ135 = A0;
const int UV = A1;

const int LED_VERDE = 8;
const int LED_AMARILLO = 9;
const int LED_ROJO = 10;

const char WIFI_NAME[] = "NOMBRE_DE_TU_WIFI";
const char WIFI_PASSWORD[] = "CONTRASENA_DE_TU_WIFI";
const char HOST[] = "TU_APP.onrender.com";
const int PORT = 443;
const char CONNECTION_TYPE[] = "SSL";

String estadoAire = "";
String estadoUV = "";

int mqReal = 0;
int mqValor = 0;
int uvLectura = 0;
float uvVoltaje = 0.0;

void setup() {
  Serial.begin(9600);
  esp8266.begin(9600);

  pinMode(LED_VERDE, OUTPUT);
  pinMode(LED_AMARILLO, OUTPUT);
  pinMode(LED_ROJO, OUTPUT);

  apagarLeds();
  sendCommand("AT", 2000);
  sendCommand("AT+CWMODE=1", 2000);
  connectWifi();
}

void loop() {
  leerMQ135();
  leerUV();
  enviarDatos();
  delay(5000);
}

void leerMQ135() {
  mqReal = analogRead(MQ135);
  mqValor = mqReal * 10;

  if (mqValor <= 350) {
    estadoAire = "Aire Bueno";
    digitalWrite(LED_VERDE, HIGH);
    digitalWrite(LED_AMARILLO, LOW);
    digitalWrite(LED_ROJO, LOW);
  } else if (mqValor <= 700) {
    estadoAire = "Aire Regular";
    digitalWrite(LED_VERDE, LOW);
    digitalWrite(LED_AMARILLO, HIGH);
    digitalWrite(LED_ROJO, LOW);
  } else {
    estadoAire = "Aire Contaminado";
    digitalWrite(LED_VERDE, LOW);
    digitalWrite(LED_AMARILLO, LOW);
    digitalWrite(LED_ROJO, HIGH);
  }
}

void leerUV() {
  uvLectura = analogRead(UV);
  uvVoltaje = (uvLectura * 5.0) / 1023.0;

  if (uvVoltaje < 1.0) {
    estadoUV = "Bajo";
  } else if (uvVoltaje < 2.5) {
    estadoUV = "Moderado";
  } else if (uvVoltaje < 4.0) {
    estadoUV = "Alto";
  } else {
    estadoUV = "Muy Alto";
  }
}

void apagarLeds() {
  digitalWrite(LED_VERDE, LOW);
  digitalWrite(LED_AMARILLO, LOW);
  digitalWrite(LED_ROJO, LOW);
}

void connectWifi() {
  String command = "AT+CWJAP=\"";
  command += WIFI_NAME;
  command += "\",\"";
  command += WIFI_PASSWORD;
  command += "\"";
  sendCommand(command, 12000);
}

void enviarDatos() {
  String path = "/api/readings?mq_raw=";
  path += mqReal;
  path += "&uv_raw=";
  path += uvLectura;
  path += "&voltage=5.0";

  String request = "GET ";
  request += path;
  request += " HTTP/1.1\r\nHost: ";
  request += HOST;
  request += "\r\nConnection: close\r\n\r\n";

  String start = "AT+CIPSTART=\"TCP\",\"";
  start = "AT+CIPSTART=\"";
  start += CONNECTION_TYPE;
  start += "\",\"";
  start += HOST;
  start += "\",";
  start += PORT;
  if (!sendCommand(start, 5000)) return;

  String sendLength = "AT+CIPSEND=";
  sendLength += request.length();
  if (!sendCommand(sendLength, 3000)) return;

  esp8266.print(request);
  delay(2000);
  sendCommand("AT+CIPCLOSE", 1000);

  Serial.print("MQ real: ");
  Serial.print(mqReal);
  Serial.print(" | MQ x10: ");
  Serial.print(mqValor);
  Serial.print(" | Aire: ");
  Serial.print(estadoAire);
  Serial.print(" | UV voltaje: ");
  Serial.print(uvVoltaje, 2);
  Serial.print(" | UV: ");
  Serial.println(estadoUV);
}

bool sendCommand(String command, unsigned long timeout) {
  esp8266.println(command);
  unsigned long startTime = millis();
  String response = "";

  while (millis() - startTime < timeout) {
    while (esp8266.available()) {
      char c = esp8266.read();
      response += c;
      Serial.write(c);
    }
  }

  return response.indexOf("OK") >= 0 || response.indexOf(">") >= 0 || response.indexOf("CONNECT") >= 0;
}
