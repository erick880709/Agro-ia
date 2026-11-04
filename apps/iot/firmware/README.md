# Firmware ESP32 — Sensor JXBS-3001-NPK-RS (Épica E1 · TT-02)

Firmware de referencia para el ESP32 que lee el sensor de suelo 7-en-1 vía
**RS485 / Modbus RTU** (9600 8N1, función 0x03) y publica una trama JSON.

## Qué hace

- Lee los registros `0x0006` (pH), `0x0012` (humedad VWC), `0x0013`
  (temperatura con signo), `0x0015` (CE) y `0x001E–0x0020` (N, P, K).
- **Valida CRC-16 Modbus** de cada respuesta y **reintenta** hasta
  `MAX_REINTENTOS` veces.
- Toma `LECTURAS_POR_PUNTO` réplicas y publica el promedio.
- Sincroniza la hora por **NTP** (fallback: el backend usa su timestamp).
- Incluye **versión de firmware** y **`msg_id`** (idempotencia) en cada trama.
- Soporta el **buffer offline**: la trama se conserva con su `msg_id` y se
  reenvía sin duplicar al reconectar.

## Conexionado

| ESP32 | Transceptor RS485 | Sensor |
|-------|-------------------|--------|
| GPIO 16 (RX) | RO | — |
| GPIO 17 (TX) | DI | — |
| GPIO 32 | DE + RE | — |
| — | A | A (bus) |
| — | B | B (bus) |
| — | — | 12 V DC (alimentación del sensor) |

> El ESP32 trabaja a **3,3 V lógico**; es obligatorio un transceptor RS485.
> La variante de fábrica del sensor se alimenta a **12 V DC**.

## Configuración mínima

- `WIFI_SSID` / `WIFI_PASS`
- `HOSTNAME_APLICA` → `device_id` único registrado en la plataforma
  (`POST /api/v1/iot/dispositivos`).
- `SENSOR_ADDR` (0x01 por defecto; configurable en el registro 0x0100).

## Publicación

El backend expone `POST /api/v1/iot/sensor/raw` para decodificar registros
crudos, y `POST /api/v1/iot/sensor` para la trama normalizada. El JSON del
firmware (`serializar_trama`) es el contrato de salida.

## Validación del CRC

El CRC-16 Modbus del firmware usa el polinomio `0xA001`. Está verificado en
`apps/backend/tests/test_decodificacion_modbus.py` contra el vector conocido:

```
01 03 00 00 00 0A  →  CRC = 0xCDC5 (lo=C5, hi=CD)
```

## Compilación

Compila con **Arduino IDE** (placa ESP32 Dev Module) o **PlatformIO**:

```ini
; platformio.ini (ejemplo)
[env:esp32dev]
platform = espressif32
board = esp32dev
framework = arduino
```

> El sketch no requiere librerías externas de Modbus (implementa el protocolo
> de forma autocontenida). La compilación del C++ no forma parte del CI de
> este repositorio; el algoritmo de CRC queda cubierto por el test en Python.
