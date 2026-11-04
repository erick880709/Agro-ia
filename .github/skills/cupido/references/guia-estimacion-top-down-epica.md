# Guía de Estimación Top-Down por Épica (Modo Épica / ROM)

*Guía de referencia · Preventa*

Esta guía aplica cuando **no existe todavía** un desglose de Historias de Usuario/Tareas Técnicas (`specter` no ha corrido, o el cliente necesita una cifra antes de invertir en ese desglose). Es una estimación **ROM (Rough Order of Magnitude)** hecha directamente sobre la épica que entrega `epicureo`, no sobre historias individuales. Es intencionalmente más gruesa que el Modo Backlog — su valor es rapidez y consistencia para preventa, no precisión de sprint.

Si el usuario ya tiene el backlog de `specter`, usa el Modo Backlog (cuerpo principal del `SKILL.md`) en su lugar — es más preciso porque parte de unidades más pequeñas. Si una épica en Modo Épica resulta de tamaño **XL** (ver sección 2), recomienda descomponerla con `specter` antes de comprometer la cifra con el cliente.

## Contenido
1. Cuándo usar esta guía
2. T-shirt sizing de la épica (Desarrollador)
3. Arquitecto — horas según alcance
4. QA — fórmula estándar y criterio alterno (foco no funcional)
5. UX/UI — horas según alcance
6. Project Manager — fórmula
7. Metodología de trabajo y duración de iteración
8. Ejemplo resuelto
9. Ítems usuales de preventa a incluir en la propuesta

---

## 1. Cuándo usar esta guía

- El insumo es una o más épicas de `epicureo` (`resources/functional/reqs/epic-*.md`), sin desglose de HU/TT todavía.
- El cliente pide un número rápido para decidir si vale la pena invertir en el desglose detallado (caso típico de preventa).
- Reestimaciones a nivel de épica completa (no por historia individual).

No reemplaza el Modo Backlog cuando ya existe el desglose — en ese caso, el desglose siempre da una cifra más confiable.

---

## 2. T-shirt sizing de la épica (Desarrollador)

Asigna un tamaño a **cada épica** de la propuesta (una propuesta puede traer varias). No promedies varias épicas en una sola talla — cada una lleva la suya.

| Talla | Indicadores | Horas de desarrollo (Frontend + Backend combinados) |
|-------|-------------|-------------------------------------------------------|
| **XS** | 1 flujo simple, CRUD básico, sin integraciones | 20–40 h |
| **S**  | Flujo moderado, pocas reglas de negocio, 0–1 integración simple | 40–80 h |
| **M**  | Varios flujos, reglas moderadas, 1–2 integraciones | 80–160 h |
| **L**  | Múltiples flujos, integraciones críticas, reglas de negocio complejas, varios roles/permisos | 160–320 h |
| **XL** | La "épica" en realidad cubre un dominio completo o varias capacidades independientes | 320 h+ |

**Regla práctica:** si al describir la épica necesitas más de 3-4 frases para resumir "qué hace", probablemente no es XS/S. Si aparecen dos o más sistemas de negocio distintos en el mismo alcance, es candidata a XL — y a descomponerse.

**Si el usuario indica proporción esperada Frontend/Backend** (ej. "es mayormente backend, casi sin UI"), reparte las horas de desarrollo con esa proporción declarada; si no la indica, usa 40% Frontend / 60% Backend como default documentado en Supuestos.

**Si la épica es XL:** no fuerces una sola cifra de bulto. Documenta el rango de la tabla como piso, marca la épica como `Requiere descomposición (specter) antes de comprometer cifra`, y ofrece continuar solo como ROM preliminar con un buffer de riesgo alto (35–40%, ver tabla de buffers del `SKILL.md`).

---

## 3. Arquitecto — horas según alcance

El esfuerzo de Arquitecto **no** es un porcentaje fijo del desarrollo — depende de decisiones de diseño, no de líneas de código. Evalúa la épica contra estos indicadores:

