# AgroIA — Documentación del Servicio de Ingesta de Sensores (muestreo por puntos)

> Guía para el equipo del sensor (firmware ESP32/LoRaWAN) y para el personal de
> campo: cómo enviar la trama de datos de cada punto de muestreo y cómo se
> refleja en el mapa de calor del reporte.

---

## 1. Resumen

| Elemento | Valor |
|---|---|
| Endpoint | `POST /api/sensor` |
| Producción | `https://agroia-backend.onrender.com/api/sensor` |
| Local (desarrollo) | `http://localhost:8000/api/sensor` |
| Método / Content-Type | `POST` · `application/json` |
| Respuesta exitosa | `202 Accepted` |
| Autenticación | No usa token; el sensor se identifica con `device_id` (debe estar registrado o se auto-registra) |
| Latencia del free tier | La primera petición tras inactividad puede tardar ~50 s (el servicio se "despierta") |

Cada trama representa **una toma de muestra en un punto del lote**. Si se
incluyen las coordenadas `latitude` y `longitude` (posición del punto dentro del
terreno), la plataforma pinta el **mapa de calor por parámetro** en el reporte.

### 🧪 Body de prueba — copie y pegue

```json
{
  "device_id": "esp32-npk-001",
  "finca_id": "8c2ea84f-b5fa-4291-a1e5-8b42fa5a9936",
  "latitude": 20.0,
  "longitude": 50.0,
  "ph": 6.1,
  "conductivity": 620,
  "nitrogen": 260,
  "phosphorus": 28,
  "potassium": 95,
  "soil_humidity": 31.0,
  "soil_temperature": 19.5,
  "humidity": 72.0,
  "temperature": 21.2,
  "rssi": -45,
  "uptime_s": 604800
}
```

> El `finca_id` del ejemplo es la **finca de demostración** que ya existe en
> producción, así que puede pegar el body tal cual y recibirá `202 Accepted`.
> Para probar con **su** finca, reemplace `finca_id` por el ID que muestra la
> plataforma (pestaña Fincas → botón «📋 Copiar» en la tarjeta de la finca).

**Prueba rápida — bash (macOS / Linux):**

```bash
curl -X POST https://agroia-backend.onrender.com/api/sensor \
  -H "Content-Type: application/json" \
  -d '{"device_id":"esp32-npk-001","finca_id":"8c2ea84f-b5fa-4291-a1e5-8b42fa5a9936","latitude":20.0,"longitude":50.0,"ph":6.1,"conductivity":620,"nitrogen":260,"phosphorus":28,"potassium":95,"soil_humidity":31.0,"soil_temperature":19.5,"humidity":72.0,"temperature":21.2,"rssi":-45,"uptime_s":604800}'
```

**Prueba rápida — PowerShell (Windows):**

```powershell
$body = '{"device_id":"esp32-npk-001","finca_id":"8c2ea84f-b5fa-4291-a1e5-8b42fa5a9936","latitude":20.0,"longitude":50.0,"ph":6.1,"conductivity":620,"nitrogen":260,"phosphorus":28,"potassium":95,"soil_humidity":31.0,"soil_temperature":19.5,"humidity":72.0,"temperature":21.2,"rssi":-45,"uptime_s":604800}'
Invoke-RestMethod -Uri "https://agroia-backend.onrender.com/api/sensor" -Method Post -ContentType "application/json" -Body $body
```

**Respuesta esperada:**

```json
{
  "status": "accepted",
  "device_id": "esp32-npk-001",
  "finca_id": "8c2ea84f-b5fa-4291-a1e5-8b42fa5a9936",
  "auto_registrado": false,
  "variables_recibidas": ["conductividad_electrica", "fosforo", "humedad", "humedad_ambiental", "nitrogeno", "ph", "potasio", "temperatura_ambiental", "temperatura_suelo"],
  "advertencias": ["npk_sin_calibrar"],
  "recibida_en": "2026-08-25T22:00:00+00:00"
}
```

- El `device_id` del ejemplo ya está registrado en producción, por lo que
  `auto_registrado` será `false`. Si usa un `device_id` nuevo, la plataforma lo
  auto-registrará contra la finca indicada en `finca_id` y responderá
  `auto_registrado: true`.
- `advertencias: ["npk_sin_calibrar"]` es normal mientras el sensor no tenga
  calibración NPK de laboratorio (sección 6).

