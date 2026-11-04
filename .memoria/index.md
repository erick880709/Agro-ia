# Memoria del proyecto

> Grafo de conocimiento generado por la skill `memoria`. Fuente de verdad: `.memoria/graph.json`.
> Este archivo se regenera; no lo edites a mano.

**12 nodo(s)** · **0 enlace(s)** · actualizado 2026-11-04T13:49:19.648Z

## Contexto activo

- **Actualizacion documentacion funcional y tecnica (RFP-003) y HTML** — `builder` · completado · 2026-11-04
  Actualizada DOCUMENTACION-PLATAFORMA.md (secciones 5-10: motor de calidad 10 estados, calibracion, grados de evidencia, seccion de evidencia en reportes, endpoints /iot y role checks) y generado DOCUMENTACION-PLATAFORMA.html autocontenido. Commit 9bc9180.
- **Desplegar RFP-003 y reclasificar finca carcel penas blancas** — `builder` · completado · 2026-11-04
  Despliegue a produccion (Render dep-dbli live, commit d5e9c6d, migraciones 050-057 aplicadas). Reclasificacion TT-16 de la finca 042217d5... con motor de 10 estados sin borrar: 100 invalidada -> 94 bajo_limite_deteccion + 4 saturada + 2 invalidada; total 202 filas intactas. Ahora 195 lecturas alimentan analisis (antes 102).
- **Revision CR-001 epicas E1-E9 RFP-003** — `code-review` · completado · 2026-11-04
  Code-review del paquete completo de 9 epicas: veredicto aprobado-con-observaciones. Hallazgo mayor de autorizacion corregido (exigir_no_cliente en escritura /iot, admin en parametros-calidad, /iot/sensor/raw publico). 3 menores (orden sonda/saturacion, migracion 051 sin reclasificar historico, str vs UUID) y 1 nit. Gate verde: 135 tests + ruff + integracion 8/8.
- **Implementar epica E9 aprendizaje automatico (RFP-003)** — `builder` · completado · 2026-11-04
  TT-14 entrenamiento solo con etiquetas de laboratorio (ml_entrenamiento.py: validar_sin_circularidad, evaluacion R2/RMSE/sesgo con covariables), TT-15 reporte de rendimiento por variable y unidad de suelo (/calibracion/rendimiento, migracion 057 unidad_suelo en par_calibracion) con modo sombra hasta cumplir metas (RT-034). 10 tests, integracion 8/8. Cierra las 9 epicas de RFP-AGROIA-003.
- **Implementar epica E8 ciclo de vida del sensor (RFP-003)** — `builder` · completado · 2026-11-04
  HU-14 plan de mantenimiento (modelo MantenimientoSensor + migracion 056 + endpoint POST /dispositivos/{id}/mantenimiento), TT-12 deteccion de deriva (detectar_deriva sesgo>meta), TT-13 telemetria de salud (voltaje y errores_crc en dispositivo + endpoint /telemetria, wire en consumer). 9 tests, integracion 8/8.
- **Implementar epica E7 reportes y pantallas (RFP-003)** — `builder` · completado · 2026-11-04
  HU-10 insignias de calidad/evidencia y leyenda metodologica (presentacion_reportes.py + endpoint /calidad/insignias), HU-11 series con banda de incertidumbre y puntos excluidos, HU-12 salud de sensores (salud_sensores.py + /sensores/{finca}/salud), HU-13 parametros administrables de calidad (modelo + migracion 055 + endpoints /parametros-calidad). 15 tests, integracion 8/8.
- **Implementar epica E6 grados de evidencia (RFP-003)** — `builder` · completado · 2026-11-04
  TT-11 grados de evidencia A/B/C/D (grados_evidencia.py: grado_laboratorio <90d, grado_sensor B/C, SIG D, puede_dosificar solo A/B), HU-08 cobertura explicita de variables no medidas con fuente, HU-09 recomendacion de muestreo. Integracion aditiva en orquestador (analyze adjunta grados_evidencia, variables_no_medidas, muestreo_recomendado). 16 tests, integracion 8/8.
