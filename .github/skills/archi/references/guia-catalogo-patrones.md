# Guía: Catálogo y validación de patrones

Usa esta guía para clasificar y evaluar patrones en `09`, `10.1`, `14.xx`, `17`, `18`, `19` y `20`. Es un catálogo de candidatos, no una lista para copiar: aplica un patrón solo si resuelve un problema concreto y conserva evidencia de su validación.

## Contenido

1. Taxonomía canónica
2. Patrones arquitectónicos
3. Patrones de diseño
4. Patrones cloud
5. Patrones de IA
6. Validación por tipo
7. Enrutamiento documental

## 1. Taxonomía canónica

| Tipo | Definición | Ejemplos |
|---|---|---|
| Táctica arquitectónica | Decisión/mecanismo que influye en un atributo de calidad específico | Retry, circuit breaker, cache-aside, timeout, idempotencia |
| Patrón arquitectónico | Organización fundamental de responsabilidades, despliegue, comunicación o datos del sistema o de un scope significativo | Monolito modular, microservicios, microfrontends, event-driven, hexagonal, CQRS |
| Patrón de diseño | Solución reutilizable a un problema recurrente dentro de uno o más componentes | Repository, Factory, Strategy, Observer, Command |
| Patrón cloud | Solución recurrente para despliegue, integración, escalado u operación cloud-native | Sidecar, Ambassador, Strangler Fig, BFF, competing consumers |
| Patrón de IA | Organización recurrente de modelo, contexto, herramientas, datos, evaluación y control | RAG, context engineering, fine-tuning, agente, model gateway |

Clasifica por el propósito dominante, no por el nombre popular. Registra un patrón una sola vez y enlaza los demás tipos relacionados. Solo las tácticas/patrones arquitectónicamente significativos promovidos al catálogo `18` reciben `TP-xxx`; un patrón de diseño local no significativo se identifica por nombre dentro de su `14.xx`, sin crear un ID global ni una ficha vacía.

Una solución compuesta conserva IDs separados por responsabilidad. Por ejemplo, Event-Driven (patrón arquitectónico), Queue-Based Load Leveling (patrón cloud), backpressure e idempotencia (tácticas arquitectónicas) son elementos distintos y se enlazan en `Interacciones y dependencias` de `18`; no los fusiones en un único `TP-xxx` ni los dupliques con nombres distintos.

Clean Code no es un sexto tipo de patrón: es un estándar transversal de calidad interna gobernado mediante `CC-xxx` según `references/guia-clean-code.md`. Un patrón de diseño puede apoyar una regla de Clean Code, pero conserva su clasificación y evidencia propias.

## 2. Patrones arquitectónicos

| Patrón | Úsalo cuando | Valida obligatoriamente | Evita cuando |
|---|---|---|---|
| Monolito modular | Un equipo o despliegue único puede sostener el dominio con límites internos claros | módulos, dependencias permitidas, ownership, pruebas de límites y ruta de extracción | se requieren despliegue/escalado/aislamiento independientes demostrados |
| Microservicios | Bounded contexts, autonomía de equipos o aislamiento operativo justifican distribución | fronteras, datos por servicio, contratos, consistencia, operación, costo y fallos distribuidos | el volumen/equipo no paga su complejidad o los límites de dominio son inestables |
| Microfrontends | Capacidades UI estables y varios equipos necesitan releases/rollback autónomos dentro de una experiencia integrada | alternativa SPA modular, shell/composición, owners, unidades desplegables, contratos/estado, UX, performance, seguridad, pruebas, observabilidad y rollback según `references/guia-microfrontends.md` | un equipo/release puede sostener la UI, fronteras inestables o la coordinación/plataforma cuesta más que la autonomía |
| Event-Driven | Se necesita desacoplamiento temporal, reacción a eventos o integración asíncrona | semántica de evento, orden, duplicados, idempotencia, esquema, replay, observabilidad y consistencia | el proceso exige respuesta sincrónica inmediata y la asincronía no aporta valor |
| Hexagonal / Ports and Adapters | Deben aislarse dominio, UI, persistencia o proveedores volátiles | dirección de dependencias, puertos, adaptadores reales y pruebas del núcleo | solo agrega capas sin dependencia variable ni dominio relevante |
| CQRS | Lectura y escritura tienen modelos, cargas o ciclos de evolución materialmente distintos | ownership, proyección, lag, consistencia, reconstrucción y operación | un único modelo satisface ambos lados sin fricción demostrada |
| Capas | La separación por responsabilidades técnicas mejora comprensión y gobierno | dependencias entre capas, reglas de acceso y ausencia de saltos/ciclos | las capas se convierten en pasarela ceremonial o impiden límites de dominio |

