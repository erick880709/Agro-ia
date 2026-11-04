# Guía: Pilares Well-Architected

Complementa `08-Well-Architected.md`. A diferencia del QAW (`07`), que prioriza según lo que los stakeholders traen a la mesa, el Well-Architected Review es una revisión **holística**: todos los pilares se evalúan, hayan sido o no mencionados en el QAW. Un `QA-xx` priorizado enriquece el análisis de su pilar relacionado, pero **no decide si el pilar se evalúa** — eso lo decide esta guía.

## Catálogo de pilares (agnóstico de nube)

| Pilar | Definición | Prácticas de ejemplo | AWS | Azure | GCP |
|---|---|---|---|---|---|
| Excelencia Operacional | Capacidad de operar, monitorear y mejorar el sistema en producción | Runbooks, despliegues automatizados, IaC, gestión de incidentes, mejora continua | Operational Excellence | Operational Excellence | Operational Excellence |
| Seguridad | Proteger datos, sistemas y activos mientras se entrega valor | Defensa en profundidad, mínimo privilegio, cifrado en tránsito/reposo, gestión de identidad, respuesta a incidentes | Security | Security | Security |
| Confiabilidad | Capacidad de recuperarse de fallos y satisfacer la demanda | Recuperación ante desastres, auto-healing, pruebas de resiliencia, gestión de cambios | Reliability | Reliability | Reliability |
| Eficiencia de Rendimiento | Uso eficiente de recursos de cómputo para cumplir requisitos | Selección de tipo de recursos según carga, escalado elástico, monitoreo de latencia, revisión periódica de arquitectura | Performance Efficiency | Performance Efficiency | Performance Optimization |
| Optimización de Costos | Evitar gasto innecesario mientras se cumplen los objetivos | Right-sizing, instancias reservadas/spot, apagado de ambientes no productivos, monitoreo de costos por etiqueta | Cost Optimization | Cost Optimization | Cost Optimization |
| Sostenibilidad | Minimizar el impacto ambiental de las cargas de trabajo | Selección de regiones de menor huella de carbono, right-sizing, arquitecturas serverless/elásticas que evitan sobre-aprovisionamiento | Sustainability | (integrado en Cost/Operational Excellence — Microsoft no lo trata como pilar formal) | Sustainability |

Si el proyecto ya confirmó un proveedor de nube único, usa el nombre y agrupación oficial de ese proveedor en `08`; si es multi-nube o agnóstico, usa esta tabla como referencia neutral.

## Cómo usarlo en `08-Well-Architected.md`

1. Recorre los 6 pilares de la tabla — ninguno queda sin fila en la matriz de cobertura (ver plantilla en `references/plantilla-documento-arquitectura.md`).
2. Para cada pilar, revisa si algún `QA-xx` priorizado en `07` le aplica directamente: si sí, deriva principios/prácticas (`PD-xx`/`BP-xxx`) de ese escenario.
3. Si ningún `QA-xx` prioritario toca el pilar, igual documenta al menos una recomendación base (ej. Seguridad y Confiabilidad casi nunca se marcan "No aplica" en un sistema con datos de negocio) o márcalo **No aplica** con un motivo concreto (ej. Sostenibilidad en una carga de trabajo interna, bajo volumen, sin objetivo de sostenibilidad del cliente).
4. No marques "No aplica" solo porque el QAW no lo mencionó — eso es "Considerado y descartado" (con motivo), un estado distinto: úsalo cuando sí se evaluó el pilar pero se concluyó que no amerita prácticas adicionales a las que ya trae el enfoque elegido.

## Revisión a nivel de pregunta (WAFR)

La matriz por pilar es el mínimo. Cuando el proveedor sea AWS, el sector sea regulado o el cliente pida una revisión Well-Architected formal, profundiza a nivel de **pregunta** del framework. Registra en `08` la tabla:

| Pregunta | Estado | Evidencia (artefacto/ID) | Riesgo | Acción / dueño |
|---|---|---|---|---|
| SEC 2 — Identidades de personas y máquinas | Cubierta | `17.6` §4, `SEC-004` | — | — |
| REL 13 — Recuperación ante desastres | Parcial | `17`, `QA-03` | Alto (HRI) | `DA-007` pendiente — owner plataforma |

Estados: `Cubierta`, `Parcial`, `No cubierta`, `No aplica` (con motivo). Riesgo: `Alto (HRI)`, `Medio (MRI)` o `Ninguno`, siguiendo la terminología de la herramienta de AWS. Todo HRI abre un riesgo en `21` y bloquea `25` si afecta un `QA-xx` priorizado.

### Preguntas del AWS Well-Architected Framework (lente `wellarchitected`)

