# RFP-AGROIA-003 — Plataforma confiable de medición de suelo con el sensor JXBS-3001-NPK-RS

**Proyecto AGROINTELIGENTE COLOMBIA · AgroIA · Versión 1.0 · 3 de noviembre de 2026** Base del análisis: *DOCUMENTACION-PLATAFORMA* (estado al 2026-11-03), manual JXBS-3001 v2.0 (RS485 Modbus) y tabla de especificaciones técnicas del sensor.

## 1. Resumen ejecutivo

AgroIA ya hace varias cosas bien: valida rangos del sensor, da prioridad al laboratorio sobre el sensor, excluye lecturas inválidas de los reportes y respeta el principio *sin análisis de suelo no hay dosis*. El problema es que **trata cada lectura del sensor como un valor exacto y equivalente a un análisis de laboratorio**, y el sensor no lo es.

Visto como agrónomo, el JXBS-3001 es un **instrumento de monitoreo y tamizaje**: excelente para temperatura, útil para humedad y pH con calibración local, y solo *indicativo* para N, P y K. Mide 7 de las 18 variables que maneja la plataforma y no mide nada de lo que define la fertilidad en suelos andinos (materia orgánica, CIC, Ca, Mg, Al, S, micronutrientes, textura).

Este RFP pide convertir AgroIA en una plataforma de medición confiable mediante: (1) decodificación fiel del dato crudo, (2) un motor de calidad más fino que "válida/inválida", (3) **propagación de la incertidumbre del sensor** a las reglas y reportes, (4) calibración local contra laboratorio, (5) protocolo de muestreo con metadatos, (6) grados de evidencia visibles en cada recomendación y (7) gestión del ciclo de vida del sensor.

**Hallazgos críticos (resumen):**

- La exactitud de NPK es ±2 % del fondo de escala (1999 mg/kg): **±40 mg/kg**, del mismo orden que los valores reales de P y K de muchos suelos. Hoy las reglas son deterministas y ignoran ese error.
- El N, P y K del sensor **no equivalen** a los métodos de laboratorio con los que están escritos los umbrales (MO/N total, Bray II, K intercambiable en cmol(+)/kg). La calibración actual es un solo factor por dispositivo.
- La calibración de fábrica es para suelos tipo loess, negro y rojo; **no** es para arenosos ni salinos, y los andisoles cafeteros no están validados.
- pH, CE y NPK dependen de que la sonda esté bien enterrada y el suelo húmedo; hoy no hay validación de contexto.

## 2. Estado actual relevante de la plataforma

- **Ingesta:** `POST /sensor`, `/iot/ingest` y consumidor RabbitMQ (`apps/iot`); normalización de tramas, GPS a metros relativos, calibración NPK por dispositivo con marca `npk_no_calibrado`.
- **Regla del sensor:** pH 3–9 (excluye 9,0), CE 0,01–10 dS/m, NPK 1–1.999 mg/kg y coordenada por defecto del firmware; lo demás se marca `calidad = invalidada` y queda fuera de análisis y reportes.
- **Fuentes:** `sensor_readings` con 18 variables y campo `calidad`; laboratorio prioritario (<90 días); SIG IGAC/UPRA como `estimado_por_sig`.
- **Motor:** reglas con fuente (UPRA/Cenicafé/AGROSAVIA), ML en modo sombra, confianza con cobertura de datos, validación humana.
- **Reportes:** mapa de calor, plano con puntos de muestreo, recomendaciones y plan económico, solo con lecturas válidas.

## 3. Qué es realmente el sensor

| Variable | Registro (Modbus) | Rango | Exactitud | Resolución | Lectura agronómica |
| --- | --- | --- | --- | --- | --- |
| Temperatura | 0x0013 (0,1 °C, con signo) | −40 a 80 °C | ±0,5 °C | 0,1 °C | Confiable. Evitar sol directo sobre la sonda. |
| Humedad | 0x0012 (0,1 %) | 0–100 % | ±3 % (0–53 %); ±5 % (53–100 %) | 0,1 % | Es contenido volumétrico (VWC), no humedad relativa ni gravimétrica. |
| CE | 0x0015 (1 µS/cm) | 0–10 000 µS/cm | **No especificada** | 10 µS/cm | CE aparente del suelo, no CE del extracto saturado (CEe). |
| pH | 0x0006 (0,01) | 3–9 | ±0,3 | 0,01 | pH in situ; difiere del pH de laboratorio (1:1 o 1:2,5). |
| N, P, K | 0x001E, 0x001F, 0x0020 (mg/kg) | 0–1999 mg/kg | ±2 % F.S. (≈ ±40 mg/kg) | 1 mg/kg | Indicativo; correlacionado con CE y humedad, no con los métodos de laboratorio. |

