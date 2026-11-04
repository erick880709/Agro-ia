# Quality gates y handoff

## Gates por repositorio

- Blueprint, manifest, receipt y generator results válidos.
- Fuente, versión, digest, licencia y permisos registrados.
- Diff revisado y sin sobrescrituras fuera de ownership.
- Dependencias instalables/restaurables con lockfile coherente.
- Lint/análisis estático y typecheck pertinentes.
- Build exitoso.
- Pruebas unitarias, integración y contrato del alcance exitosas.
- Health/smoke test y vertical slice mínimo observables.
- Cada endpoint no explícitamente público exige una identidad resuelta desde el contexto autenticado, cableada en la ruta misma (no solo declarada en un módulo de identidad sin usar desde ningún router) — una prueba de contrato/integración debe fallar en `401`/`403` sin credenciales y pasar con ellas.
- Todo proceso de fondo (worker, consumidor de cola, scheduler) tiene una prueba que arranca su ciclo de vida real (`lifespan`/entrypoint del proceso), no solo el handler aislado, y demuestra que procesa al menos un mensaje/job de extremo a extremo.
- Todo flujo de confirmación humana (HITL) tiene una prueba de round-trip por el protocolo real que expone el componente (HTTP/SSE, mensajería, etc.): propuesta → pausa → decisión → reanudación conservando el mismo estado de turno/política — no basta con probar la función interna que ejecuta la acción ya confirmada.
- Todo cliente HTTP con reintento automático que invoque un verbo no idempotente (POST/PATCH/DELETE) admite y propaga una clave de idempotencia derivada de un identificador estable de la operación (p. ej. el id del job/mensaje que la originó) — nunca del número de intento.
- Un endpoint que exige identidad (`Depends`/middleware de auth) sobre un recurso identificado por la URL/payload (`session_id`, `conversation_id`, etc.) también verifica que el principal autenticado sea DUEÑO de ese recurso específico, nunca solo que esté autenticado — el recurso se crea explícitamente ligado al principal (un endpoint de creación que lo genera server-side), nunca de forma implícita en el primer uso de un ID elegido por el llamador.
- Cualquier `RetryPolicy`/clasificador de reintento compuesto por una composition root (no el fallback por defecto del propio cliente HTTP) reutiliza la función clasificadora ya exportada por ese módulo (nunca la reconstruye ni la omite) — una prueba debe invocar la política tal como la ensambla esa composition root y confirmar que clasifica como reintentable un error de transporte/504 real, no solo probar `RetryPolicy` en aislamiento con excepciones genéricas.
- Todo bucle de fondo que procesa una secuencia (consumidor de cola, scheduler) captura la excepción de CADA ítem/job individual y sigue con el siguiente — una excepción de un ítem nunca termina el bucle completo; la tarea de fondo que lo ejecuta está supervisada (se reinicia si termina de forma inesperada) y su vida se refleja en el endpoint de *readiness*, no solo en una lista de configuración estática.
- Un puerto de consumo de cola expone confirmación/abandono del mensaje ya recibido (`ack`/`abandon` o equivalente), no solo `receive()` — sin esa forma, ningún adaptador futuro (ni siquiera uno hacia un broker real) puede implementar redelivery-sin-duplicar-el-efecto; el bucle que lo usa distingue "el trabajo ya se resolvió pero no se pudo reportar" (confirmar de todos modos, para no reintentar un efecto que ya ocurrió) de "el trabajo nunca se resolvió" (abandonar, para permitir redelivery).
- Si un archetype expone una frontera de identidad HTTP, el modo real valida credenciales de verdad (firma/expiración/issuer/audience contra un JWKS u otro mecanismo estándar genérico — nunca atado a un IdP concreto), y cualquier atajo de desarrollo (header de depuración, token fijo) solo funciona cuando el entorno configurado lo declara explícitamente Y no llegó ninguna credencial real — nunca en cualquier entorno por defecto. Documentar el atajo como "placeholder, sustitúyelo antes de producción" sin ese gateo por entorno dentro del propio código no es un control, es una promesa sin verificar.
- Un adaptador real hacia un protocolo de terceros (proveedor de modelo, gateway de mensajería, etc.) traduce TODO el estado que ese protocolo exige para correlacionar una solicitud con su respuesta (p. ej. el id de una tool call en Chat Completions) — un modelo de datos interno más simple que el protocolo real (sin ese id) puede pasar todas las pruebas contra un doble/simulado y aun así ser incompatible con el protocolo real; al menos una prueba debe ejercitar la función de traducción contra la forma exacta que el protocolo real exige, no solo contra el doble.
- Cuando un bucle confirma (`ack`) un ítem para evitar un efecto duplicado en vez de reintentarlo, ese caso queda registrado en un store consultable/resoluble (mismo patrón que un checkpoint de dedup: puerto + adaptador en memoria intercambiable), nunca solo en un log — un log no es un mecanismo de recuperación.
- Una tarea de fondo supervisada (se reinicia sola tras un fallo) espera con backoff acotado entre reinicios, nunca inmediato y sin límite — un fallo persistente desde el arranque no debe convertirse en un bucle cerrado de reinicio-fallo a máxima velocidad de CPU/logs. Que la tarea siga viva (`not task.done()`) tampoco demuestra que esté progresando: expón además cuántos reinicios consecutivos lleva (o una señal de progreso para un bucle de cadencia predecible) para que *readiness* pueda distinguir "viva y sana" de "viva pero crash-looping".
- Un validador JWT/OIDC exige explícitamente la presencia de cada claim de seguridad del que depende (`exp` como mínimo; también `iss`/`aud`/`sub` si el código los usa) — la mayoría de librerías (PyJWT incluida) solo VALIDAN un claim si está presente, nunca exigen su presencia por defecto; un token firmado sin `exp` (que nunca expira) pasa silenciosamente si no se pide explícitamente. Una prueba debe firmar un token sin ese claim y confirmar el rechazo, no solo probar con un token expirado.
- Cada endpoint nuevo que se agregue a un router ya existente hereda CERO control de acceso de sus vecinos — un router documentado como "solo probes de infraestructura" (`/health`/`/ready`) puede terminar hospedando un endpoint administrativo real (lista o muta estado con detalle operativo); ese endpoint necesita su PROPIA credencial (identidad de usuario si aplica, o un token de operador compartido — fail closed si no está configurado) evaluada por sí sola, nunca heredada por estar en el mismo archivo/tag que un healthcheck.
- Cuando una respuesta del proveedor propone varias tool calls a la vez, el ciclo Tool Use intenta TODAS antes de detenerse — que una necesite confirmación humana no debe truncar el procesamiento de las que le siguen en la misma respuesta (ejecutarlas o dejarlas también pendientes); el turno solo se reanuda cuando NINGUNA tool call de esa respuesta sigue pendiente. Una prueba debe proponer al menos dos tool calls en una sola respuesta simulada (una que exija confirmación y otra que no) y confirmar que ambas se resuelven, no solo la primera.
- Sin secretos ni datos del proyecto origen en el arquetipo.
- Sin nuevos artefactos DevOps/IaC/empaquetado operacional.
- Sin drift no declarado en archivos `managed` (`check-drift` contra el receipt).