- **Implementar epica E5 protocolo de muestreo y contexto (RFP-003)** — `builder` · completado · 2026-11-04
  HU-05 metadatos de muestreo (modelo SesionMuestreo + migracion 054 + campos profundidad/punto/replica/sesion en sensor_readings + endpoint /muestreo/sesiones), HU-06 contexto agronomico (contexto_agronomico.py, ventana post-fertilizacion/riego -> valida_con_advertencia, wire en consumer), HU-07 guia de campo (/muestreo/guia). 11 tests, integracion 8/8.
- **Implementar epica E4 calibracion local (RFP-003)** — `builder` · completado · 2026-11-04
  TT-08 modelo de calibracion por regresion lineal (calibracion.py + modelos calibracion_sensor/par_calibracion + migracion 053), TT-09 capa de equivalencia sensor-laboratorio (grado B/C), TT-10 aplicabilidad de humedad por suelo (arenoso/salino no aplicable), HU-04 endpoints /calibracion/pares y /calibracion/{device_id}. 13 tests, integracion 8/8.
- **Implementar epica E3 incertidumbre y clasificacion (RFP-003)** — `builder` · completado · 2026-11-04
  TT-06 incertidumbre por variable (incertidumbre.py, exactitud/raiz3, migracion 052, consumer guarda mapa de incertidumbres), TT-07 banda de frontera (banda_frontera.py + RulesEngine.evaluar_con_banda) y agregacion robusta (agregacion_robusta.py, mediana/IQR/minimo puntos), HU-03 presentacion con incertidumbre (formatear_valor). 26 tests, integracion 8/8.

## Avances

### ✅ Actualizacion documentacion funcional y tecnica (RFP-003) y HTML

- **id:** `mem-20261104134919-6aa278-builder-actualizacion-documentacion-funcional-y-tecnica-rfp`
- **skill:** `builder` · **estado:** completado · **creado:** 2026-11-04
- **resumen:** Actualizada DOCUMENTACION-PLATAFORMA.md (secciones 5-10: motor de calidad 10 estados, calibracion, grados de evidencia, seccion de evidencia en reportes, endpoints /iot y role checks) y generado DOCUMENTACION-PLATAFORMA.html autocontenido. Commit 9bc9180.
- **archivos:** `DOCUMENTACION-PLATAFORMA.md`

### ✅ Desplegar RFP-003 y reclasificar finca carcel penas blancas

- **id:** `mem-20261104132531-cca2eb-builder-desplegar-rfp-003-y-reclasificar-finca-carcel-penas`
- **skill:** `builder` · **estado:** completado · **creado:** 2026-11-04
- **resumen:** Despliegue a produccion (Render dep-dbli live, commit d5e9c6d, migraciones 050-057 aplicadas). Reclasificacion TT-16 de la finca 042217d5... con motor de 10 estados sin borrar: 100 invalidada -> 94 bajo_limite_deteccion + 4 saturada + 2 invalidada; total 202 filas intactas. Ahora 195 lecturas alimentan analisis (antes 102).
- **archivos:** `apps/backend/agroia_backend/services/motor_calidad.py`

### ✅ Revision CR-001 epicas E1-E9 RFP-003

- **id:** `mem-20261104131024-6c1a07-code-review-revision-cr-001-epicas-e1-e9-rfp-003`
- **skill:** `code-review` · **estado:** completado · **creado:** 2026-11-04
- **resumen:** Code-review del paquete completo de 9 epicas: veredicto aprobado-con-observaciones. Hallazgo mayor de autorizacion corregido (exigir_no_cliente en escritura /iot, admin en parametros-calidad, /iot/sensor/raw publico). 3 menores (orden sonda/saturacion, migracion 051 sin reclasificar historico, str vs UUID) y 1 nit. Gate verde: 135 tests + ruff + integracion 8/8.
- **archivos:** `docs/reviews/CR-001-epicas-rfp003.md`

### ✅ Implementar epica E9 aprendizaje automatico (RFP-003)

- **id:** `mem-20261104125937-18adfb-builder-implementar-epica-e9-aprendizaje-automatico-rfp-003`
- **skill:** `builder` · **estado:** completado · **creado:** 2026-11-04
- **resumen:** TT-14 entrenamiento solo con etiquetas de laboratorio (ml_entrenamiento.py: validar_sin_circularidad, evaluacion R2/RMSE/sesgo con covariables), TT-15 reporte de rendimiento por variable y unidad de suelo (/calibracion/rendimiento, migracion 057 unidad_suelo en par_calibracion) con modo sombra hasta cumplir metas (RT-034). 10 tests, integracion 8/8. Cierra las 9 epicas de RFP-AGROIA-003.
- **archivos:** `apps/backend/agroia_backend/services/ml_entrenamiento.py`