Otros datos del manual que condicionan el uso: respuesta <1 s, IP68, presión 0,9–1,1 atm, Modbus RTU 9600 8N1 (función 0x03), dirección por defecto 0x01 configurable (registro 0x0100), hasta más de 16 sensores por bus.

**Lo que el sensor no mide:** materia orgánica, CIC, textura, Ca, Mg, Na, Al y acidez intercambiable, S, B, Zn, Cu, Fe, Mn. Esas variables solo pueden venir de laboratorio, SIG o modelo, y la plataforma debe decirlo explícitamente.

## 4. Hallazgos

| ID | Sev. | Hallazgo | Impacto agronómico |
| --- | --- | --- | --- |
| H-01 | Crítica | Reglas deterministas sin incertidumbre. Un pH de 5,4 ±0,3 o un K de 60 ±40 mg/kg se clasifican como si fueran exactos. | Clasificaciones de aptitud y alertas inestables cerca de los umbrales. |
| H-02 | Crítica | NPK del sensor no es equivalente a Bray II, K intercambiable ni a MO/N total. Los umbrales de Cenicafé/UPRA están en unidades de laboratorio (p. ej. K en cmol(+)/kg; 1 cmol(+)/kg ≈ 391 mg/kg). La calibración es un factor multiplicativo único. | Comparar mg/kg del sensor contra umbrales de laboratorio produce recomendaciones erróneas. |
| H-03 | Crítica | El sensor cubre 7 de 18 variables. Relaciones Ca/Mg/K, Al, MO y CIC no son medibles con él. | Riesgo de rellenar con valores por defecto o de mezclar fuentes sin avisar en el reporte. |
| H-04 | Alta | No hay validación del contexto de medición: sonda en aire, suelo seco o sin contacto. El manual advierte que la aguja debe estar enterrada y que no conviene energizar el sensor al aire. | pH, CE y NPK espurios que pasan el filtro de rango. |
| H-05 | Alta | La humedad es VWC con calibración de fábrica para loess, negro y rojo; no apta para arenosos ni salinos. Los andisoles (cenizas volcánicas) del Eje Cafetero y otros suelos del catálogo (45 cultivos) no están validados. | Humedad sesgada; no se convierte a agua disponible ni a déficit hídrico. |
| H-06 | Alta | CE sin exactitud declarada, es CE aparente y no se documenta compensación por temperatura. Los umbrales de salinidad son en CEe (dS/m). | Falsos positivos o negativos de salinidad. |
| H-07 | Alta | Falsa precisión: se muestran 0,01 de pH y 1 mg/kg de NPK, cuando la exactitud real es ±0,3 y ±40. | El usuario interpreta diferencias que son ruido. |
| H-08 | Alta | Muestreo: el manual recomienda promediar varias mediciones. La plataforma tiene posición x/y pero no réplicas, profundidad, modo de instalación ni puntos mínimos para interpolar el mapa de calor. | Mapas y promedios por lote no representativos. |
| H-09 | Alta | ML en modo sombra: riesgo de circularidad si las etiquetas derivan de reglas aplicadas al propio sensor, y de entrenar con ruido sin modelarlo. | "Acuerdo" ML–reglas que no valida nada. |
| H-10 | Media | Límites asimétricos: se excluye pH 9,0 pero no pH ≤3,0, CE ≥10 dS/m ni NPK ≥1999 (todos saturación). Y un 0 en CE o NPK es "bajo el límite de detección", no necesariamente inválido; hoy se descarta información. | Se pierde la señal de suelos realmente pobres o se aceptan lecturas saturadas. |
| H-11 | Media | Sin metadatos de contexto: fertilización, riego o lluvia reciente elevan CE y NPK en horas. | Picos de nutrientes interpretados como fertilidad del suelo. |
| H-12 | Media | Decodificación: temperatura en complemento a dos (p. ej. 0xFF9B = −10,1 °C), escalas distintas por registro, cada valor de 16 bits. No se guarda el valor crudo. | Errores silenciosos de escala o signo sin posibilidad de auditoría. |
| H-13 | Media | Inconsistencias del manual: portada "JXBS-3001-TR-RS" frente a "NPK-RS"; alimentación 12 V por defecto (5/3,3 V opcional) frente a 12–24 V; ejemplos de tramas con CRC y registros inconsistentes (probable conversión del PDF). | Compra o cableado de una variante equivocada; pruebas con vectores no confiables. |
| H-14 | Media | Sin gestión de vida útil: deriva de electrodos, recalibración y mantenimiento. | Degradación lenta no detectada. |
| H-15 | Baja | Bus multi-sensor: direcciones únicas y mapeo dirección ↔ sensor ↔ lote ↔ profundidad no modelado. | Lecturas atribuidas al lote o profundidad equivocados. |

