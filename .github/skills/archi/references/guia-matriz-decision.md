# Guía: Matriz de Decisión Ponderada

Complementa `09-Alternativas-de-Solucion.md` y `20-Decisiones-Arquitectonicas.md`. Estructura comparaciones con una fórmula explícita y trazable sin reemplazar el juicio ni la selección humana registrada en `10`.

## Cuándo usarla

Actívala cuando se cumplan **ambas** condiciones:

1. Hay **2 o más alternativas real y actualmente viables** para una decisión de peso arquitectónico (no una decisión trivial con una sola opción sensata).
2. El trade-off **no es obvio a simple vista** — ninguna alternativa domina claramente en todos los criterios relevantes, o el proyecto tiene restricciones/prioridades que podrían invertir la elección "de manual".

Ejemplos típicos: estilo arquitectónico (monolito vs. microservicios vs. serverless), composición frontend (SPA modular vs. Microfrontends según `references/guia-microfrontends.md`), proveedor de nube, motor de base de datos (usa `references/guia-catalogo-bases-de-datos.md` para las dimensiones y el catálogo por tipo), framework backend/frontend, patrón de mensajería (colas vs. bus de eventos), librería de resiliencia, plataforma de bajo código.

**No la uses** cuando la alternativa ganadora sea evidente y de bajo impacto; ahí basta una entrada corta en `20-Decisiones-Arquitectonicas.md`.

## Categorías de evaluación

Las mismas 5 categorías aplican como punto de partida, pero **no fuerces las 5 en cada grupo** — para una decisión puntual de tecnología (ej. motor de BD) reduce a las 3-4 categorías realmente relevantes y omite el resto:

| Categoría | De dónde sale | Cuándo se omite |
|---|---|---|
| **Atributos de Calidad** | Reutiliza los `QA-xx` de `05-Atributos-de-Calidad.md` | Casi nunca |
| **Well-Architected** | Pilares aplicables de `08-Well-Architected.md` | Cuando no diferencia las alternativas |
| **Costos / Esfuerzo** | Cifras de `17.4-Pricing_<Proyecto>.md`; si no existe, esfuerzo relativo documentado en `04-Supuestos.md` | Nunca |
| **Riesgos / Restricciones** | Restricciones de `03-Restricciones.md` y riesgos específicos | Cuando no diferencia alternativas |
| **Lineamientos del proyecto** | Preferencias de stack, estándares o gobierno ya confirmados en la línea base (Paso 0.5) — vendor lock-in aceptado, stack ya adoptado por el equipo, licencias existentes | Cuando la línea base no documentó ningún lineamiento aplicable a este grupo |

## Fórmula y escalas

```
Puntaje por criterio = Prioridad (0-5) × Calificación (0-5)
Puntaje total de la alternativa = Σ (Puntaje por criterio) del grupo
```

**Prioridad** (importancia del criterio para el proyecto/cliente):

| Valor | Significado |
|---|---|
| 5 | Crítico — no negociable |
| 4 | Muy importante |
| 3 | Importante |
| 2 | Deseable |
| 1 | Agradable de tener |
| 0 | No aplica a este proyecto |

**Calificación** (qué tan bien satisface la alternativa ese criterio):

| Valor | Significado |
|---|---|
| 5 | Satisface completamente |
| 4 | Satisface bien, con observaciones menores |
| 3 | Satisface parcialmente |
| 2 | Satisface en medida limitada |
| 1 | Apenas satisface, con riesgo alto |
| 0 | No satisface el criterio |

## Modo de normalización objetiva (criterios medibles)

Usa este modo en vez de una calificación subjetiva 0-5 cuando el criterio tiene un **valor real medido** para cada alternativa (costo en $, latencia en ms, throughput, tamaño de equipo requerido, etc.) — es más defendible que "a ojo" porque dos personas midiendo lo mismo llegan al mismo puntaje.

```
Si el criterio es "menor es mejor" (ej. costo, latencia):
  Calificación = mín(valores de todas las alternativas) × 5 ÷ valor de esta alternativa

Si el criterio es "mayor es mejor" (ej. throughput, cobertura de pruebas):
  Calificación = máx(valores de todas las alternativas) × 5 ÷ valor de esta alternativa
```

La alternativa con el mejor valor real siempre obtiene Calificación = 5; el resto queda proporcional a qué tan lejos está del mejor valor. El resultado se multiplica por la Prioridad (0-5) igual que en el modo subjetivo, para mantener consistencia en la tabla.

No mezcles ambos modos en la misma fila — sí puedes mezclarlos en la misma tabla (unas filas con valor medido y normalización, otras con calificación subjetiva de juicio experto), siempre que la columna Observación deje explícito cuál modo se usó y el valor real detrás de la normalización.

## Caso de uso: comprar, reutilizar o construir un componente

Actívalo cuando la decisión sea sobre un **componente puntual** (librería, servicio de terceros, módulo interno ya existente) y no sobre el estilo arquitectónico completo — para eso usa las categorías generales de arriba. El resultado normalmente no necesita archivo propio: documenta el ganador y el puntaje como una entrada corta en `20-Decisiones-Arquitectonicas.md`, citando esta matriz.