| Complejidad arquitectónica | Indicadores | Horas de Arquitecto |
|---|---|---|
| **Baja** | Extiende un sistema/módulo existente, sin integraciones nuevas, patrón ya establecido en el proyecto | 4–8 h |
| **Media** | 1–2 integraciones nuevas, o un componente nuevo dentro de una arquitectura ya conocida | 8–20 h |
| **Alta** | Nuevo servicio/dominio, múltiples integraciones, decisiones de arquitectura significativas (ADRs nuevos) | 20–40 h |
| **Muy alta** | Nueva plataforma o dominio crítico, múltiples sistemas involucrados, alta incertidumbre técnica | 40 h+ (recomienda spike/PoC previo, no comprometas la cifra sin él) |

Si existe un documento de arquitectura previo (`resources/architecture/`, salida de `archi`) para el mismo proyecto, revísalo antes de asignar el nivel — reutilizar una decisión ya tomada baja la complejidad real frente a decidirla desde cero.

---

## 4. QA — fórmula estándar y criterio alterno (foco no funcional)

### 4.1 Fórmula estándar ("formulado")
Por defecto, el esfuerzo de QA se calcula como **25% de las horas de desarrollo** de la épica (rango aceptable 20–30% según criticidad del dominio — sube al 30% si la épica toca flujos transaccionales o regulados).

```
Horas QA = Horas Desarrollo × 0.25
```

### 4.2 Criterio alterno — épica enfocada en requerimientos no funcionales
Si la épica está **predominantemente enfocada en atributos no funcionales** (performance, seguridad, accesibilidad, resiliencia — no en features nuevas), la fórmula del 25% subestima el esfuerzo real: en vez de aplicarla, estima por tipo de prueba:

| Tipo de prueba no funcional | Horas base |
|---|---:|
| Rendimiento / carga (performance, load testing) | 16–40 h |
| Seguridad (revisión SAST/DAST, pentesting básico) | 16–32 h |
| Accesibilidad (WCAG) | 8–16 h |
| Resiliencia / recuperación (chaos testing, failover) | 16–24 h |

Suma solo los tipos de prueba que la épica realmente requiere (no apliques las cuatro por defecto). Si la épica combina features funcionales *y* un componente no funcional fuerte, **combina ambos criterios**: 25% sobre las horas de desarrollo funcional, más las horas específicas de NFR — y declara esa combinación explícitamente en Supuestos, no la presentes como un solo número sin desglosar.

---

## 5. UX/UI — horas según alcance

Solo aplica si la épica tiene componente de interfaz. Si es puramente backend/API/batch sin pantallas nuevas ni ajustadas, **omite el rol** (0 horas, y dilo explícitamente en vez de dejar la fila vacía sin explicación).

| Alcance UX/UI | Indicadores | Horas |
|---|---|---|
| Ninguno | Sin interfaz nueva ni modificada | 0 h |
| Bajo | Ajustes menores a pantallas existentes, reutiliza el design system tal cual | 8–16 h |
| Medio | 1–3 pantallas/flujos nuevos, dentro del design system ya definido | 16–40 h |
| Alto | Flujo end-to-end nuevo, múltiples pantallas, posible research/validación con usuarios | 40–80 h+ |

---

## 6. Project Manager — fórmula ("formulado")

El esfuerzo de PM se calcula como **porcentaje del esfuerzo total del equipo** (suma de Arquitecto + Desarrollador + QA + UX/UI), no por épica aislada sino sobre el total de la propuesta — la coordinación no escala linealmente por épica individual.

| Duración total estimada del proyecto | % PM sobre el esfuerzo del equipo |
|---|---:|
| ≤ 1 mes | 10% |
| 1–3 meses | 12% |
| 3–6 meses | 15% |
| > 6 meses | 18% (recomienda evaluar un PM dedicado full-time en vez de este cálculo proporcional) |

```
Horas PM = (Horas Arquitecto + Horas Desarrollo + Horas QA + Horas UX/UI) × % según duración
```

Calcula primero la duración aproximada (usando la velocidad/capacidad del equipo, sección 7) para saber qué porcentaje aplica, y decláralo como supuesto si la duración final difiere de la usada para fijar el %.

---

## 7. Metodología de trabajo y duración de iteración

Esto se pregunta **una sola vez, al inicio de la sesión de estimación** (Paso 0 del `SKILL.md`) y determina cómo se presenta la proyección temporal:

| Metodología | Cómo se proyecta el tiempo |
|---|---|
| **Scrum** | Sprints de duración fija (típicamente 1–4 semanas, pregunta la duración exacta). Iteraciones = horas totales del equipo ÷ capacidad por sprint. |
| **XP (Extreme Programming)** | Iteraciones cortas, típicamente 1–2 semanas — mismo cálculo que Scrum, pero usa el término "iteración" en vez de "sprint" en la salida. |
| **SAFe** | Sprints de 2 semanas dentro de un Program Increment (PI) de 8–12 semanas — pregunta duración del PI y del sprint; presenta ambos niveles en la proyección. |
| **Kanban** | Sin iteración fija — no fuerces un número de "sprints". Pide la capacidad diaria/semanal del equipo (horas-persona por día) y presenta la proyección como **lead time estimado** y throughput (unidades de trabajo/semana), con hitos en vez de sprints. |
| **Cascada / Waterfall** | Sin iteraciones — presenta la proyección como fases secuenciales (Análisis, Diseño, Construcción, Pruebas, Despliegue) con horas/días por fase, no como sprints. |
| **Híbrido / otro** | Pregunta al usuario cómo mide sus ciclos de entrega y adapta la terminología de la salida a lo que responda — no asumas Scrum por defecto solo porque es el más común. |

Si el usuario no sabe o no tiene definida la metodología, pregunta explícitamente antes de generar la proyección — no asumas Scrum de 2 semanas por defecto como hacía la versión anterior de esta skill. Documenta la respuesta en "Parámetros de Estimación" del documento de salida.

---

## 8. Ejemplo resuelto

Épica: "Permitir a un cliente consultar y descargar su historial de transacciones de los últimos 12 meses, con filtros por fecha y tipo, integrando con el sistema core existente."

- **Talla (Desarrollador):** M (varios flujos — consulta, filtro, descarga —, 1 integración con el core). Horas de desarrollo: 120 h (60% Backend = 72h, 40% Frontend = 48h, split default).
- **Arquitecto:** Media (1 integración nueva con el core, dentro de arquitectura conocida) → 14 h.
- **QA:** enfoque funcional estándar → 120 h × 0.25 = 30 h.
- **UX/UI:** Medio (2 pantallas: listado con filtros + detalle de descarga) → 24 h.
- **PM:** duración estimada ~3 semanas → categoría "≤ 1 mes" → 10% sobre (14 + 120 + 30 + 24 = 188 h) = 18.8 h.
- **Total épica:** 188 + 18.8 ≈ **206.8 horas**.

---

## 9. Ítems usuales de preventa a incluir en la propuesta

Además de las tablas de esfuerzo, toda propuesta generada por esta skill (PPTX y HTML) debe incluir los elementos que un cliente espera ver en una propuesta comercial de preventa, no solo la estimación técnica:

- **Contexto/necesidad de negocio** (resumen en lenguaje de negocio, no técnico) — se toma de la épica refinada de `epicureo`.
- **Épica(s) incluidas** — el enunciado refinado de cada épica tal como lo dejó `epicureo` (sección obligatoria, ver `SKILL.md`).
- **Alcance** (qué incluye la propuesta) y **exclusiones explícitas** (qué NO incluye).
- **Equipo propuesto** — roles y dedicación (no solo horas totales, también composición sugerida del squad).
- **Cronograma** en los términos de la metodología acordada (sección 7).
- **Inversión estimada** (si hay tarifas) o solo esfuerzo (si no las hay) — ver "Estructura de costos" del `SKILL.md`.
- **Riesgos y supuestos.**
- **Vigencia de la propuesta** (ej. "Esta estimación es válida por 30 días desde su fecha de emisión" — usa 30 días si el usuario no indica otra vigencia, y decláralo como supuesto).
- **Próximos pasos** (ej. "Aprobación → kickoff → desglose detallado con specter si no se ha hecho aún").

No es necesario un apartado legal/comercial completo (eso lo cubre `proposal-doc-generator` en el flujo de preventa) — esta skill entrega la vista de esfuerzo con el mínimo de contexto de negocio para que la propuesta se sostenga sola si se comparte de forma independiente.