## 5. Objetivo y alcance

**Objetivo:** que cada medición de suelo que llega a un reporte o recomendación tenga origen trazable, calidad evaluada, incertidumbre explícita y un grado de evidencia que limite lo que se puede concluir con ella.

**Dentro del alcance:** firmware y trama del ESP32, ingesta, modelo de datos, motor de calidad, motor de reglas y orquestador (consumo de incertidumbre), calibración, reportes y pantallas, administración de parámetros, campaña de validación en campo, monitoreo del sensor.

**Fuera del alcance:** reemplazo del sensor, nuevos tipos de sensor, recetas de dosis sin laboratorio (se mantiene el principio de dominio), rediseño del asesor conversacional.

**Principios:**

1. El valor crudo se conserva siempre; nada se borra, solo se clasifica.
2. Todo umbral, rango y tolerancia es un **parámetro administrable** (Administración → Parámetros), no un valor fijo en el código.
3. Lo no medido se declara "no medido"; nunca se rellena en silencio.
4. Sin laboratorio no hay dosis; el sensor sustenta tendencias, alertas y priorización de muestreo.

## 6. Requerimientos

### Épica E1 — Integridad de la ingesta

- **RF-01 Decodificación fiel.** El consumidor decodifica los registros 0x0006, 0x0012, 0x0013, 0x0015, 0x001E–0x0020 con sus escalas; temperatura como entero con signo de 16 bits. Se almacena `valor_crudo` (entero), `valor_escalado` y la unidad.
- **RF-02 Conversión de unidades.** CE se normaliza a dS/m (µS/cm ÷ 1000); humedad se etiqueta como VWC (%), nunca como "HR".
- **RF-03 Firmware.** Validar CRC y reintentar (máx. N, parametrizable), timeout por sensor, múltiples lecturas por punto, hora desde NTP o RTC, buffer offline con idempotencia, versión de firmware en cada trama. Requiere transceptor RS485 y alimentación de 12 V (el ESP32 es de 3,3 V lógico).
- **RF-04 Registro de sensores.** Por dispositivo: modelo y variante, dirección Modbus, baudios, fecha de instalación, profundidad, modo (superficial o enterrado), lote y último mantenimiento. Unicidad dirección ↔ bus.
- **RF-05 Verificación de variante.** Prueba de aceptación que lee todos los registros del equipo recibido y confirma que expone pH, CE, N, P y K antes de dar de alta el dispositivo (ver H-13).

### Épica E2 — Motor de calidad del dato

- **RF-06 Estados de calidad ampliados:** `valida`, `valida_con_advertencia`, `bajo_limite_deteccion`, `saturada`, `fuera_de_rango`, `sonda_fuera_de_suelo`, `humedad_insuficiente`, `no_calibrada`, `estimado_sig`, `invalidada`. Cada lectura guarda la lista de motivos y la versión de la regla aplicada.
- **RF-07 Saturación simétrica.** pH ≤ límite inferior o ≥ límite superior, CE ≥ 10 dS/m y N, P o K ≥ 1999 se marcan `saturada`. Un 0 en CE o NPK se marca `bajo_limite_deteccion` y se conserva para análisis con su incertidumbre, sin tratarlo como error.
- **RF-08 Validez por humedad.** Si VWC está por debajo de un mínimo parametrizable (valor inicial 15 %, a confirmar en campo), pH, CE y NPK pasan a `humedad_insuficiente`. Humedad y CE cercanas a 0 simultáneamente indican `sonda_fuera_de_suelo`.
- **RF-09 Plausibilidad cruzada.** Reglas parametrizables: saltos de temperatura incompatibles con la inercia del suelo, temperatura >45 °C (sol directo), NPK alto con CE ≈ 0, variación entre réplicas del mismo punto fuera de tolerancia (detección con mediana y MAD).
- **RF-10 Transparencia.** Cada reporte indica "N de M lecturas válidas" y cuántas se excluyeron por cada motivo. Las excluidas siguen consultables en administración.

