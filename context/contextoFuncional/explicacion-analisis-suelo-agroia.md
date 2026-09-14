# AgroIA — Explicación funcional del análisis de suelo

> Documento de divulgación generado a partir del contexto funcional vigente (Documento Funcional-Técnico v3.5, RFP AgroInteligente Colombia, especificaciones v3.0/v4/v8 y estado del proyecto v0.2.0).
> **Propósito:** explicar en lenguaje claro todo lo que la plataforma puede hacer con el análisis del suelo y cómo beneficia al agricultor en dos momentos clave: **antes de sembrar** (¿qué me conviene sembrar?) y **con el cultivo ya sembrado** (¿dónde abono, dónde riego y qué me dicen los datos?).

---

## 1. Resumen ejecutivo

AgroIA es una **plataforma de agricultura de precisión** que funciona como un **agrónomo virtual** para el campo colombiano. Recibe mediciones del suelo (sensores IoT, archivos, análisis de laboratorio ICA y estimaciones oficiales IGAC/UPRA), las cruza con clima, geografía y conocimiento agronómico (UPRA, Cenicafé, AGROSAVIA), y entrega:

- **Antes de sembrar:** un ranking de cultivos aptos para ese suelo, con rentabilidad estimada.
- **Con cultivo sembrado:** un diagnóstico por variable (qué falta, qué sobra), un plan de fertilización, un mapa de **dónde abonar** en el lote, el cálculo de **cuándo y cuánto regar**, alertas climáticas y una predicción de rendimiento.

Principios que rigen toda la plataforma:

| Principio | Qué significa para el agricultor |
|---|---|
| **Nunca se bloquea por datos faltantes** | Si el sensor no mide algo, el análisis sigue y dice honestamente qué falta y qué certeza tiene. |
| **El sistema experto manda** | Las reglas agronómicas (UPRA/Cenicafé/AGROSAVIA) son la fuente de verdad; la IA apoya sin arriesgar. |
| **Honestidad técnica** | Cada dato muestra si es medido, estimado o validado en laboratorio; la confianza se explica con semáforos. |
| **Trazabilidad total** | Toda acción queda auditada (quién, qué, cuándo) para certificaciones BPA. |

---

## 2. ¿De dónde salen los datos del suelo?

El motor analiza hasta **18 variables**: pH, nitrógeno, fósforo, potasio, calcio, magnesio, azufre, hierro, manganeso, zinc, cobre, boro, materia orgánica, CIC, textura, humedad del suelo, temperatura del suelo y conductividad eléctrica.

| Fuente | Cómo llega | Ventaja |
|---|---|---|
| **Sensores IoT en campo** | Trama del firmware vía `POST /api/sensor` (pH, CE, NPK, humedad/temperatura de suelo y ambiente, GPS de la toma) | Lecturas continuas, georreferenciadas por punto de toma (`pos_x/pos_y` → mapa del lote) |
| **Carga de archivo** | CSV, TXT o JSON con mediciones tomadas a mano | Sirve cuando el sensor perdió conexión; dispara el análisis al instante |
| **Laboratorio ICA** | Ingesta del informe de laboratorio (ventana de 90 días) | **Fuente de verdad**: valida N/P/K/pH/MO y quita la penalización por sensor sin calibrar |
| **SIG IGAC/UPRA** | Enriquecimiento automático al registrar la finca con su polígono | Prellena textura, materia orgánica y CIC con datos oficiales si el sensor no los mide |

**Regla de precedencia:** el laboratorio gana al sensor y el sensor gana a la estimación SIG. La lectura usada indica su origen («Validado en laboratorio», «Calibrado de fábrica», «Estimado por SIG (IGAC/UPRA)») y su antigüedad («🕒 Última toma hace X días»).

---

## 3. Escenario A — Antes de sembrar: «¿Qué me conviene sembrar aquí?»

El agricultor elige su finca, pulsa **«🧪 Analizar suelo»** y recibe una respuesta que combina ciencia del suelo y economía.

### 3.1 Ranking de cultivos aptos (UC1)

El motor evalúa el suelo contra las reglas de **cada cultivo del catálogo** (hoy 45 cultivos activos, con reglas específicas para café, maíz, papa, plátano, arroz, aguacate, cacao, fríjol, tomate, yuca, entre otros) y entrega un **top 5** con:

- **Score de aptitud (0–100)** calculado por las desviaciones del suelo frente al rango ideal de cada variable.
- **Clasificación UPRA:** 🟢 Apta (≥80) · Moderadamente apta (≥60) · Marginalmente apta (≥40) · No apta (<40).
- **Ajustes por cultivo:** qué variable está fuera de rango y qué hacer para corregirla (ej. «pH 4.9 — requiere encalado para café [5.5–6.5]»).
- **Fisiología del cultivo:** si la profundidad efectiva del lote es menor que la raíz que el cultivo necesita, se penaliza con un ajuste explícito.