| Pilar | Preguntas |
|---|---|
| Excelencia Operacional | OPS 1 prioridades · OPS 2 estructura organizacional · OPS 3 cultura · OPS 4 observabilidad · OPS 5 reducir defectos y mejorar el flujo a producción · OPS 6 mitigar riesgos de despliegue · OPS 7 preparación para soportar la carga · OPS 8 uso de la observabilidad · OPS 9 salud de las operaciones · OPS 10 gestión de eventos · OPS 11 evolución de las operaciones |
| Seguridad | SEC 1 operación segura · SEC 2 identidades · SEC 3 permisos · SEC 4 detección · SEC 5 protección de red · SEC 6 protección de cómputo · SEC 7 clasificación de datos · SEC 8 datos en reposo · SEC 9 datos en tránsito · SEC 10 respuesta a incidentes · SEC 11 seguridad en el ciclo de vida de la aplicación |
| Confiabilidad | REL 1 cuotas y restricciones · REL 2 topología de red · REL 3 arquitectura de servicios · REL 4 interacciones que previenen fallos · REL 5 interacciones que mitigan fallos · REL 6 monitoreo de recursos · REL 7 adaptación a la demanda · REL 8 implementación de cambios · REL 9 backups · REL 10 aislamiento de fallos · REL 11 tolerancia a fallos de componentes · REL 12 pruebas de confiabilidad · REL 13 recuperación ante desastres |
| Eficiencia de Rendimiento | PERF 1 selección de recursos y patrones · PERF 2 cómputo · PERF 3 datos · PERF 4 red · PERF 5 proceso de mejora continua |
| Optimización de Costos | COST 1 gestión financiera cloud · COST 2 gobierno del uso · COST 3 monitoreo de costo · COST 4 retiro de recursos · COST 5 costo al seleccionar servicios · COST 6 tipo, tamaño y número · COST 7 modelos de precio · COST 8 transferencia de datos · COST 9 demanda y oferta · COST 10 evaluación de servicios nuevos · COST 11 costo del esfuerzo |
| Sostenibilidad | SUS 1 selección de región · SUS 2 alinear recursos a la demanda · SUS 3 patrones de software y arquitectura · SUS 4 gestión de datos · SUS 5 hardware y servicios · SUS 6 procesos organizacionales |

Mapa de evidencias habituales: OPS 4/8 → observabilidad en `14.xx` y `19`; OPS 5/6 → pipeline AS-IS o handoff a Vulcano; SEC 1-6 → `17.6` y `19.1`; SEC 7-9 → `16`/`16.xx` y `19.1`; REL 2/10 → `17.6`; REL 4/5/11 → `18`; REL 9/13 → `16.xx` y `17`; PERF → `05` y `18`; COST → `17.4`/`17.4.1`; SUS → `17` y `17.6`.

### Lentes complementarias

Agrega una lente cuando el dominio la justifique; no reemplaza la revisión base.

| Lente | Cuándo | Énfasis |
|---|---|---|
| Financial Services Industry | Banca, seguros, mercado de capitales | Roles de riesgo, evaluación regulatoria, separación de funciones, credenciales privilegiadas, aislamiento de ambientes SDLC, gestión de llaves, DLP, ransomware, reporte de incidentes a reguladores, niveles de resiliencia, fallas grises, backups y retención |
| Data Analytics | Plataformas de datos y analítica | Despliegue reproducible de jobs, acceso a datos entre sistemas, gobierno de datos y metadatos, formatos y particionamiento |
| Serverless, SaaS, Container Build, Generative AI y otras | Según el patrón principal seleccionado en `10` | Ver la lista vigente de lentes del proveedor |

### Analizar no es recomendar

En Caso B, separa la observación del juicio: primero describe lo que existe (servicios, flujos, patrones) y solo después registra recomendaciones como riesgos en `21` o fases en `24`. Una recomendación escrita como si fuera un hecho observado invalida la evidencia AS-IS.

### Exportación opcional a AWS Well-Architected Tool

Si el cliente usa la herramienta de AWS, genera `08.1-WA-Tool_<Proyecto>.json` con: nombre de workload, ambiente, regiones, lentes (`wellarchitected` más las complementarias) y, por pregunta, las opciones seleccionadas y una nota con la evidencia enlazada. Los `QuestionId`/`ChoiceId` se obtienen de la herramienta (`aws wellarchitected list-answers`), **nunca se inventan**: si no se pueden consultar, el archivo queda como borrador con la pregunta en notación `SEC 2` y la carga la hace un responsable humano. Azure ofrece la *Azure Well-Architected Review* y Google Cloud el *Architecture Framework*: usa el mismo formato de tabla con su numeración propia.

## Fuente

AWS Well-Architected Framework (preguntas por pilar y lentes tomadas del dataset de `aws-samples/sample-well-architected-acceleration-with-generative-ai`, verifica contra la versión vigente de la herramienta), Microsoft Azure Well-Architected Framework y Google Cloud Architecture Framework. Los nombres de pilar difieren levemente entre proveedores; la tabla usa la terminología más extendida (AWS) como base neutral.