### Épica E3 — Incertidumbre y clasificación

- **RF-11 Incertidumbre por variable.** Tabla parametrizable (valores iniciales en el Anexo A). Se calcula la incertidumbre estándar con criterio de distribución rectangular (exactitud/√3) y se guarda con la lectura. Para humedad se usa la exactitud por tramo (±3 / ±5).
- **RF-12 Clasificación con banda de frontera.** Si |valor − umbral| ≤ exactitud, la clase se informa como **"indeterminada (frontera)"**, con la probabilidad estimada de cada clase. El motor de reglas y el orquestador consumen esa salida; la confianza (incluido el umbral duro de 80 %) incorpora la incertidumbre medida.
- **RF-13 Precisión de presentación.** pH a 0,1 (±0,3), N, P y K redondeados a la incertidumbre (p. ej. decenas de mg/kg), humedad a 1 %, CE a 0,01 dS/m. Se muestra siempre el intervalo, no solo el valor.
- **RF-14 Agregación robusta.** Valor por punto = mediana de réplicas; valor por lote = estadístico con intervalo; el mapa de calor solo se genera con un mínimo parametrizable de puntos válidos y muestra la incertidumbre de interpolación.

### Épica E4 — Calibración local

- **RF-15 Modelo de calibración.** Sustituir el factor único por regresión lineal (pendiente e intercepto) por dispositivo, variable y unidad de suelo, con n, R², RMSE, sesgo, vigencia y responsable. Se mantiene el historial.
- **RF-16 Capa de equivalencia sensor ↔ laboratorio.** Las reglas se evalúan en la unidad del laboratorio (K en cmol(+)/kg; P por Bray II; N a partir de MO). La conversión usa la calibración vigente; sin calibración, la variable queda en grado C y no alimenta clasificaciones definitivas.
- **RF-17 Campaña de calibración.** Flujo en la aplicación para registrar pares sensor–laboratorio: muestra compuesta del mismo punto y profundidad el mismo día, método de laboratorio, laboratorio, fecha. Alertas de calibración vencida.
- **RF-18 Calibración de humedad por suelo.** Curva VWC del sensor vs. gravimétrico × densidad aparente por unidad de suelo (en el Eje Cafetero, al menos andisoles). Conversión a agua disponible y estado hídrico usando capacidad de campo y punto de marchitez por textura (de laboratorio o SIG).
- **RF-19 CE.** Caracterizar con soluciones patrón (p. ej. 1413 µS/cm), normalizar a 25 °C si el sensor no lo hace, y calibrar CE aparente ↔ CEe/CE 1:5 por suelo para evaluar salinidad.

### Épica E5 — Protocolo de muestreo y contexto

- **RF-20 Metadatos por lectura o sesión:** profundidad (cm), modo de instalación, número de réplica, pedregosidad del punto, tiempo de estabilización, observaciones y foto opcional.
- **RF-21 Contexto agronómico:** fecha de última fertilización, riego y lluvia (IDEAM o pluviómetro). Lecturas dentro de una ventana parametrizable posterior a fertilización o riego se marcan `valida_con_advertencia` y no se usan para clasificar fertilidad.
- **RF-22 Guía de campo en la app:** mínimo de réplicas por punto, inserción vertical sin balanceo, evitar piedras, profundidad por cultivo (zona radical), pozo >20 cm de diámetro para instalación enterrada, horario de lectura recomendado.
- **RF-23 Aplicabilidad por suelo.** Si el lote está marcado arenoso o con CE alta, la humedad del sensor pasa a `no_calibrada` hasta que exista calibración propia.

### Épica E6 — Interpretación y grados de evidencia

- **RF-24 Grados de evidencia.** A: laboratorio vigente (<90 días). B: sensor con calibración local vigente que cumple metas. C: sensor sin calibración local (indicativo). D: estimado SIG o modelo. Cada dato, clasificación y recomendación exhibe su grado.
- **RF-25 Reglas por grado.** Dosis de fertilización y clasificación definitiva solo con A (o B en variables que cumplan metas). Con C: tendencias, alertas y priorización de dónde muestrear. Se mantiene el principio de dominio de no dosificar sin análisis.
- **RF-26 Cobertura explícita.** El reporte tiene una sección "Variables no medidas" (MO, CIC, textura, Ca, Mg, Al, S, micros) con su fuente (laboratorio, SIG o ninguna). Las reglas de antagonismo y relaciones catiónicas se omiten, indicándolo, cuando falten sus insumos.
- **RF-27 Recomendación de muestreo de laboratorio.** Cuando el sensor detecta anomalías o variables en frontera, el sistema sugiere puntos concretos de muestreo para laboratorio, alineado con la comisión de muestreo en grilla y el módulo de costos.