**Beneficio:** elimina la siembra «a ciegas»; el productor ve *por qué* un cultivo es apto o no y qué le costaría corregir el suelo.

### 3.2 Rentabilidad, no solo aptitud

El ranking se enriquece con **precios de cosecha por departamento**:

- Calcula `ingreso bruto estimado` (rendimiento × precio) y `utilidad estimada por hectárea`.
- Recalcula el score ponderado (`score × 0.7 + utilidad × 0.3`) y marca el cultivo **«Más rentable»** con badge.

**Beneficio:** un cultivo apto pero sin mercado en la región deja de ser la primera opción; se siembra lo que es apto **y** rentable.

### 3.3 Variedades y rotación

- **🌾 Variedades por altitud:** el catálogo filtra variedades compatibles con la altitud de la finca (p. ej. variedades de café Cenicafé).
- **🔄 Rotación sugerida:** según el último ciclo cosechado, el sistema recomienda el cultivo compatible para rotar (ej. maíz → fríjol/arveja).

**Beneficio:** protege el suelo del agotamiento y reduce presión de plagas entre ciclos.

### 3.4 Cuándo sembrar (Almanaque Bristol)

El calendario lunar (Almanaque Bristol) cruza las fases de la luna con el cultivo elegido y emite recomendaciones de siembra cultural (`siembra_lunar`), configurables por usuario.

**Beneficio:** respeta la tradición campesina y da una fecha de siembra sugerida además del dato técnico.

### 3.5 Simular antes de invertir («¿y si aplico cal?»)

El **modo simulación** permite modificar valores del suelo (pH, N, P, K) y reejecutar el motor **sin guardar nada**: responde «si aplico cal y subo el pH a 6.5, ¿el aguacate pasa a apto?».

**Beneficio:** el productor prueba enmiendas virtuales antes de gastar un peso.

### 3.6 Si faltan datos: muestreo inteligente

Si el análisis es preliminar, el reporte incluye **«📌 Muestreo inteligente»**: elige los 3 puntos del lote de **máxima incertidumbre** (los más lejanos entre sí) para tomar la muestra compuesta de laboratorio, con mapa descargable (GeoJSON) y la proyección de cuánto subiría la confianza.

**Beneficio:** una sola visita al laboratorio en los puntos correctos convierte un análisis «preliminar» en uno «validado».

---

## 4. Escenario B — Con el cultivo sembrado: «¿Dónde abono, dónde riego, qué hago?»

Cuando la finca ya tiene cultivo, el análisis cambia de pregunta: ya no es *qué sembrar*, sino **cómo cuidar lo sembrado**. El análisis UC2 responde con diagnóstico, planes y mapas.

### 4.1 Diagnóstico del suelo por variable (UC2)

Cada variable medida se compara con el **rango ideal del cultivo sembrado** y se clasifica:

| Estado | Significado | Ejemplo |
|---|---|---|
| **DÉFICIT** | Está por debajo del rango óptimo | «Potasio bajo: aplicar KCl…» |
| **EXCESO** | Está por encima del rango óptimo | «Exceso de N en fructificación: reduzca dosis…» |
| **SIN DATO** | No se midió; se indica qué parámetro falta | «pH sin dato: suministre la lectura para diagnóstico certero» |

Cada fila trae **lectura actual, rango ideal, acción correctiva, prioridad (Crítica/Alta/Media/Baja), fuente (UPRA/Cenicafé/AGROSAVIA) y confiabilidad**. Las acciones sobre N/P/K de sensor sin validar se marcan *«condicional a confirmación de laboratorio»*.

**Beneficio:** el agricultor sabe exactamente **qué le falta, qué le sobra y qué es urgente**.

### 4.2 Dónde abonar: mapa de calor y plano del lote

- **Mapa de calor (sección M):** cada toma del sensor viene georreferenciada (`pos_x/pos_y` en metros). El reporte pinta un mapa de calor **por variable** con rampa de intensidad: se ve en qué zonas del lote el pH es más ácido, dónde el potasio está bajo, dónde la humedad es crítica.
- **Plano del lote (sección N):** SVG con los puntos de toma, cierre convexo del polígono, área/perímetro, pendiente y drenaje.

**Beneficio:** la fertilización deja de ser uniforme (y cara); se abona **solo donde hace falta y en la dosis correcta** — agricultura de precisión por zonas.

### 4.3 Qué abonar: plan de fertilización ejecutable

Cada déficit viene con su **plan sugerido**: fuente del producto (urea, DAP, KCl, cal dolomítica…), frecuencia y dosis. La dosis se define tras validación de laboratorio (nunca se inventa).

