# RT-032: Reglas de validación e incertidumbre parametrizables (Anexo A)

**Tipo:** Requisito técnico
**Categoría:** Integración / Stack tecnológico
**Fuente:** RFP-AGROIA-003 §3 y §9 (Anexo A)

## Descripción
Valores iniciales parametrizables: temperatura −40 a 80 °C (±0,5, alerta >45 °C); humedad VWC 0–100 % (±3 ≤53 / ±5 >53, 0 con CE≈0 = sonda fuera del suelo); pH >3,00 y <9,00 (≤3,00 y ≥9,00 saturada, ±0,3, requiere humedad mínima); CE 10 a <10 000 µS/cm (0 = bajo detección, ≥10 000 saturada, normalizar a 25 °C, CE aparente no CEe); N/P/K 1 a <1999 mg/kg (0 = bajo detección, ≥1999 saturada, ±40 mg/kg, indicativo hasta calibrar).

## Criterio medible / restricción concreta
Según lo especificado en la descripción; los valores son parametrizables y ajustables con el equipo agronómico.

## Impacto en la arquitectura
Alimenta el motor de calidad (RF-062 a RF-065) y la incertidumbre (RF-067).

## Notas del analista
Incertidumbre calculada con distribución rectangular (exactitud/√3).