No omitas un gate fallido: corrige, registra una excepción autorizada o marca el componente bloqueado. Estos gates surgieron de defectos reales que pasaron rondas previas de generación (endpoints de ejemplo sin autenticación cableada, un worker cuyo `lifespan` nunca arrancaba el consumidor, un flujo HITL que registraba la confirmación pero no reanudaba el turno, reintentos POST sin garantía de idempotencia, un endpoint autenticado que igual permitía operar sobre la sesión de otro principal, una política de reintento HTTP compuesta sin su clasificador — nunca reintentaba un error real —, un scheduler que un solo job roto detenía para siempre, un puerto de cola sin forma de confirmar/abandonar un mensaje, una identidad de desarrollo que se aceptaba sin gateo por entorno, un adaptador real que perdía el id de correlación que su propio protocolo exige, un caso de "confirmado sin resolver" que solo quedaba en un log, un supervisor que reiniciaba en bucle cerrado sin backoff, un JWT válido pero sin `exp` que se aceptaba, un `DELETE` administrativo sin ninguna credencial por vivir junto a `/health`, y una tool call que desaparecía en silencio si otra de la misma respuesta necesitaba confirmación primero) — trátalos como gates de primera clase, no como detalle opcional del arquetipo.

## Verificación continua de archivos `managed`

Declarar una ruta como `managed` en el receipt no la protege por sí sola: nada impide que alguien la edite a mano fuera de un run de `solution-baseline`. Usa `check-drift` para cerrar ese hueco sin tener que re-renderizar el arquetipo completo:

```powershell
python "<skill-root>/scripts/solution_baseline.py" check-drift --root <repo>
```

Compara el hash actual de cada ruta `managed` contra el hash registrado en `receipt.yaml` al momento de generarla. Una ruta `managed` sin hash registrado se reporta como `unverifiable`, no como violación — corrige el receipt para que quede verificable. Un hallazgo `modified` o `missing` significa que el archivo se editó o borró fuera del flujo del skill: no lo sobrescribas automáticamente, resuélvelo como `reconcile`/`upgrade` o regístralo como drift `accepted` con owner. Puede colgarse como gate liviano en CI (sin necesitar el motor del generador) para detectar el tamper antes de mezclar cambios.