**Beneficio:** el productor no pregunta «¿qué echo?»: tiene producto, momento y cantidad.

### 4.4 Interacciones entre nutrientes (antagonismos)

El motor evalúa reglas de segundo orden y emite hallazgos «**AJUSTE NUTRICIONAL**»:

- Exceso de K bloquea la absorción de Ca/Mg → priorizar calcio/magnesio.
- Exceso de P fija zinc → considerar aplicación foliar de Zn.
- Exceso de N en fructificación → retrasa la maduración; reducir dosis.
- pH ácido (<5.5) + Mg bajo → usar **cal dolomítica** en vez de cal agrícola.

**Beneficio:** evita el error clásico de «corregir un nutriente empeorando otro» y ahorra insumos.

### 4.5 Dónde y cuándo regar

El módulo de agua combina tres piezas:

- **Humedad del suelo por punto:** el mapa de calor de humedad muestra qué zonas del lote están secas y necesitan riego localizado.
- **Balance hídrico ETo/Kc (FAO-56):** calcula la evapotranspiración del cultivo menos la lluvia pronosticada (Open-Meteo y modelo internacional ECMWF) y responde **«💧 Necesidad de riego»** en los próximos 7 días.
- **Calidad del agua de riego (FAO-29):** clasifica CE, RAS, cloruros y boro en ninguna | leve-moderada | severa, con recomendación (agua salina puede arruinar el suelo aun fertilizando bien).

**Beneficio:** se riega lo justo, donde toca y solo si la lluvia no va a cubrirlo — ahorro de agua y energía, sin estrés hídrico para la planta.

### 4.6 Manejo por etapa del cultivo (fenología + GDD)

Si la finca registra el ciclo sembrado (fecha de siembra, etapa fenológica), el diagnóstico se ajusta a la etapa:

- **Vegetativa** → priorizar nitrógeno.
- **Floración** → priorizar fósforo y boro.
- **Fructificación** → priorizar potasio y calcio.
- **Cosecha** → respetar carencias sin forzar maduración.

Además, con los **Grados-Día (GDD)** acumulados según la climatología IDEAM, el sistema estima **cuánto falta para cosecha** («⏳ Faltan ~N GDD, optimice riego»).

**Beneficio:** cada peso de fertilizante cae en la etapa donde la planta lo aprovecha; y se conoce la ventana de cosecha.

### 4.7 Alertas climáticas que protegen las labores

Cada 6 horas se evalúa el pronóstico de 7 días:

- **🌧 Lluvia > 20 mm/24h + fertilización programada** → «Aplace la aplicación: riesgo de lixiviación» (el abono se lavaría del suelo y se perdería el dinero).
- **🥶 Mínima < 5 °C + cultivo sensible en floración** → «Riesgo de helada: active riego por aspersión».

**Beneficio:** el insumo no se pierde por la lluvia y la floración no se quema por la helada.

### 4.8 Presupuesto y rentabilidad: plan económico

El productor puede declarar su **presupuesto de fertilización ($/ha)**. El sistema:

1. Calcula el **costo del plan ideal** (todas las correcciones).
2. Prioriza por severidad (críticas primero) e incluye acciones **hasta agotar el presupuesto**.
3. Muestra qué quedó **incluido**, qué quedó **aplazado** y la **diferencia de rendimiento** esperada.
4. Proyecta **ROI**: (ganancia − costo del plan) ÷ costo, con alerta «⚠️ Inversión justa, considere subvenciones» si el retorno es bajo.

Los precios de insumos se actualizan en el panel de administración (urea, DAP, KCl, cal…), así el ROI no queda desactualizado.

**Beneficio:** con poco presupuesto se financian primero las correcciones que más rinden.

### 4.9 Predicción de rendimiento

- **Con historial de ciclos:** promedio de rendimiento real × 1.15 (plan optimizado al presupuesto) o × 1.25 (plan ideal).
- **Sin historial:** se usa el rendimiento esperado de la ficha técnica del cultivo.
- Al cosechar, el rendimiento declarado se valida contra el esperado: valores atípicos (2× o 0.3×) se marcan para no contaminar el modelo, sin bloquear el guardado.

**Beneficio:** el agricultor proyecta cuántas toneladas esperar y cuánto valen.

### 4.10 Del diagnóstico a la acción: órdenes de trabajo y BPA

