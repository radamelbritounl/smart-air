# Smart Air

Proyecto basico para Arduino UNO, MQ135, sensor UV, ESP8266 ESP-01 y una pagina web con Python.

## Que hace

- Lee el valor real del MQ135.
- Calcula `MQ135 x 10`.
- Clasifica la calidad del aire:
  - `0 - 350`: Bajo
  - `351 - 700`: Medio
  - `701+`: Alto
- Lee el sensor UV.
- Muestra voltaje constante de `5.0 V`.
- Actualiza la web cada 5 segundos.
- Genera graficas con Python y las muestra en la pagina web.
- Guarda datos para mostrar promedios diarios de los ultimos 7 dias.
- Usa programacion orientada a objetos en `app.py`.

## Conexion usada

- MQ135: `VCC -> 5V`, `GND -> GND`, `AOUT -> A0`.
- Sensor UV: `VCC -> 3.3V`, `GND -> GND`, `SIG -> A1`.
- LED verde: pin `8`.
- LED amarillo: pin `9`.
- LED rojo: pin `10`.
- ESP8266 ESP-01:
  - `VCC -> 3.3V`
  - `GND -> GND`
  - `CH_PD/EN -> 3.3V`
  - `TX del ESP -> pin 2 del Arduino`
  - `RX del ESP -> pin 3 del Arduino con divisor de voltaje`

Importante: el RX del ESP8266 no debe recibir 5V directo desde el Arduino. Usa divisor de voltaje o conversor logico.

## Crear base de datos en Supabase

1. Crea un proyecto gratuito en Supabase.
2. Abre SQL Editor.
3. Ejecuta el contenido de `database.sql`.
4. Copia:
   - `SUPABASE_URL`
   - `SUPABASE_KEY`

Para un proyecto universitario pequeno, puedes usar la anon key si la tabla solo se usa para demostracion. Para algo mas cuidado, usa una key privada solo en Render.

## Publicar gratis en Render

1. Sube este proyecto a GitHub.
2. En Render, crea un Web Service desde el repositorio.
3. Usa:
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `gunicorn app:app`
4. En variables de entorno agrega:
   - `SUPABASE_URL`
   - `SUPABASE_KEY`
5. Copia el link final de Render y ponlo en `HOST` dentro del codigo Arduino.

Ese link se puede convertir a codigo QR.

## Probar en la computadora

```bash
pip install -r requirements.txt
python app.py
```

Luego abre:

```text
http://localhost:5000
```

Puedes simular una lectura con:

```text
http://localhost:5000/api/readings?mq_raw=42&uv_raw=120&voltage=5.0
```

## Guia completa

Para subir a GitHub, publicar en Render y cargar el Arduino, lee:

```text
GUIA_DESPLIEGUE.md
```