## Trazabilidad de quality gates declarados

Un `quality_gate` declarado en `components[].quality_gates` del blueprint (p. ej.
`boundaries-lint`, `typecheck`, `integration-tests-msw`) que nunca aparece en
`receipt.validations[].id` desaparece en silencio: nada lo marca como
incumplido, simplemente no corrió. Ciérralo con:

```powershell
python "<skill-root>/scripts/solution_baseline.py" check-gate-coverage --blueprint <blueprint.yaml> --component <id> --receipt <repo>/.solution-baseline/receipt.yaml
```

Cualquier gate en `missing_gates` bloquea que el componente se marque
`validated`/`completed` — regístralo como `blocked`/`partial` con handoff
explícito, o ejecútalo antes de cerrar el componente.

### Reglas de arquitectura sin mecanismo de verificación

Una regla de arquitectura (`CC-xxx`) declarada en `security_requirements` sin
ningún lint rule ni test automatizado que la verifique no está cumplida, esté
o no violada hoy: nadie la está revisando. Al reconciliar o crear un
componente, cada `CC-xxx` declarado debe tener al menos un mecanismo
ejecutable (regla de lint, prueba de arquitectura) o quedar registrado como
blocker/gap explícito — nunca como texto sin enforcement y sin rastro.

### Boundaries con lista fija (allow-list) desincronizada

Un boundary de arquitectura implementado como lista fija de nombres (p. ej.
un array de features en la config de ESLint) no tiene relación automática
con las carpetas reales en disco: deja de cubrir cualquier carpeta agregada
después de que la lista se editó por última vez, y el gate sigue "pasando"
sin que en realidad esté revisando esas carpetas. Detéctalo con:

```powershell
python "<skill-root>/scripts/solution_baseline.py" check-boundary-coverage --root <repo> --discover-glob "src/features/*" --declared <feature-1> --declared <feature-2> ...
```

Cualquier entrada en `undeclared` es una carpeta real sin cobertura de
boundary — trátalo igual que un gate en rojo, no como hallazgo cosmético.
Prefiere, en el propio arquetipo/generador, un mecanismo de **descubrimiento
genérico** (enumerar el directorio en tiempo de verificación) en vez de una
lista fija — es el mismo criterio que ya exigen `CC-001`/`CC-006`/`CC-012`/
`CC-013`/`CC-015`/`CC-016` en los arquetipos Python de este catálogo
(`discover_modules()`/`discover_native_shapes_modules()`, nunca una lista
codificada).

## Conformidad con el sistema de diseño

Un componente `web` o `library` que declara `design_system` en el blueprint consume un sistema de diseño congelado —tokens (`*.tokens.json`, W3C Design Tokens), catálogo de componentes y manifiesto de assets de marca— con el mismo rigor que un contrato OpenAPI: se congela (hash registrado) antes de generar consumidores y cualquier cambio posterior es una revisión explícita, no un ajuste local. Verifícalo con:

```powershell
python "<skill-root>/scripts/solution_baseline.py" check-design-conformance --root <repo> --blueprint <blueprint.yaml> --component <id> --solution-root <raíz-de-la-solución>
```

El comando falla cuando `design_system.status` no es `confirmed`, no se declararon tokens, falta un artefacto declarado, un artefacto no tiene `sha256` (sin congelar) o su hash difiere del registrado, o cuando el código del componente contiene más literales de estilo (colores hex/`rgb()`/`hsl()`, `font-size` en px) fuera de `style_zones`/`literal_exemptions` que `max_literal_violations`. En brownfield usa `max_literal_violations` como trinquete: regístralo con el conteo actual y un owner, y bájalo en cada reconcile; nunca lo subas para hacer pasar un cambio.

Cuando el adaptador los declare, ejecuta también `design-conformance` y `a11y`, y exige en el vertical slice: tema y estilos derivados de los tokens congelados (no valores copiados), assets de marca tomados del manifiesto (nunca redibujados) y ausencia de violaciones de accesibilidad serias o críticas en los componentes compartidos. Una pieza faltante del sistema de diseño se registra como brecha para su dueño (UX / sistema de diseño), no se inventa dentro del componente.

Un arquetipo que declara la capability `design-system` genera sus dos golden projects con paquetes de tokens distintos (por ejemplo uno neutral y uno de marca), y ambos pasan los mismos gates sin cambiar código: es la prueba de que el arquetipo no depende de ninguna marca.

## Pruebas de arquetipo

