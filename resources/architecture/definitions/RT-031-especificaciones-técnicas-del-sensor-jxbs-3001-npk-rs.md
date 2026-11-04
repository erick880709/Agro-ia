# RT-031: Especificaciones técnicas del sensor JXBS-3001-NPK-RS

**Tipo:** Requisito técnico
**Categoría:** Integración / Stack tecnológico
**Fuente:** RFP-AGROIA-003 §3 y §9 (Anexo A)

## Descripción
Decodificación y escalas del sensor RS485 Modbus RTU 9600 8N1 (función 0x03, dirección por defecto 0x01 configurable en 0x0100): temperatura 0x0013 (0,1 °C con signo, −40 a 80 °C, ±0,5 °C); humedad 0x0012 (0,1 %, 0–100 %, ±3/±5 % por tramo); CE 0x0015 (1 µS/cm, resolución 10, 0–10 000 µS/cm, exactitud no especificada); pH 0x0006 (0,01, 3–9, ±0,3); N/P/K 0x001E–0x0020 (mg/kg, 0–1999, ±2 % F.S. ≈ ±40 mg/kg). Respuesta <1 s, IP68, presión 0,9–1,1 atm, hasta 16+ sensores por bus.

## Criterio medible / restricción concreta
Según lo especificado en la descripción; los valores son parametrizables y ajustables con el equipo agronómico.

## Impacto en la arquitectura
Condiciona la ingesta (apps/iot), la decodificación (RF-057) y los límites de validación (RT-032).

## Notas del analista
El sensor no mide MO, CIC, textura, Ca, Mg, Na, Al, S, B, Zn, Cu, Fe, Mn — solo 7 de 18 variables.