### Épica E7 — Reportes y pantallas

- **RF-28** Reporte con valores ± incertidumbre, insignias de calidad y de grado de evidencia, y leyenda metodológica (qué mide el sensor y qué no).
- **RF-29** Series de tiempo con banda de incertidumbre, marcadores de eventos (riego, fertilización, lluvia) y puntos excluidos visibles en gris.
- **RF-30** Pantalla de salud de sensores: última lectura, tasa de lecturas válidas, deriva frente a laboratorio, calibración vigente, próximo mantenimiento.
- **RF-31** Administración de parámetros de calidad (rangos, saturación, humedad mínima, tolerancias, ventanas de contexto, incertidumbres) con auditoría de cambios y versionado de la regla.

### Épica E8 — Ciclo de vida del sensor

- **RF-32** Contrastes periódicos sensor–laboratorio y detección de deriva (alerta cuando el sesgo supera la meta).
- **RF-33** Plan de mantenimiento: limpieza, revisión de agujas y cable, reemplazo; registro por dispositivo.
- **RF-34** Telemetría de salud: voltaje de alimentación, tasa de errores CRC, tiempo sin reportar.

### Épica E9 — Aprendizaje automático

- **RF-35** Entrenar y evaluar los modelos con etiquetas de laboratorio, nunca con salidas de reglas aplicadas al mismo sensor. Incluir las covariables de contexto (humedad, temperatura, CE) y la incertidumbre.
- **RF-36** Reportar el rendimiento del modelo por grado de evidencia y por unidad de suelo; mantener modo sombra hasta cumplir metas.

## 7. Requerimientos no funcionales

- **Trazabilidad:** versión de regla, calibración y firmware asociadas a cada lectura; reproducibilidad de cualquier reporte.
- **Compatibilidad:** migraciones Alembic reversibles; las lecturas históricas se reclasifican con un proceso por lotes, sin borrar nada.
- **Rendimiento:** la evaluación de calidad no agrega más de 100 ms por trama; reproceso histórico por lotes.
- **Seguridad y privacidad:** se mantienen RLS, roles y auditoría vigentes.
- **Operación offline:** el firmware y la PWA conservan la idempotencia existente.
- **Pruebas:** cobertura unitaria de decodificación y reglas con vectores propios (incluidos temperaturas negativas y saturaciones).

## 8. Cambios al modelo de datos

- **`sensor_readings`:** `valor_crudo`, `valor_escalado`, `valor_normalizado`, `unidad`, `incertidumbre`, `calidad` (enum ampliado), `motivos_calidad[]`, `version_regla`, `grado_evidencia`, `profundidad_cm`, `punto_id`, `replica_n`, `sesion_muestreo_id`, `vwc_pct`, `ce_25c_dsm`.
- **`dispositivos_iot`:** `modelo`, `variante`, `direccion_modbus`, `baudios`, `firmware`, `fecha_instalacion`, `profundidad_cm`, `modo_instalacion`, `lote_id`, `ultimo_mantenimiento`, `estado_salud`.
- **Nuevas tablas:** `calibracion_sensor` (dispositivo, variable, unidad de suelo, pendiente, intercepto, n, R², RMSE, sesgo, vigencia), `par_calibracion` (lectura de sensor y resultado de laboratorio con método), `sesion_muestreo` (punto, réplicas, contexto de fertilización y riego, observaciones), `parametro_calidad_sensor` (parámetros administrables con versión).

## 9. Validación y criterios de aceptación

**Técnica:** 100 % de los vectores de prueba decodificados correctamente (incluida temperatura negativa); cero lecturas `invalidada`, `saturada` o `humedad_insuficiente` en reportes; todo reporte con grado de evidencia y variables no medidas declaradas; reclasificación histórica sin pérdida de registros.

**Campaña de campo (en paralelo a las fases 2 y 3):** al menos 30 pares sensor–laboratorio por unidad de suelo y variable, cubriendo el rango de valores, con laboratorio acreditado y métodos declarados. Metas iniciales **a validar** (si no se cumplen, la variable permanece en grado C):