---

## 2. Formato de la trama (JSON)

```json
{
  "device_id": "esp32-npk-001",
  "finca_id": "8c2ea84f-b5fa-4291-a1e5-8b42fa5a9936",
  "latitude": 20.0,
  "longitude": 50.0,
  "humidity": 72.0,
  "temperature": 21.2,
  "conductivity": 620,
  "ph": 6.1,
  "nitrogen": 260,
  "phosphorus": 28,
  "potassium": 95,
  "rssi": -45,
  "uptime_s": 604800
}
```

### ¿A qué finca corresponde la trama? (resolución)

El orden de resolución es el siguiente:

1. **`finca_id` en la trama**: si se envía y la finca existe, la medición (y el
   dispositivo) quedan asociados a esa finca. Si el dispositivo ya estaba en
   otra finca, se reasocia automáticamente a la indicada.
2. **Dispositivo registrado**: si no se envía `finca_id`, se usa la finca que
   tiene registrada el `device_id`.
3. **Auto-registro**: si el `device_id` es desconocido y no viene `finca_id`,
   se asocia a la primera finca disponible (evite este caso: registre el
   dispositivo o envíe siempre `finca_id`).

> **¿De dónde saco el ID de la finca?** Al crear la finca en la plataforma
> (pestaña Fincas → formulario), el sistema muestra el **ID de la finca** con
> botón «Copiar». También aparece en la tarjeta de cada finca. Use ese ID como
> `finca_id` en la trama.

### Campos

| Campo | Tipo | Obligatorio | Unidad | Descripción |
|---|---|---|---|---|
| `device_id` | string | ✅ | — | ID único del sensor (ej. `esp32-npk-001`) |
| `finca_id` | string | ❌ (recomendado) | — | UUID de la finca a la que corresponde la medición (se obtiene al crear la finca en la plataforma) |
| `latitude` | float | ❌ (necesario para el mapa de calor) | metros | Posición X del punto de toma dentro del lote, medida desde una esquina (se acepta también `pos_x`) |
| `longitude` | float | ❌ (necesario para el mapa de calor) | metros | Posición Y del punto de toma dentro del lote (se acepta también `pos_y`) |
| `ph` | float | ❌ | 0–14 | pH del suelo |
| `conductivity` | float | ❌ | µS/cm | Conductividad eléctrica (el servidor la convierte a dS/m) |
| `nitrogen` | float | ❌ | ppm | Nitrógeno (N) |
| `phosphorus` | float | ❌ | ppm | Fósforo (P) |
| `potassium` | float | ❌ | ppm | Potasio (K) |
| `humidity` | float | ❌ | % | Humedad relativa **ambiente** (DHT22). Para humedad del **suelo** use `soil_humidity` |
| `temperature` | float | ❌ | °C | Temperatura **ambiente**. Para temperatura del **suelo** use `soil_temperature` |
| `rssi` | int | ❌ | dBm | Señal del enlace de radio |
| `uptime_s` | int | ❌ | s | Segundos desde encendido del sensor |

- Se aceptan campos extra (no rompen la trama).
- El servidor normaliza y persiste las 18 variables de suelo canónicas
  (nitrógeno, fósforo, potasio, calcio, magnesio, azufre, hierro, manganeso,
  zinc, cobre, boro, materia orgánica, CIC, textura, humedad del suelo,
  temperatura del suelo, conductividad, pH + ambientales).
- **NPK sin calibrar**: si el dispositivo no tiene `npk_calibrado`, los valores
  N/P/K se marcan como "sin calibrar" y el reporte lo advierte.

### Alias aceptados por variable (por si el firmware cambia de nombres)

`n`→nitrógeno, `p`→fósforo, `k`→potasio, `ce`/`ec`→conductividad, `mo`→materia
orgánica, `soil_humidity`→humedad del suelo, `soil_temperature`→temperatura del
suelo, etc. El mapa completo está en `services/normalizacion_iot.py::MAPA_CAMPOS`.

> Importante: `humidity` y `temperature` se registran como telemetría
> **ambiental** del sensor. Si el sensor mide el suelo, enviar
> `soil_humidity` y `soil_temperature` para alimentar el mapa de calor y el
> motor de recomendaciones.

---

## 3. Ejemplo de envío

### curl (prueba rápida)