### ✅ Implementar epica E8 ciclo de vida del sensor (RFP-003)

- **id:** `mem-20261104125458-b30e90-builder-implementar-epica-e8-ciclo-de-vida-del-sensor-rfp-00`
- **skill:** `builder` · **estado:** completado · **creado:** 2026-11-04
- **resumen:** HU-14 plan de mantenimiento (modelo MantenimientoSensor + migracion 056 + endpoint POST /dispositivos/{id}/mantenimiento), TT-12 deteccion de deriva (detectar_deriva sesgo>meta), TT-13 telemetria de salud (voltaje y errores_crc en dispositivo + endpoint /telemetria, wire en consumer). 9 tests, integracion 8/8.
- **archivos:** `apps/backend/agroia_backend/services/ciclo_vida_sensor.py`

### ✅ Implementar epica E7 reportes y pantallas (RFP-003)

- **id:** `mem-20261104125057-109ed8-builder-implementar-epica-e7-reportes-y-pantallas-rfp-003`
- **skill:** `builder` · **estado:** completado · **creado:** 2026-11-04
- **resumen:** HU-10 insignias de calidad/evidencia y leyenda metodologica (presentacion_reportes.py + endpoint /calidad/insignias), HU-11 series con banda de incertidumbre y puntos excluidos, HU-12 salud de sensores (salud_sensores.py + /sensores/{finca}/salud), HU-13 parametros administrables de calidad (modelo + migracion 055 + endpoints /parametros-calidad). 15 tests, integracion 8/8.
- **archivos:** `apps/backend/agroia_backend/services/presentacion_reportes.py`

### ✅ Implementar epica E6 grados de evidencia (RFP-003)

- **id:** `mem-20261104124658-b33b30-builder-implementar-epica-e6-grados-de-evidencia-rfp-003`
- **skill:** `builder` · **estado:** completado · **creado:** 2026-11-04
- **resumen:** TT-11 grados de evidencia A/B/C/D (grados_evidencia.py: grado_laboratorio <90d, grado_sensor B/C, SIG D, puede_dosificar solo A/B), HU-08 cobertura explicita de variables no medidas con fuente, HU-09 recomendacion de muestreo. Integracion aditiva en orquestador (analyze adjunta grados_evidencia, variables_no_medidas, muestreo_recomendado). 16 tests, integracion 8/8.
- **archivos:** `apps/backend/agroia_backend/services/grados_evidencia.py`

### ✅ Implementar epica E5 protocolo de muestreo y contexto (RFP-003)

- **id:** `mem-20261104123708-3630ca-builder-implementar-epica-e5-protocolo-de-muestreo-y-context`
- **skill:** `builder` · **estado:** completado · **creado:** 2026-11-04
- **resumen:** HU-05 metadatos de muestreo (modelo SesionMuestreo + migracion 054 + campos profundidad/punto/replica/sesion en sensor_readings + endpoint /muestreo/sesiones), HU-06 contexto agronomico (contexto_agronomico.py, ventana post-fertilizacion/riego -> valida_con_advertencia, wire en consumer), HU-07 guia de campo (/muestreo/guia). 11 tests, integracion 8/8.
- **archivos:** `apps/backend/agroia_backend/services/contexto_agronomico.py`

### ✅ Implementar epica E4 calibracion local (RFP-003)

- **id:** `mem-20261104121447-77dccf-builder-implementar-epica-e4-calibracion-local-rfp-003`
- **skill:** `builder` · **estado:** completado · **creado:** 2026-11-04
- **resumen:** TT-08 modelo de calibracion por regresion lineal (calibracion.py + modelos calibracion_sensor/par_calibracion + migracion 053), TT-09 capa de equivalencia sensor-laboratorio (grado B/C), TT-10 aplicabilidad de humedad por suelo (arenoso/salino no aplicable), HU-04 endpoints /calibracion/pares y /calibracion/{device_id}. 13 tests, integracion 8/8.
- **archivos:** `apps/backend/agroia_backend/services/calibracion.py`

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