No todos estos patrones pertenecen al mismo nivel de decisión:

- `09` compara **configuraciones de descomposición y despliegue** — consolidada, híbrida o distribuida — usando Monolito Modular, Microservicios y Event-Driven solo donde afecten la topología de un scope. Para el canal UI compara SPA modular/Microfrontends como eje propio cuando cambie topología, entrega u operación.
- Microfrontends se selecciona por canal/capacidad siguiendo `references/guia-microfrontends.md`; su aplicación vive en `10.1`, `14`-`17`. No se deriva automáticamente de Microservicios.
- Hexagonal y Capas se aplican normalmente dentro de cada contenedor significativo en `14.xx`.
- CQRS se decide por bounded context, contenedor o caso de uso y se materializa en `14.xx`/`16.xx`; no lo extiendas a todo el sistema sin drivers transversales.
- Solo eleva Hexagonal/CQRS a `09` cuando su aplicación generalizada cambia materialmente infraestructura, consistencia, costo, operación o comparación de alternativas.

Una configuración híbrida no es un patrón adicional: es la composición explícita de distintas formas de despliegue por capacidad, según `references/guia-alternativas-solucion.md`.

## 3. Patrones de diseño

| Patrón | Problema que debe existir | Evidencia esperada |
|---|---|---|
| Repository | Separar lógica de dominio de acceso persistente con colección/aggregate semantics | interfaz usada por dominio, implementación aislada y pruebas sin infraestructura |
| Factory | Construcción compleja, variante o con invariantes que no debe dispersarse | punto único de creación, invariantes y pruebas de variantes |
| Strategy | Varias políticas intercambiables bajo un contrato estable | al menos dos estrategias reales o una variación confirmada; selección explícita |
| Observer / Publish-Subscribe local | Varios componentes reaccionan a cambios sin acoplamiento directo | ciclo de suscripción, errores, orden y liberación de recursos |
| Command | Encapsular una acción para cola, auditoría, retry o deshacer | contrato, resultado, idempotencia y manejo de error |
| Adapter | Traducir un contrato externo o variante tecnológica | límite, traducción, errores y pruebas de contrato |
| Decorator | Agregar comportamiento transversal composable sin modificar el núcleo | orden de composición, costo y pruebas por combinación |

Documenta patrones locales en `14.xx`. Promuévelos a `18` solo si afectan un `QA-xx`, varios componentes/contenedores, un riesgo o una `DA-xxx`. No fuerces patrones GoF donde una función, módulo o composición simple sea suficiente.

## 4. Patrones cloud

| Patrón | Propósito | Validación mínima |
|---|---|---|
| Sidecar | Ejecutar capacidad auxiliar junto a una carga principal | ciclo de vida, recursos, comunicación local, fallo y ownership operativo |
| Ambassador | Externalizar conectividad/protocolo hacia servicios remotos | rutas, credenciales, retries, observabilidad y punto de fallo |
| Strangler Fig | Migrar gradualmente desde legacy | enrutamiento, coexistencia, ownership de datos, rollback y criterio de retiro |
| Backend for Frontend (BFF) | Adaptar API/experiencia a un canal específico | límites por canal, duplicación, seguridad y evolución independiente |
| API Gateway / Gateway Aggregation | Centralizar entrada y/o composición | autenticación, límites, timeout, degradación y evitar lógica de negocio centralizada |
| Queue-Based Load Leveling | Amortiguar picos y proteger consumidores | capacidad, backpressure, latencia, DLQ y recuperación |
| Competing Consumers | Escalar procesamiento paralelo de una cola | orden, partición, idempotencia, fairness y poison messages |
| Claim Check | Mover payload grande fuera del mensaje | seguridad, expiración, atomicidad, acceso y limpieza |
| External Configuration Store | Compartir configuración dinámica | versionado, secretos, caché, fallback y auditoría |
| Sharding | Distribuir datos/carga por clave | clave, rebalanceo, consultas cruzadas, hotspots y recuperación |

Todo patrón cloud debe mapearse a `CT-xx`, ambientes y proveedor/servicio en `17`, además de seguridad, observabilidad, costo, lock-in, failure domains y portabilidad. No marques `Implementada` sin IaC, configuración o evidencia del entorno.

## 5. Patrones de IA