Cada candidato debe generar dos golden projects con nombres/parámetros distintos, repetir render de forma determinista, rechazar combinaciones inválidas, probar pairwise las capabilities relevantes y ejecutar upgrades desde versiones declaradas como soportadas. Cuando el arquetipo expone endpoints, procesos de fondo, un flujo HITL o reintentos HTTP, los golden projects ejercitan también los gates de comportamiento observable de la lista anterior (autenticación por endpoint y pertenencia del recurso, arranque real del proceso de fondo y su supervisión, round-trip HITL, idempotencia en reintentos, clasificación real del reintento HTTP, ack/abandon del consumidor) — no basta con que compile y con que los tests unitarios aislados pasen; una mutación deliberada de cada uno (revertirlo y confirmar que la prueba correspondiente falla) es la forma de verificar que el gate tiene dientes, no solo forma.

Al menos uno de los dos golden projects se genera con los defaults reales de `copier.yml` sin sobreescribir ningún parámetro (nunca solo con nombres de prueba más cortos que el default real) — un `package_name`/nombre derivado más largo que el usado habitualmente en pruebas puede exceder el límite de longitud de línea de un import ya existente y ese hallazgo queda enmascarado si todos los golden projects usan parámetros de prueba convenientemente cortos (hallazgo de revisión, 2026-09-11: un import agregado en una ronda de fixes solo rompía `ruff` con el `project_name` por defecto real del arquetipo, nunca con los nombres de prueba usados hasta entonces).

## Evaluaciones del skill/agente

Incluye escenarios greenfield, brownfield con las cinco categorías de ownership, catálogo no confiable, arquitectura contradictoria, contrato no congelado, fallo parcial, upgrade conflictivo, falta de permiso remoto e intento de invadir el alcance de Vulcano.

Evalúa decisiones y efectos observables; evita tests basados únicamente en frases o headings.

## Handoff a Builder/Ranger

Entrega:

- Componentes creados/reconciliados y sus repositorios.
- Blueprint y fuentes arquitectónicas.
- Arquetipo/capabilities, versiones, digests y overlays.
- Comandos reales de desarrollo y validación.
- Contratos canónicos y estado de generación de clientes/modelos.
- Decisiones, supuestos, drift aceptado, deuda y bloqueos.
- Receipts y evidencias de gates.
- Alcance pendiente para `builder` y revisiones sugeridas para `ranger`.

## Handoff a Vulcano

Entrega solo metadatos, nunca artefactos ejecutables: no generes ni ejecutes Dockerfiles, IaC, pipelines ni manifiestos de despliegue.

El artefacto es `<repository>/.solution-baseline/vulcano-handoff.yaml` por componente, un subconjunto estructuralmente compatible con el vocabulario de Score (score.dev/v1b1: `containers`, `service.ports`, `resources`) para los campos que cubre. Declara intención de la aplicación, no cómo desplegarla:

- `containers.<nombre>.variables`: nombres de variables de configuración requeridas, sin valores reales (igual regla que `.env.example`).
- `containers.<nombre>.livenessProbe` / `readinessProbe`: los health endpoints ya definidos para la aplicación.
- `service.ports`: puertos que la aplicación expone.
- `resources`: dependencias externas declaradas por tipo (`postgres`, `redis`, `queue`, etc.) con `required`, sin aprovisionarlas.
- `restrictions`: restricciones operativas que Vulcano debe respetar (afinidad, conectividad, orden de arranque).

No incluye `image`, `volumes`, `files` ni `resources.limits/requests`: construir la imagen, dimensionar capacidad y aprovisionar son responsabilidad de Vulcano. Valida antes de entregar:

```powershell
python "<skill-root>/scripts/solution_baseline.py" validate --kind handoff --file <repo>/.solution-baseline/vulcano-handoff.yaml --strict
```

En modo estricto, `web`/`api` deben declarar al menos un puerto y cada contenedor debe declarar al menos un health probe.

## Reporte final

Resume resultado, archivos/repositories modificados, validaciones ejecutadas, excepciones y siguiente paso. Distingue `completed`, `partial` y `blocked`. No ocultes resultados parciales detrás de una conclusión global.

Esa distinción no es solo narrativa: un nodo del DAG (`kind: render/apply/validate`) nunca se registra `status: completed`, ni una entrada de `instances[]` nunca se registra `status: validated`, si el step `validate` real correspondiente para ese repositorio no reportó `status: succeeded` — usa `partial` en ese caso, incluso si el desvío quedó `accepted_drift` con handoff a `builder`. `validate --kind run` (sin necesitar `--strict`) rechaza esta inconsistencia automáticamente; no dependas de revisión manual para detectarla.
