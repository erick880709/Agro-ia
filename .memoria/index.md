# Memoria del proyecto

> Grafo de conocimiento generado por la skill `memoria`. Fuente de verdad: `.memoria/graph.json`.
> Este archivo se regenera; no lo edites a mano.

**3 nodo(s)** · **0 enlace(s)** · actualizado 2026-11-04T12:07:40.961Z

## Contexto activo

- **Implementar epica E3 incertidumbre y clasificacion (RFP-003)** — `builder` · completado · 2026-11-04
  TT-06 incertidumbre por variable (incertidumbre.py, exactitud/raiz3, migracion 052, consumer guarda mapa de incertidumbres), TT-07 banda de frontera (banda_frontera.py + RulesEngine.evaluar_con_banda) y agregacion robusta (agregacion_robusta.py, mediana/IQR/minimo puntos), HU-03 presentacion con incertidumbre (formatear_valor). 26 tests, integracion 8/8.
- **Implementar epica E2 motor de calidad del dato (RFP-003)** — `builder` · completado · 2026-11-04
  TT-04 motor de 10 estados (motor_calidad.py, migracion 051 con renombrado de estados legados), TT-05 reglas de validez parametrizables (saturacion simetrica, bajo limite, humedad minima, sonda fuera, plausibilidad), HU-02 endpoint de transparencia calidad-resumen. 20 tests. Contrato del sensor validado sin cambios (integracion 8/8).
- **Implementar epica E1 integridad de ingesta (RFP-003)** — `builder` · completado · 2026-11-04
  TT-01 decodificacion Modbus JXBS-3001 + CRC16 (15 tests), TT-02 firmware ESP32 (apps/iot/firmware), TT-03 verificacion de variante, HU-01 registro de dispositivos con configuracion (migracion 050).

## Avances

### ✅ Implementar epica E3 incertidumbre y clasificacion (RFP-003)

- **id:** `mem-20261104120740-2fb521-builder-implementar-epica-e3-incertidumbre-y-clasificacion-r`
- **skill:** `builder` · **estado:** completado · **creado:** 2026-11-04
- **resumen:** TT-06 incertidumbre por variable (incertidumbre.py, exactitud/raiz3, migracion 052, consumer guarda mapa de incertidumbres), TT-07 banda de frontera (banda_frontera.py + RulesEngine.evaluar_con_banda) y agregacion robusta (agregacion_robusta.py, mediana/IQR/minimo puntos), HU-03 presentacion con incertidumbre (formatear_valor). 26 tests, integracion 8/8.
- **archivos:** `apps/backend/agroia_backend/services/incertidumbre.py`

### ✅ Implementar epica E2 motor de calidad del dato (RFP-003)

- **id:** `mem-20261104033544-bf2ebe-builder-implementar-epica-e2-motor-de-calidad-del-dato-rfp-0`
- **skill:** `builder` · **estado:** completado · **creado:** 2026-11-04
- **resumen:** TT-04 motor de 10 estados (motor_calidad.py, migracion 051 con renombrado de estados legados), TT-05 reglas de validez parametrizables (saturacion simetrica, bajo limite, humedad minima, sonda fuera, plausibilidad), HU-02 endpoint de transparencia calidad-resumen. 20 tests. Contrato del sensor validado sin cambios (integracion 8/8).
- **archivos:** `apps/backend/agroia_backend/services/motor_calidad.py`

### ✅ Implementar epica E1 integridad de ingesta (RFP-003)

- **id:** `mem-20261104031919-41c56e-builder-implementar-epica-e1-integridad-de-ingesta-rfp-003`
- **skill:** `builder` · **estado:** completado · **creado:** 2026-11-04
- **resumen:** TT-01 decodificacion Modbus JXBS-3001 + CRC16 (15 tests), TT-02 firmware ESP32 (apps/iot/firmware), TT-03 verificacion de variante, HU-01 registro de dispositivos con configuracion (migracion 050).
- **archivos:** `apps/backend/agroia_backend/services/decodificacion_modbus.py`