| Variable | Meta contra referencia |
| --- | --- |
| pH | Sesgo ≤ 0,3 y RMSE ≤ 0,4 frente a pH en agua 1:1 |
| Humedad | RMSE ≤ 5 puntos de VWC frente a gravimétrico × densidad aparente |
| CE | R² ≥ 0,8 frente a CE 1:5 o CEe |
| N, P, K | R² ≥ 0,6 en el rango del suelo; de lo contrario, solo tendencia |

Esas metas son una propuesta de partida: se ajustan con el equipo agronómico antes de iniciar la campaña.

## 10. Fases y esfuerzo estimado

Estimación inicial en persona-días (sujeta a refinamiento en el kickoff).

| Fase | Contenido | Esfuerzo |
| --- | --- | --- |
| 0. Verificación | RF-05, lectura de registros del equipo real, vectores de prueba, confirmación de variante y alimentación (H-13) | 3–5 |
| 1. Integridad | E1 y estados de calidad E2 (RF-06 a RF-10), reclasificación histórica | 12–18 |
| 2. Incertidumbre | E3 y grados de evidencia (RF-24, RF-25, RF-26), ajustes al motor de reglas y al orquestador | 15–22 |
| 3. Calibración | E4, E5 y campaña de campo (aplicación + laboratorio + análisis) | 20–30 más campaña |
| 4. Reportes y UI | E7, parámetros administrables (RF-31) | 10–15 |
| 5. Ciclo de vida y ML | E8 y E9 | 10–14 |

La campaña de laboratorio tiene costo externo adicional y condiciona el cierre de la fase 3.

## 11. Riesgos

- **Metas de calibración no alcanzadas para NPK:** se mitiga declarándolo como indicativo y priorizando el laboratorio; el sistema funciona igual.
- **Costo y tiempo de laboratorio:** coordinar con la comisión de muestreo en grilla y el módulo de costos para amortizarlo.
- **Variante de sensor equivocada o diferente a la documentada:** resuelto con la fase 0.
- **Sobrecarga de señales para el usuario final:** diseñar la UI con un resumen de una línea ("confiable / indicativo / sin datos") y detalle bajo demanda.
- **Reclasificación histórica que altere reportes ya entregados:** conservar la versión de regla vigente al momento de emisión.

## 12. Entregables

1. Código y migraciones de las épicas E1 a E9 con pruebas automatizadas.
2. Documento de calibración y protocolo de campo (guía del técnico).
3. Informe de resultados de la campaña y de las metas por variable.
4. Pantalla de administración de parámetros y pantalla de salud de sensores.
5. Reporte actualizado con incertidumbre, calidad, grado de evidencia y variables no medidas.
6. Actualización de *DOCUMENTACION-PLATAFORMA* y del catálogo funcional.

## 13. Supuestos y preguntas abiertas

1. ¿Qué referencia exacta tiene el sensor adquirido (etiqueta del equipo) y qué variante de alimentación?
2. ¿Qué laboratorio y qué métodos usará la campaña (pH, MO, Bray II, K intercambiable, CE)?
3. ¿Qué unidades de suelo se priorizan para calibrar (andisoles cafeteros primero)?
4. ¿Se instalarán sensores enterrados de forma permanente o solo se usarán en muestreo superficial por puntos?
5. ¿Hay profundidad estándar por cultivo definida por el equipo agronómico?

## Anexo A — Reglas de validación e incertidumbre propuestas (valores iniciales parametrizables)

| Variable | Escala | Rango útil | Saturación o límite de detección | Incertidumbre inicial | Notas |
| --- | --- | --- | --- | --- | --- |
| Temperatura | 0,1 °C, con signo | −40 a 80 °C | — | ±0,5 °C | Alerta >45 °C (sol directo). |
| Humedad VWC | 0,1 % | 0–100 % | 0 con CE≈0: sonda fuera del suelo | ±3 % (≤53 %); ±5 % (>53 %) | Calibrar por suelo; no apta para arenosos ni salinos. |
| pH | 0,01 | >3,00 y <9,00 | ≤3,00 y ≥9,00 saturada | ±0,3 | Requiere humedad mínima. |
| CE | 1 µS/cm (resolución 10) | 10 a <10 000 µS/cm | 0: bajo detección; ≥10 000: saturada | Por caracterizar (no especificada) | Normalizar a 25 °C; CE aparente, no CEe. |
| N, P, K | 1 mg/kg | 1 a <1999 mg/kg | 0: bajo detección; ≥1999: saturada | ±40 mg/kg (2 % de 1999) | Indicativo hasta calibrar; sensible a CE y humedad. |