- **📋 Generar órdenes de trabajo:** cada acción del diagnóstico se convierte en una labor (fertilización, enmienda, riego, control fitosanitario) con producto, dosis, fecha programada, responsable y estado. El dashboard muestra **«Tareas pendientes de hoy»** y se completan en campo (incluso offline con la PWA).
- **📋 Trazabilidad BPA:** checklist ICA 30021/2017, períodos de carencia y reporte de trazabilidad por medición — listo para certificación de Buenas Prácticas Agrícolas.
- **🔄 Ciclo productivo:** se registra siembra → aplicaciones → cosecha → rendimiento; ese historial alimenta la rotación, la predicción de rendimiento y el aprendizaje del modelo.

**Beneficio:** la recomendación no se queda en papel; se convierte en trabajo asignado, ejecutado y verificado.

---

## 5. Información y predicciones que entrega el aplicativo (resumen)

| Capacidad | Qué responde | Entrada principal |
|---|---|---|
| Aptitud del suelo | ¿Este cultivo sirve aquí? (score + clasificación UPRA) | Variables de suelo + reglas del cultivo |
| Ranking de siembra | Top 5 cultivos con score, confianza y ajustes | Todo el suelo + catálogo |
| Deficiencias y excesos | Qué nutriente falta/sobra, cuánto y con qué prioridad | Sensores / laboratorio |
| Plan de fertilización | Producto, dosis, frecuencia y costo | Déficits + precios de insumos |
| Dónde abonar/regar | Mapa de calor y plano por variable del lote | Toma georreferenciada (`pos_x/pos_y`) |
| Necesidad de riego | Cuánto regar en los próximos 7 días (ETo/Kc − lluvia) | Pronóstico + Kc del cultivo |
| Calidad de agua | Si el agua de riego es apta (CE/RAS/cloruros/boro) | Análisis de agua FAO-29 |
| Fenología y GDD | Qué priorizar por etapa y cuánto falta para cosecha | Ciclo sembrado + climatología IDEAM |
| Rendimiento esperado | t/ha proyectadas (×1.15 plan optimizado / ×1.25 ideal) | Historial de ciclos o ficha técnica |
| Rentabilidad | Ingreso bruto, utilidad y ROI por hectárea | Precios de cosecha + plan económico |
| Alertas climáticas | Aplazar abono por lluvia / riesgo de helada | Pronóstico 7 días + fenología + labores |
| Plagas y enfermedades | Diagnóstico desde foto (motor AgroVision + fallback) | Imagen del cultivo |
| Confianza del análisis | Semáforo de 4 barras y cómo subir al 80 % | Calibración, cobertura, violaciones, respaldos |

### Confianza transparente

El análisis siempre muestra **por qué** cree lo que cree (semáforo de 4 barras): calibración del sensor, cobertura de fertilidad, violaciones activas y respaldo humano de agrónomos. Con confianza < 80 % el resultado se muestra **«Pendiente de validación técnica»** — nunca «Apta» a secas — e indica los 2 pasos más rentables para subir la confianza.

---

## 6. Beneficios concretos para el agricultor

| Antes | Con AgroIA |
|---|---|
| Fertiliza «por costumbre» o por intuición | Fertiliza según déficits medidos, con producto, dosis y prioridad |
| Abona parejo todo el lote | Abona **por zonas**, solo donde el mapa de calor lo indica |
| Riega por calendario | Riega según balance hídrico ETo/Kc y humedad por punto |
| Pierde abono con la lluvia | Recibe alerta para **aplazar** la aplicación |
| Siembra sin saber si el cultivo sirve | Siembra el cultivo apto **y rentable** de la región |
| Corrige un nutriente y bloquea otro | El motor avisa de antagonismos (K-Ca-Mg, P-Zn…) |
| No sabe cuánto va a cosechar | Proyecta rendimiento y ROI antes de invertir |
| Sin datos históricos para certificar | Trazabilidad BPA y ciclos productivos auditados |

---

## 7. Fuentes del conocimiento agronómico

- **Reglas agronómicas:** UPRA, Cenicafé, AGROSAVIA (54 reglas activas, 17 variables).
- **Clasificación de aptitud:** metodología UPRA (Apta → No apta).
- **Agua:** FAO-29 (calidad) y FAO-56 (ETo/Kc).
- **Clima:** Open-Meteo, modelo internacional ECMWF (IFS 0.25°, datos abiertos) y climatología IDEAM.
- **Suelos:** Estudio General de Suelos IGAC (1:100.000) y zonificaciones UPRA/SIPRA.
- **BPA:** checklist ICA resolución 30021/2017.
- **IA:** RandomForest de diagnóstico (17 variables) y de aptitud, en modo sombra con promoción por variable cuando la precisión real supera 0.85 (aprendizaje activo con aceptaciones de agrónomos y ciclos cosechados reales).

---

*Documento informativo — el detalle técnico y de endpoints vive en `resources/architecture/Documento_Funcional_Tecnico_AgroIA.md` (v3.5).*