Dos grupos de criterios, evaluados por separado (uno no reemplaza al otro — un componente puede reutilizarse bien mid pero salir caro de mantener):

| Categoría | Criterio | Peso sugerido de partida* |
|---|---|---|
| Reutilización | ¿Posee la funcionalidad necesaria? Si no, ¿se puede modificar? | 0.6 |
| Reutilización | ¿Ha tenido desempeño óptimo en ambientes productivos? | 0.3 |
| Reutilización | ¿Se adapta al proyecto (interfaces, escalabilidad, ambientes de despliegue, RNF del cliente)? | 0.1 |
| Adquisición | ¿El proyecto puede asumir el costo, incluyendo licencias y adaptaciones? | 0.3 |
| Adquisición | ¿Agiliza o al menos no afecta los tiempos de desarrollo? | 0.2 |
| Adquisición | ¿El nivel de soporte genera confianza? | 0.2 |
| Adquisición | ¿Podría reutilizarse en el futuro? | 0.05 |
| Adquisición | ¿Su rendimiento no afecta ningún atributo de calidad prioritario (`QA-xx`)? | 0.1 |
| Adquisición | ¿Implica una curva de aprendizaje relevante para el equipo? | 0.15 |

\* Pesos heredados de la plantilla histórica `GRCpl103_MatrizCompraReutilizacion` — úsalos como punto de partida razonable, pero confírmalos con el usuario si el proyecto tiene prioridades distintas (la regla general de no inventar un peso sigue aplicando).

Califica cada criterio (0-5, o normalizado si hay un valor medido — ej. costo real de licencia) para cada alternativa evaluada (reutilizar el componente interno X, comprar el de terceros Y, construir uno nuevo), y decide con el mismo proceso de la sección siguiente.

## Caso de uso: interfaces conversacionales y agentic UI

No compares assistant-ui, Vercel AI SDK UI, AG-UI, A2UI, OpenAI ChatKit y CopilotKit en una
sola matriz como si fueran alternativas equivalentes. Primero clasifica las capas y después
construye configuraciones que cubran el mismo alcance:

| Grupo | Responsabilidad | Alternativas típicas a verificar |
|---|---|---|
| UI kit/componentes | Composer, mensajes, tools, threads, feedback, HITL y theming | assistant-ui / CopilotKit / OpenAI ChatKit / componentes propios |
| Runtime/estado | Stream, message parts, persistencia, retry/cancel y errores | Vercel AI SDK UI / runtime de assistant-ui o CopilotKit / runtime propio |
| Protocolo agente↔UI | Eventos, estado, interrupts, correlación y reanudación | AG-UI / contrato SSE-WebSocket propio |
| UI generativa | Schema declarativo, catálogo permitido, acciones, validación y renderer | A2UI / spec propia / componentes fijos |

Una tecnología puede cubrir más de un grupo y una configuración puede incluir varias. Declara
solapamientos y el owner de cada responsabilidad para evitar puntuar dos veces la misma capacidad.
Si una opción integrada cubre kit + runtime + protocolo, compárala contra otra configuración con
cobertura equivalente, no contra un protocolo aislado.

Deriva los criterios de `QA-xx`, restricciones, requisitos Iris y PoC. Como mínimo considera los
aplicables:

- fidelidad a `SURF/SCR/CMP/ST/ERR/TC`, Design System y accesibilidad;
- cobertura de streaming, tool calls/HITL, cancelación, threads y reanudación;
- compatibilidad con frontend, backend/agente, identidad y hosting vigentes;
- contrato/versionado, observabilidad, testing y manejo de errores;
- seguridad de contenido, componentes/acciones generados y trust boundaries;
- esfuerzo de adapter/migración, bundle/runtime, skills del equipo y time-to-market;
- portabilidad de modelo/backend, lock-in, soporte, licencia, roadmap y salida de contingencia.

Registra fuente oficial, versión/estado y fecha de consulta por candidato. Si la madurez o el
comportamiento productivo no están demostrados, la evaluación vive en `11`; los desconocidos en
`12`; la comparación ejecutada en `13`; el baseline resultante en `10.1`; y el razonamiento final
en `20`. `09` solo participa si la decisión cambia configuración macro, límites desplegables o
topología, por ejemplo embed administrado frente a frontend propio o protocolo estándar frente a
contrato propietario con impacto material.

## Proceso

