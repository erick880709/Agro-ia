# RF-059: Firmware

**Tipo:** Requerimiento funcional
**Fuente:** RFP-AGROIA-003 §6 (Requerimientos, Épica E1)
**Prioridad:** No especificada

## Descripción
El firmware del dispositivo valida CRC y reintenta (máximo N reintentos, parametrizable), aplica timeout por sensor, toma múltiples lecturas por punto, obtiene la hora desde NTP o RTC, mantiene un buffer offline con idempotencia e incluye la versión de firmware en cada trama. Requiere transceptor RS485 y alimentación de 12 V (el ESP32 trabaja a 3,3 V lógico).

## Actores involucrados
Firmware ESP32, consumidor IoT

## Criterios de aceptación
No especificados en el RFP — definir con el cliente.

## Dependencias / relacionados
RF-057 (decodificación); RNF-037 (operación offline).

## Notas del analista
La variante de alimentación debe confirmarse en la fase 0 (H-13: 12 V por defecto vs 12–24 V).