```bash
curl -X POST https://agroia-backend.onrender.com/api/sensor \
  -H "Content-Type: application/json" \
  -d '{
    "device_id": "esp32-npk-001",
    "finca_id": "8c2ea84f-b5fa-4291-a1e5-8b42fa5a9936",
    "latitude": 20.0, "longitude": 50.0,
    "ph": 6.1, "conductivity": 620,
    "nitrogen": 260, "phosphorus": 28, "potassium": 95,
    "humidity": 72.0, "temperature": 21.2,
    "rssi": -45, "uptime_s": 604800
  }'
```

### ESP32 (Arduino / ESP-IDF) — referencia

```cpp
// Ejemplo con HTTPClient (ESP32 Arduino core)
#include <WiFi.h>
#include <HTTPClient.h>
#include <ArduinoJson.h>

const char* API_URL = "https://agroia-backend.onrender.com/api/sensor";
const char* DEVICE_ID = "esp32-npk-001";
const char* FINCA_ID  = "8c2ea84f-b5fa-4291-a1e5-8b42fa5a9936"; // ID de la finca

void enviarMedicion(float posX, float posY, float ph, float ceUsCm,
                    float nPpm, float pPpm, float kPpm,
                    float hrAmb, float tempAmb, int rssi) {
  if (WiFi.status() != WL_CONNECTED) return;

  StaticJsonDocument<512> doc;
  doc["device_id"]  = DEVICE_ID;
  doc["finca_id"]   = FINCA_ID;   // finca a la que corresponde
  doc["latitude"]   = posX;      // metros dentro del lote
  doc["longitude"]  = posY;
  doc["ph"]         = ph;
  doc["conductivity"] = ceUsCm;  // µS/cm
  doc["nitrogen"]   = nPpm;      // ppm
  doc["phosphorus"] = pPpm;
  doc["potassium"]  = kPpm;
  doc["humidity"]   = hrAmb;     // %
  doc["temperature"]= tempAmb;   // °C
  doc["rssi"]       = rssi;
  doc["uptime_s"]   = millis() / 1000;

  String body;
  serializeJson(doc, body);

  HTTPClient http;
  http.begin(API_URL);
  http.addHeader("Content-Type", "application/json");
  int code = http.POST(body);
  // 202 = aceptada; 4xx = revisar detalle en la respuesta JSON
  http.end();
}
```

---

## 4. Muestreo en cuadrícula (cómo tomar los puntos)

Para que el mapa de calor sea representativo:

1. Divida el lote como una **matriz** (ej. 3×3, 4×3 según el tamaño).
2. Defina una esquina del lote como origen `(0, 0)`.
3. Mida las coordenadas de cada punto en **metros** (`latitude`, `longitude`).
4. En cada punto tome la muestra y envíe una trama con esas coordenadas.
5. Envíe todas las tramas en una sola jornada de muestreo (mismo día) para que
   el reporte compare puntos comparables.

Ejemplo de cuadrícula 3×3 en un lote de 250 × 100 m:

```
(0,100) ─────────────── (250,100)
  │  x=20   x=125  x=230   │
  │ y=90   y=90   y=90     │
  │  ●──────●──────●       │
  │  │      │      │       │
  │ y=50   y=50   y=50     │
  │  ●──────●──────●       │
  │  │      │      │       │
  │ y=10   y=10   y=10     │
  │  ●──────●──────●       │
(0,0) ───────────────── (250,0)
```

> El reporte muestra una celda por punto: verde = dentro del rango ideal,
> ámbar = cerca, rojo = fuera; y una vista «Resumen» con cuántas variables
> están fuera del ideal en cada punto.

---

## 5. Respuesta del servidor

### Éxito — `202 Accepted`

```json
{
  "status": "accepted",
  "device_id": "esp32-npk-001",
  "finca_id": "8c2ea84f-b5fa-4291-a1e5-8b42fa5a9936",
  "auto_registrado": false,
  "variables_recibidas": ["conductividad_electrica", "fosforo", "nitrogeno", "ph", "potasio"],
  "advertencias": [],
  "recibida_en": "2026-08-25T22:00:00+00:00"
}
```

- `auto_registrado: true` → el `device_id` no existía y quedó asociado a la
  finca indicada en `finca_id` (o a la primera finca si la trama no lo traía).
- `advertencias` → por ejemplo `["npk_sin_calibrar"]` cuando N/P/K no están
  calibrados contra laboratorio.
