# Guia para subir y ejecutar Smart Air

Esta guia asume que ya creaste el proyecto en Supabase y que estas en el paso de copiar `SUPABASE_URL` y `SUPABASE_KEY`.

## 1. Copiar datos de Supabase

En Supabase entra a:

```text
Project Settings -> API
```

Copia estos dos valores:

```text
Project URL      -> SUPABASE_URL
anon public key  -> SUPABASE_KEY
```

No pegues tu contrasena de WiFi ni claves privadas en GitHub. La `SUPABASE_KEY` se coloca en Render como variable de entorno.

## 2. Probar que la tabla existe

En Supabase abre `SQL Editor` y ejecuta el contenido de:

```text
database.sql
```

La tabla debe llamarse:

```text
readings
```

## 3. Subir el proyecto a GitHub con PowerShell

Abre PowerShell en la carpeta del proyecto:

```powershell
cd "C:\Users\Rada\OneDrive\Documentos\Smart Air"
```

Configura tu nombre y correo si nunca usaste Git:

```powershell
git config --global user.name "Tu Nombre"
git config --global user.email "tu-correo@example.com"
```

Inicializa Git y guarda la primera version:

```powershell
git init
git add .
git commit -m "Primera version Smart Air"
git branch -M main
```

Ahora crea un repositorio en GitHub:

```text
GitHub -> New repository -> smart-air -> Create repository
```

No marques opciones como README, .gitignore o license, porque este proyecto ya los tiene.

Despues copia el enlace HTTPS del repositorio. Se vera parecido a:

```text
https://github.com/TU_USUARIO/smart-air.git
```

Conecta tu carpeta con GitHub y sube el proyecto:

```powershell
git remote add origin https://github.com/TU_USUARIO/smart-air.git
git push -u origin main
```

Si GitHub te pide iniciar sesion, sigue la ventana que aparezca. Si pide token, se crea desde GitHub en `Settings -> Developer settings -> Personal access tokens`.

## 4. Publicar en Render gratis

Entra a Render y sigue:

```text
New -> Web Service -> Build and deploy from a Git repository
```

Conecta tu GitHub y elige el repositorio `smart-air`.

Configura:

```text
Name: smart-air
Runtime: Python
Build Command: pip install -r requirements.txt
Start Command: gunicorn app:app
Plan: Free
```

En `Environment Variables` agrega:

```text
SUPABASE_URL = tu Project URL de Supabase
SUPABASE_KEY = tu anon public key de Supabase
```

Luego presiona:

```text
Create Web Service
```

Cuando termine, Render te dara un link parecido a:

```text
https://smart-air.onrender.com
```

Ese link es el que puedes convertir en codigo QR.

## 5. Probar la pagina

Abre tu link de Render:

```text
https://smart-air.onrender.com
```

Al inicio puede decir `Esperando datos`, porque todavia no hay lecturas.

Para simular una lectura desde el navegador, abre este enlace cambiando el dominio:

```text
https://smart-air.onrender.com/api/readings?mq_raw=42&uv_raw=120&voltage=5.0
```

Despues vuelve a:

```text
https://smart-air.onrender.com
```

La pagina deberia mostrar datos.

## 6. Editar el codigo Arduino

Abre:

```text
arduino/smart_air_uno_esp01.ino
```

Cambia estas tres lineas:

```cpp
const char WIFI_NAME[] = "NOMBRE_DE_TU_WIFI";
const char WIFI_PASSWORD[] = "CONTRASENA_DE_TU_WIFI";
const char HOST[] = "TU_APP.onrender.com";
```

Ejemplo:

```cpp
const char WIFI_NAME[] = "MiWifi";
const char WIFI_PASSWORD[] = "12345678";
const char HOST[] = "smart-air.onrender.com";
```

Importante: en `HOST` no pongas `https://`. Solo va el dominio.

## 7. Conexiones del ESP8266 ESP-01

Usa esta conexion:

```text
ESP8266 TX  -> Arduino pin 2
ESP8266 RX  -> Arduino pin 3 con divisor de voltaje
ESP8266 VCC -> 3.3V
ESP8266 GND -> GND
ESP8266 EN/CH_PD -> 3.3V
```

El RX del ESP8266 no debe recibir 5V directo. Para el divisor de voltaje puedes usar, por ejemplo:

```text
Arduino pin 3 -> resistencia 1k -> ESP RX
ESP RX -> resistencia 2k -> GND
```

## 8. Cargar el codigo al Arduino

1. Abre Arduino IDE.
2. Abre `arduino/smart_air_uno_esp01.ino`.
3. Selecciona `Arduino Uno`.
4. Selecciona el puerto correcto.
5. Presiona `Upload`.
6. Abre el Monitor Serial a `9600`.

Cada 5 segundos deberias ver las lecturas y el intento de envio.

## 9. Si no llegan datos

Revisa en este orden:

1. Que el link de Render abra en el navegador.
2. Que la prueba manual `/api/readings?...` inserte datos.
3. Que `HOST` no tenga `https://`.
4. Que el WiFi y la contrasena esten bien escritos.
5. Que el ESP8266 tenga buena alimentacion de 3.3V.
6. Que `TX del ESP -> pin 2` y `RX del ESP -> pin 3` esten cruzados correctamente.
7. Que tu firmware del ESP8266 acepte `AT+CIPSTART="SSL",...`.

Si tu ESP8266 no acepta SSL, hay que cambiar la estrategia de envio o usar otro firmware/modulo.