1. **Identifica los grupos de decisión reales.** Para configuración de descomposición/nube, usa las mismas alternativas y el mismo mapa de alcance de `09-Alternativas-de-Solucion.md`; no califiques Hexagonal o CQRS como si fueran alternativas macro. Para composición frontend usa las alternativas y criterios de `references/guia-microfrontends.md`, sin mezclar la selección del patrón con la herramienta concreta de composición.
2. **Define los criterios dinámicos del grupo** (ver tabla de categorías arriba) — normalmente 6-12 filas totales, no una tabla exhaustiva de 20 criterios que nadie va a leer.
3. **Asigna la prioridad de cada criterio** según los `QA-xx` y restricciones ya documentados — si el peso de un criterio no está claro, pregúntale al usuario en vez de asumir un número (una prioridad inventada invalida todo el puntaje que depende de ella).
4. **Califica cada alternativa por criterio**, con una observación breve que justifique el número (nunca un puntaje sin justificación — es lo que hace la matriz auditable en vez de arbitraria).
5. **Calcula subtotales por categoría y el puntaje total** de cada alternativa.
6. **Documenta la decisión**: alternativa ganadora, puntaje, justificación (en qué categorías fue más fuerte), y las condiciones/supuestos bajo los cuales se tomó (ej. "esta decisión asume que el equipo no crecerá más de 8 desarrolladores en el próximo año").

## Dónde vive el resultado (regla anti-duplicación)

Sigue la misma regla ya establecida en `plantilla-documento-arquitectura.md` para evitar duplicar contenido entre archivos:

- Si la decisión de configuración/nube ya vive en `09`, agrega la matriz allí; `20` solo enlaza a `09` y a la selección de `10`.
- Si la decisión no tiene archivo propio, la matriz vive en la entrada correspondiente de `20-Decisiones-Arquitectonicas.md`.

## Plantilla de la tabla

```markdown
#### Grupo: [Nombre del grupo] — [Alternativa A] vs. [Alternativa B] (vs. [Alternativa N])

> **Tipo de decisión:** [Motor de BD / Framework / Patrón / Librería / Estilo arquitectónico / etc.]
> **Contexto:** [Por qué se evalúan estas opciones y qué problema resuelven]

| Categoría | Criterio | Prioridad<br>(0-5) | [Alt. A] | [Alt. B] | [Alt. N] | Puntaje [Alt. A]<br>P×C | Puntaje [Alt. B]<br>P×C | Puntaje [Alt. N]<br>P×C | Observación |
|---|---|---:|---:|---:|---:|---:|---:|---:|---|
| Atributos de Calidad | [Criterio — cita `QA-xx`] | [P] | [C] | [C] | [C] | [P×C] | [P×C] | [P×C] | [Obs.] |
| | **Subtotal Atributos de Calidad** | | | | | **[Σ]** | **[Σ]** | **[Σ]** | |
| Well-Architected | [Pilar relevante] | [P] | [C] | [C] | [C] | [P×C] | [P×C] | [P×C] | [Obs.] |
| | **Subtotal Well-Architected** | | | | | **[Σ]** | **[Σ]** | **[Σ]** | |
| Costos / Esfuerzo | [Criterio — cita `17.4-Pricing_<Proyecto>.md` si existe] | [P] | [C] | [C] | [C] | [P×C] | [P×C] | [P×C] | [Obs.] |
| | **Subtotal Costos / Esfuerzo** | | | | | **[Σ]** | **[Σ]** | **[Σ]** | |
| Riesgos / Restricciones | [Cita `RT-Dxx`/`RN-Dxx`/`RR-Dxx` si aplica] | [P] | [C] | [C] | [C] | [P×C] | [P×C] | [P×C] | [Obs.] |
| | **Subtotal Riesgos / Restricciones** | | | | | **[Σ]** | **[Σ]** | **[Σ]** | |
| Lineamientos del proyecto | [Preferencia ya confirmada en línea base] | [P] | [C] | [C] | [C] | [P×C] | [P×C] | [P×C] | [Obs.] |
| | **Subtotal Lineamientos** | | | | | **[Σ]** | **[Σ]** | **[Σ]** | |
| | **PUNTAJE TOTAL** | | | | | **[Σ total]** | **[Σ total]** | **[Σ total]** | |
| | **Posición** | | | | | **[#]** | **[#]** | **[#]** | |

**Alternativa elegida:** [Nombre] — **Puntaje:** [Total] / [Máximo posible]

**Justificación:** [Por qué obtuvo el mayor puntaje; en qué categorías fue más fuerte.]

**Condiciones de la decisión:**
- [Supuesto bajo el cual se tomó la decisión]
- [Riesgo aceptado conscientemente]
```

## Manejo de información faltante

| Situación | Acción |
|---|---|
| No hay prioridades de negocio documentadas para un criterio | Pregunta al usuario antes de construir la fila — no inventes un peso |
| No existe `17.4-Pricing_<Proyecto>.md` para Costos | Usa esfuerzo relativo y documenta el supuesto en `04-Supuestos.md` |
| Todas las alternativas quedan prácticamente empatadas | Documenta el empate brevemente y decide con un criterio de desempate explícito (ej. preferencia del equipo, madurez de la comunidad) en vez de forzar una diferencia artificial |
| El usuario pide "solo dime cuál usar" sin querer ver la matriz | Genera igual la matriz completa (queda como respaldo auditable) pero lidera la respuesta con la recomendación y 2-3 razones, enlazando al detalle |