- `variables_recibidas` usa los **nombres canónicos en español** (ej.
  `conductividad_electrica`, `fosforo`, `nitrogeno`).

### Errores

| HTTP | `code` | Significado |
|---|---|---|
| `422` | `FINCA_NOT_FOUND` | El `finca_id` de la trama no corresponde a una finca registrada |
| `422` | `NO_FINCAS` | No hay fincas registradas y el dispositivo es desconocido (no se pudo auto-registrar) |
| `422` | `INGEST_ERROR` | Error interno al persistir la trama |
| `422` | (validación) | `device_id` ausente o campos con tipo incorrecto |

---

## 6. Calibración NPK

Si el sensor NPK fue calibrado contra un laboratorio, regístrelo así y la
plataforma aplica los **factores de calibración** a cada trama:

```json
POST /api/v1/iot/dispositivos
{
  "device_id": "esp32-npk-001",
  "finca_id": "8c2ea84f-b5fa-4291-a1e5-8b42fa5a9936",
  "nombre": "Sensor cuadrícula lote 1",
  "npk_calibrado": true
}
```

---

## 7. Registro de dispositivos (evitar auto-registro a la finca equivocada)

```bash
curl -X POST https://agroia-backend.onrender.com/api/v1/iot/dispositivos \
  -H "Content-Type: application/json" \
  -d '{"device_id":"esp32-npk-001","finca_id":"UUID_DE_LA_FINCA","nombre":"Sensor 1","npk_calibrado":false}'
```

El `finca_id` se obtiene del administrador de la plataforma (pestaña Fincas).

---

## 8. Carga por archivo (alternativa sin conexión)

Cuando el sensor no tiene señal, las tramas pueden exportarse a un archivo y
subirse manualmente: `POST /api/v1/iot/carga` (multipart: `file` + `finca_id`
opcional). Formatos aceptados:

### CSV ancho con varias filas (una fila = un punto de muestreo)

```csv
x,y,ph,conductividad,n,p,k,humedad,temperatura
20,90,5.6,410,250,20,75,25,18.0
125,90,5.9,470,230,24,85,29,18.8
230,90,6.2,530,210,28,95,33,19.6
20,50,5.9,480,225,23,83,28,18.5
125,50,6.2,540,205,27,93,32,19.3
230,50,6.4,600,185,31,103,36,20.1
20,10,6.2,550,195,26,91,31,19.2
125,10,6.4,610,175,30,101,35,20.0
230,10,6.7,670,155,34,111,39,20.8
```

(Se aceptan también los nombres `latitude,longitude`, `pos_x,pos_y`,
`coordenada_x,coordenada_y`, `columna,fila`.)

### JSON — lista de tramas (una por punto)

```json
[
  {"device_id":"esp32-npk-001","finca_id":"8c2ea84f-b5fa-4291-a1e5-8b42fa5a9936","x":20,"y":90,"ph":5.6,"conductivity":410,"nitrogen":250},
  {"device_id":"esp32-npk-001","finca_id":"8c2ea84f-b5fa-4291-a1e5-8b42fa5a9936","x":125,"y":90,"ph":5.9,"conductivity":470,"nitrogen":230}
]
```

Respuesta: `{status:"accepted", numero_muestras: 9, variables_recibidas:[...], analisis:{...}}`.
La carga ejecuta el análisis al instante y deja las muestras listas para el reporte.

---

## 9. Dónde se ve el resultado

1. **Reporte** (`Reportes → Generar reporte`): sección **«M — Mapa de calor del
   lote»** con pestañas por parámetro (pH, N, P, K, humedad…) y vista
   «🧭 Resumen» con todas las variables a la vez.
2. **Chat agronómico**: el asesor usa esas mismas lecturas con posición para
   responder "¿cómo está el lote por sectores?".
3. **Historial / sensores**: cada lectura queda en la serie temporal de la finca.

---

## 10. Notas operativas

- Envíe cada punto con **reloj UTC o sin zona**; el servidor marca la recepción.
- Free tier: si el servicio está dormido, la primera trama puede tardar ~50 s;
  las siguientes son inmediatas. Use reintentos (timeout ≥ 60 s) en el firmware.
- No envíe más de ~1 trama/segundo por dispositivo.
- Un `device_id` siempre reporta contra su finca registrada; para cambiar de
  finca, re-regístrelo con el nuevo `finca_id`.
