---
id: TT-02
type: Tarea Técnica
epic: RFP-AGROIA-003
priority: Alta
points: 8
---

# TT-02: Firmware ESP32 (CRC, buffer, NTP/RTC)

## Descripción
Validar CRC con reintentos parametrizables, timeout por sensor, múltiples lecturas por punto, hora desde NTP o RTC, buffer offline con idempotencia y versión de firmware en cada trama.

## Criterios de Done
- [ ] Trama con CRC inválido se descarta o reintenta.
- [ ] Idempotencia de ingesta sin duplicados.
- [ ] La trama incluye versión de firmware.

## Dependencias
- Ninguna