| Patrón | Úsalo cuando | Validación mínima |
|---|---|---|
| RAG | La respuesta necesita conocimiento externo actualizable y trazable | corpus, permisos, chunking, recuperación, grounding/citas, precisión, latencia y costo |
| Context Engineering | El comportamiento depende de construir contexto, memoria, instrucciones y herramientas | presupuesto de contexto, procedencia, prioridad, sanitización, versionado y evaluación |
| Fine-tuning | Se requiere comportamiento estable que prompt/RAG no logra con costo o calidad aceptable | dataset/licencia, baseline, evaluación separada, drift, rollback y costo total |
| Agent Pattern | El modelo planifica/itera y usa herramientas para alcanzar una meta | límites, permisos, presupuesto, terminación, memoria, auditoría y fallback humano |
| Tool Calling | El modelo invoca capacidades determinísticas | schemas, autorización, validación, idempotencia, timeout y manejo de resultados |
| Routing / Model Gateway | Se elige modelo, prompt o flujo según tarea/riesgo | política, fallback, calidad por ruta, costo, latencia y versionado |
| Guardrails | Se aplican controles de entrada/salida y política | amenazas, cobertura, falsos positivos/negativos, bypass y escalamiento |
| Human-in-the-loop | Una decisión requiere revisión, excepción o responsabilidad humana | umbral, cola, SLA, evidencia presentada y autoridad de override |
| Semantic Cache | Consultas semánticamente equivalentes pueden reutilizar respuesta | similitud, TTL, privacidad, invalidación, exactitud y ahorro medido |
| Evaluator-Optimizer | Una etapa evalúa y mejora iterativamente una salida | criterio de parada, independencia del evaluador, costo y evidencia de mejora |

Para cualquier patrón de IA registra modelo/versión, prompt/contexto, datos, evaluación offline/online, grounding/alucinación, prompt injection, PII, permisos de herramientas, observabilidad, latencia, costo, fallback y responsabilidad humana. Un prototipo convincente no equivale a validación productiva.

El campo "costo" de RAG, Fine-tuning, Agent Pattern, Tool Calling, Routing/Model Gateway y Semantic Cache no es una palabra suelta: se calcula siguiendo `references/guia-costos-ia.md` (tokens de entrada/salida por capacidad, volumen mensual, rango entre modelos candidatos cuando no hay uno elegido) y su resultado vive en `17.4`/`17.5`, no repetido aquí.

## 6. Validación por tipo

| Tipo | Pregunta de validación |
|---|---|
| Táctica arquitectónica | ¿La prueba demuestra que el mecanismo ayuda a cumplir la medida del `QA-xx` sin trade-off inaceptable? |
| Patrón arquitectónico | ¿La topología, límites, datos, comunicación y operación materializan los drivers mejor que las alternativas? |
| Patrón de diseño | ¿Resuelve un problema recurrente real con menor acoplamiento/complejidad que una solución simple? |
| Patrón cloud | ¿Funciona en failure domains reales con seguridad, observabilidad, costo y lock-in aceptados? |
| Patrón de IA | ¿Supera evaluación representativa con riesgos, costo, latencia, gobernanza y fallback controlados? |

Los estados permitidos siguen `references/guia-tacticas-patrones.md`. `Seleccionada` exige decisión; `Implementada` exige evidencia; `Validada` exige prueba con umbral. Si falta evidencia, conserva `Propuesta` en el campo Estado y escribe `Missing evidence` en el campo de evidencia o parámetro pendiente; no uses `Missing evidence` como estado.

## 7. Enrutamiento documental

La propiedad es única **por faceta**, no un único archivo para todo el ciclo: comparación, selección, aplicación, mecanismo transversal y razonamiento son contenidos diferentes. Los documentos posteriores enlazan; no copian el contenido del dueño de la faceta.

| Tipo | Comparación / selección | Aplicación materializada | Índice, decisión y auditoría |
|---|---|---|---|
| Táctica arquitectónica | `05` identifica el `QA-xx`; `20` decide cuando hay alternativa relevante | `14.xx` y flujo aplicable | `18` posee mecanismo/validación; `25` audita |
| Patrón arquitectónico | `09` compara los que cambian configuración macro o composición frontend; `10` registra esa selección | `14`-`17` poseen topología; `10.1`/`14`-`17` poseen Microfrontends; `14.xx` posee Hexagonal/Capas y `14.xx`/`16.xx` CQRS localizado | `18` indexa los significativos; `20` posee razonamiento; `25` audita |
| Patrón de diseño | No requiere selección global salvo impacto arquitectónico | `14.xx` posee problema, alcance y uso local | `18` solo si es significativo; `20` solo si requiere decisión; `25` audita |
| Patrón cloud | `09` compara cuando diferencia alternativas; `10` registra selección | `17` posee mapeo a proveedor, ambientes y operación | `18` indexa; `20` decide; costos y `25` validan |
| Patrón de IA | `09` compara si cambia la alternativa; `10` registra selección | `14.xx` posee aplicación interna; `19` posee evaluación transversal de datos/modelo/guardrails/costo/fallback | `18` indexa; `20` decide; `21` registra riesgos; `25` audita |
