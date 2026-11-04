# Preguntas guía por archivo

## Índice

- [DevOps Strategy](#devops-strategy)
- [Infrastructure as Code](#infrastructure-as-code)
- [Observability](#observability)

Para ir a un archivo, quitar el prefijo numérico del output y buscar
`### <nombre-base-del-archivo>.md`. Seleccionar únicamente preguntas
no resueltas; el banco no es un cuestionario para disparar completo.

Banco de preguntas para la Fase 2, paso 2 del `SKILL.md`. Para cada archivo: qué se hereda y
NO debe volver a preguntarse, señales en el repo que reemplazan la pregunta, y las preguntas a
hacer solo si el dato sigue faltando. No dispares el bloque completo — selecciona lo que
realmente falte, agrupado en un máximo de 5-6 preguntas por ronda.

Estas preguntas cubren el contenido normal del archivo (greenfield o AS-IS). Cuando el pilar
tiene evidencia real y `references/senales-modernizacion.md` detectó hallazgos (Fase 0.3), se
suma **una** pregunta más, ya cubierta en el paso 1 de la Fase 2 del `SKILL.md`: si el
arquitecto quiere solo el AS-IS o también el TO-BE con gap analysis y roadmap — no la repitas
aquí, ya está resuelta antes de llegar a este banco de preguntas.

---

## devops-strategy/

### repository-management.md

**Preguntas:**
- ¿Repositorio de código y de documentación separados, o todo en un mismo repo (monorepo con
  carpeta de docs)?
- ¿En qué herramienta/instancia vive cada uno (Azure DevOps, GitHub, SharePoint, Confluence) y
  de quién es la instancia (cliente o proveedor)?
- ¿Qué estructura de carpetas de alto nivel tiene el repositorio de documentación (si existe
  uno separado)?
- ¿Cómo se gestionan los permisos y accesibilidad por rol (quién puede leer, escribir, aprobar)?
- ¿Hay convención de nomenclatura de repos si el proyecto usa varios (uno por servicio, uno por
  capa)?

### task-management.md

**Preguntas:**
- ¿Qué herramienta gestiona el tablero de tareas (Jira, Azure Boards, GitHub Projects, Trello)?
- ¿Qué columnas tiene el flujo (Backlog → To Do → In Progress → In Review → Done, u otro)?
  ¿Hay límites WIP por columna?
- ¿Qué tipos de ítem se usan y cómo se diferencian (épica, historia de usuario, tarea técnica,
  bug)?
- ¿Cuál es la Definition of Ready (qué debe cumplir un ítem para entrar a un sprint) y la
  Definition of Done (qué debe cumplir para cerrarse)?
- ¿Hay convención de nombres/IDs para los ítems del tablero (y coincide con la convención de
  nombre de rama de `04-branching-strategy.md`)?

### incident-management.md

**Preguntas:**
- ¿Qué niveles de severidad existen para incidentes/bugs (ej. Crítico/Alto/Medio/Bajo) y qué
  criterio define cada uno?
- ¿Qué tiempo de respuesta/resolución se espera por nivel de severidad (SLA)?
- ¿Cuál es el flujo desde que se reporta un incidente hasta que se cierra (quién lo triagea,
  quién lo asigna, quién valida el cierre)?
- ¿Qué campos debe tener un reporte de bug (título, pasos para reproducir, comportamiento
  esperado vs. real, evidencia, severidad, ambiente)?
- ¿Quién es responsable de atender cada nivel de severidad (on-call, equipo de desarrollo,
  soporte de primer nivel)?
- ¿Quién asume Incident Commander, operaciones, comunicaciones y scribe? ¿Qué canal técnico,
  status page y frecuencia de actualización se usan?
- ¿Cuál es el criterio de cierre y cómo se gestionan postmortems sin culpa y acciones con owner,
  fecha y seguimiento?

**Nota:** si ya existe `observability/06-alerting.md` y `observability/07-runbooks.md`, este archivo
no debe redefinir la mitigación técnica (eso vive en `07-runbooks.md`) — cubre el **proceso de
gestión** del incidente (severidad, flujo, responsables, SLA), no los pasos de diagnóstico.

### devops-overview.md

**Primer archivo de la sesión — no depende de ningún otro archivo de `vulcano`.** Solo hereda de
baseline: tamaño y composición del equipo (bloque 10 de `archi`, si ya fue relevado), y las
respuestas de la Fase 0.4 (plataforma preferida, herramientas corporativas obligatorias,
madurez del equipo).

**No preguntes aquí el nombre final de cada herramienta** (CI/CD, IaC, observabilidad) — eso se
resuelve en su propio archivo más adelante en la secuencia. Este archivo solo pregunta el
criterio con el que se van a elegir, no la elección en sí.

**Preguntas:**
- ¿Cuál es la filosofía de entrega del equipo (continuous deployment, continuous delivery con
  aprobación manual, releases programados)?
- ¿Qué roles existen hoy alrededor de DevOps (equipo dedicado, cada squad es dueño de su
  pipeline, un solo owner de plataforma)?
- ¿Qué criterio debe guiar la selección de herramientas más adelante (preferencia por open
  source, estándar corporativo ya exigido, expertise previo del equipo, soporte multi-nube)? Si
  ya se resolvieron herramientas corporativas obligatorias en la Fase 0.4, resúmelas aquí como
  criterio ya fijado, no las vuelvas a preguntar.
- ¿Existe algún documento de gobernanza DevOps previo que este archivo deba respetar o
  reemplazar?

### branching-strategy.md

**Señal en el repo:** revisa el historial de ramas reales (`git branch -a`, patrones de nombre)
y reglas de protección visibles — si ya hay un patrón consistente, propónlo como borrador en
vez de preguntar desde cero.

**Preguntas:**
- ¿Trunk-based development, GitFlow, GitHub Flow, o un híbrido propio?
- ¿Cómo se nombran las ramas de feature/fix/hotfix (convención de prefijos)?
- ¿Quién aprueba un PR antes de merge (mínimo de revisores, code owners obligatorios)?
- ¿Se permite merge directo a la rama principal en algún caso (hotfix de producción)?
- ¿Squash, merge commit o rebase al integrar?

### ci-cd.md

**Hereda de:** `04-branching-strategy.md` (qué rama dispara qué pipeline),
`05-environments.md` (a qué ambientes despliega cada etapa) y `resources/qa/` si ya existe.
Como `06-ci-cd.md` se genera antes de `07-continuous-testing.md`, define inicialmente etapas y
gates preliminares; al generar `07-continuous-testing.md`, reconcilia ambos archivos y actualiza
en CI/CD los gates y enlaces.

**Señal en el repo:** si ya existe `.github/workflows/`, `azure-pipelines.yml`, `Jenkinsfile`,
etc., documenta el AS-IS a partir de ese archivo real (etapas, triggers, jobs) y solo pregunta
lo que el código no deja claro (por qué esa decisión, planes de cambio). Busca además
`sonar-project.properties`, `.codeclimate.yml`, `qodana.yaml`, configuración de linters/análisis
estático y reportes/gates de calidad en pipeline para no preguntar umbrales ya observables.

**Preguntas — Integración Continua:**
- ¿Qué herramienta de CI/CD se usa o se va a usar?
- ¿Qué dispara un build (push, PR, tag, cron)?
- ¿Qué etapas tiene el pipeline (build, test, análisis estático, empaquetado, despliegue)?
- ¿Hay quality gates que bloquean el pipeline? Para cada gate: ¿qué umbral concreto y qué pasa
  si no se cumple (bloquea el merge, solo advierte)?
- ¿Quién es responsable de configurar, mantener y revisar los reportes del pipeline?
- ¿El artefacto se construye una sola vez y se promueve por digest? ¿Cómo se gestionan cache,
  concurrencia, cancelación, timeout/retry y runners self-hosted?
- ¿Qué identidad usa el pipeline (OIDC/workload identity o secreto persistente) y cuáles son sus
  permisos mínimos por ambiente?

**Preguntas — Inspección Continua y Deuda Técnica:**
- ¿Qué herramienta o capacidad inspecciona calidad y cómo publica feedback en el PR? Si no hay
  una confirmada, define primero capacidades requeridas; no asumas SonarQube u otro producto.
- ¿Qué métricas aplican y cómo se definen: cobertura de código nuevo, duplicación, complejidad,
  mantenibilidad/confiabilidad e issues bloqueantes? Para cada una: ¿cuál es la fuente,
  baseline, umbral objetivo y consecuencia del gate?
- ¿Los gates evalúan código nuevo mediante baseline/ratchet o bloquean también deuda histórica?
  ¿Cómo se evita paralizar cambios por problemas preexistentes sin normalizar deuda nueva?
- ¿Cómo se registra y prioriza la deuda aceptada: impacto, owner, SLA/fecha objetivo, criterio de
  salida y revisión periódica?
- ¿Cómo se aprueban excepciones o falsos positivos y qué vencimiento, revalidación y control
  compensatorio exige cada una?

**Preguntas — Topología y ubicación del/los pipeline(s):**
- ¿El sistema tiene más de una unidad desplegable independiente (ej. backend + frontend con
  App Services/servicios propios, o varios microservicios)? Si sí: ¿un solo pipeline combinado
  que construye/despliega todo, o un pipeline por unidad con trigger por path
  (`paths: include: [<carpeta>/**]`)? No asumas "uno combinado" solo porque es más simple de
  generar — si `infrastructure-as-code/06-modules.md` ya crea cómputo separado por componente
  (App Services, funciones, servicios distintos) y/o `09-release-management.md` ya declaró
  versionado independiente por paquete, un pipeline combinado normalmente está en tensión con
  esas decisiones (acopla velocidad y blast radius de unidades que ya se trataron como
  independientes en el resto de la sesión) — señálaselo al arquitecto en vez de generarlo en
  silencio. Registra la respuesta como `decisions.pipeline_topology` (`single` /
  `per_component`).
- Si hay más de un pipeline (`per_component`) o el proyecto ya tiene otros pipelines en una
  carpeta dedicada (ej. `infra/pipelines/` para Terraform): ¿dónde viven los archivos de
  definición de cada pipeline? La convención de la plataforma sugiere un default (Azure
  DevOps/GitHub Actions: `azure-pipelines.yml`/`.github/workflows/*.yml` en la raíz para un solo
  pipeline), pero con más de un pipeline de aplicación o con otra carpeta de pipelines ya en uso,
  agruparlos todos en una carpeta dedicada (ej. `pipelines/`) suele ser más descubrible que
  repartirlos entre la raíz y subcarpetas según el tipo. Documenta la ruta elegida explícitamente
  — `vulcano-bob` la necesita para saber dónde generar cada archivo, no la infiere.
- Si hay E2E que ejercita más de una unidad desplegable a la vez (ej. Playwright contra
  frontend+backend juntos): ¿en qué pipeline vive y qué cambio deja de disparar esa validación
  automáticamente cuando se separan los pipelines? Documenta el trade-off explícito en vez de
  asumir que separar pipelines no tiene costo de cobertura cruzada.

**Preguntas — Despliegue Continuo:**
- ¿Qué estrategia de despliegue se usa por ambiente (rolling, blue-green, canary)? ¿Es la misma
  para todos los ambientes o cambia (ej. rolling en dev, canary en producción)? Registra la
  respuesta como `decisions.deployment_strategy`.
- Si la estrategia es canary o blue-green: ¿qué % de tráfico inicial recibe la versión nueva, con
  qué métrica y ventana se analiza automáticamente (ej. tasa de error p95 durante 10 minutos), y
  qué condición dispara abort/rollback automático vs. cuál requiere intervención manual? No
  propongas análisis automático a un equipo Básico (ver `orden-y-dependencias.md`, "Progresión
  por madurez") — para ese caso, documenta el bake time y el checklist manual de verificación.
- ¿El despliegue lo ejecuta el propio pipeline (push) o un controlador externo que reconcilia
  contra un repositorio de manifiestos (GitOps, ej. ArgoCD/Flux)? Pregunta explícitamente cuando
  el target de despliegue sea Kubernetes/contenedores orquestados — en ese caso GitOps suele ser
  el patrón más maduro. Registra la respuesta como `decisions.deployment_model`.
- ¿Qué tipo de aprobación tiene cada ambiente (automática tras pasar el anterior, manual con
  aprobador nombrado)?
- ¿El despliegue a producción requiere aprobación manual o es automático tras pasar staging?
- **Gestión de artefactos:** ¿dónde se publican (registry, Artifactory, GitHub Packages)? ¿cuál
  es la política de retención? ¿cómo se nombran/versionan?
- ¿Por qué canal se notifican el resultado del pipeline y las promociones entre ambientes (Slack,
  Teams, email, ninguno todavía)? Registra la respuesta como `decisions.notification_channel`; si
  ya se resolvió en `10-incident-management.md` para alertas de severidad, puedes reutilizar el
  mismo canal en vez de preguntar de nuevo.

**Nota de generación:** incluye la sección verificable de inspección/deuda y un bloque de
**pseudocódigo YAML** (estructura de etapas, sin implementación final ni comandos reales) tanto
para CI como para CD — ver `references/plantillas-archivos.md`.

### continuous-testing.md

**Hereda de:** `resources/qa/` si el skill `ranger` ya generó contenido ahí (planes de prueba en
`resources/qa/plans/`, runbooks en `resources/qa/runbooks/`) — en ese caso, **este archivo
resume y referencia esa estrategia real, no inventa una nueva**. `06-ci-cd.md` (en qué etapa corre
cada tipo de prueba).

**Preguntas (solo si `resources/qa/` no existe o no cubre esto):**
- ¿Qué niveles de la pirámide de pruebas aplican (unitarias, integración, E2E, carga,
  seguridad) y qué % de cobertura se espera en cada uno?
- ¿Qué herramienta se usa por tipo de prueba (Jest/JUnit para unitarias, Playwright/Selenium
  para E2E, k6/JMeter para carga)?
- ¿En qué etapa del pipeline corre cada tipo (algunas en cada PR, otras solo antes de producción
  por su duración)?
- ¿Cuál es el criterio de cobertura mínima por capa (dominio, aplicación, integración)?
- ¿Cómo se gestionan los datos de prueba por ambiente (fixtures, seeds, anonimización de datos
  productivos)?

### release-management.md

**Hereda de:** `06-ci-cd.md`, `05-environments.md`.

**Preguntas — cadencia y criterios:**
- ¿Cuál es la cadencia de releases (continua, semanal, por sprint, por demanda del negocio)?
- ¿Qué criterios definen "go" vs. "no-go" para un release a producción?
- ¿Cómo se comunica un release (changelog, notas de versión, canal de aviso)?
- ¿Existe una estrategia de rollback definida, o depende del mecanismo de despliegue (ver
  también `11-disaster-recovery.md`)?
- ¿Se usa un sistema de feature flags para desacoplar el despliegue del release (activar código
  en producción sin exponerlo a usuarios todavía)? Si sí, ¿qué proveedor o mecanismo propio, y
  quién administra los flags (desarrollo, producto)? Registra la respuesta como
  `decisions.feature_flags` — usa `none` si el equipo libera directamente con cada despliegue.

**Preguntas — control de versiones:**
- ¿Versionado semántico (`<major>.<minor>.<patch>`), por fecha (CalVer), o esquema propio para
  el código? Ver el stack ya confirmado en `resources/architecture/stack.md` para indicar dónde
  vive la versión (`package.json`, `.csproj`/`AssemblyInfo.cs`, `pom.xml`, según corresponda).
- ¿La documentación del proyecto tiene su propio control de versiones, separado del código
  (ej. historial nativo de SharePoint, o versionado manual con changelog)? Si vive en el mismo
  repositorio de código, no dupliques la pregunta — ya se resolvió en `02-repository-management.md`.
- ¿Se requiere aprobación antes de que un cambio de documentación quede visible al equipo, o
  basta con el historial automático?

### environments.md (devops-strategy)

**Hereda de:** proveedor de nube y servicios de `resources/architecture/`.

**Preguntas:**
- ¿Cuántos ambientes existen y con qué nombre (dev, qa, staging, prod, u otros)?
- ¿Cuál es el propósito específico de cada uno (ej. "qa" es para pruebas manuales,
  "staging" espeja producción exactamente)?
- ¿Cómo se promueve un cambio de un ambiente al siguiente (automático, manual, con gate de
  aprobación)? Registra la tabla de ambientes en ese mismo orden de promoción.
- ¿Todos los ambientes tienen el mismo nivel de recursos/escala, o los no productivos están
  reducidos?
- ¿Hay ambientes efímeros (por PR, por feature branch)?

### security.md (devops-strategy)

**Hereda de:** `19.1-Modelo-de-Amenazas-y-Requisitos-de-Seguridad_*` y sus `SEC-xxx`,
`14.00`/`14.xx` para exposición y controles de aplicación, requisitos de cumplimiento ya
relevados por `archi`, y `08-secrets-management.md` (IaC) si existe. Aplica
`contrato-handoff-archi.md`: no re-preguntes amenazas, alcance ni criterios arquitectónicos;
pregunta solo cómo operacionalizarlos.

Antes de preguntar, muestra los `SEC-xxx` aplicables y cuáles aún no tienen herramienta,
stage, evidencia, frecuencia, owner o disposición. Las preguntas siguientes se limitan a esos
vacíos y a controles DevSecOps sin requisito Archi explícito.

**Preguntas — controles por etapa del SDLC:**
- ¿Qué análisis de seguridad corren en el pipeline y en qué etapa cada uno: SAST, DAST,
  SCA/dependencias, escaneo de imágenes de contenedor, **IAST** (si aplica al stack)?
- Para cada control: ¿qué severidad mínima bloquea el pipeline vs. cuál solo genera advertencia?
- ¿Qué repositorios y ramas cubre el secret scanning? ¿Qué acción se toma al detectar un
  secreto expuesto (bloquear el push, alertar, rotar automáticamente)?
- ¿Qué umbral de vulnerabilidad en librerías de terceros bloquea el pipeline (ej. "cualquier
  CVE crítico o alto sin parche disponible")?
- ¿Se genera SBOM? ¿Cómo se firman artefactos/imágenes y se produce/verifica provenance antes
  del despliegue? ¿Actions/plugins y dependencias quedan fijados a versiones inmutables?
- ¿Qué policy as code gobierna IaC, imágenes o despliegues y cómo se aprueban excepciones?

**Preguntas — remediación y gobierno:**
- ¿Cuál es el SLA de remediación por severidad (ej. crítico: 24h, alto: 7 días, medio: 30 días,
  bajo: próximo sprint)?
- ¿Cómo se gestionan los accesos a los ambientes (RBAC, SSO, acceso just-in-time)?
- ¿Existen auditorías o certificaciones de cumplimiento que el pipeline deba soportar (evidencia,
  logs de aprobación)? Si `archi` ya documentó un requisito de cumplimiento (SOC2, ISO 27001,
  PCI-DSS u otro), agrega aquí los controles adicionales que ese estándar exige — no lo
  re-preguntes, solo tradúcelo a controles concretos del pipeline.
- ¿Quién es responsable de revisar hallazgos de seguridad (equipo de AppSec, el mismo equipo
  de desarrollo)?

### disaster-recovery.md

**Hereda de:** RTO/RPO y SLA de disponibilidad si ya están en un RNF de `resources/architecture/`
— no los inventes si ya están definidos ahí, solo tradúcelos a plan operativo.

**Preguntas:**
- Si no hay RTO/RPO ya definidos: ¿cuánto tiempo de inactividad es tolerable (RTO) y cuánta
  pérdida de datos es aceptable (RPO)?
- ¿Existe estrategia de backup (frecuencia, retención, dónde se almacena, cifrado)?
- ¿Hay un plan de failover a otra región/zona, o el sistema acepta downtime total ante un
  desastre mayor?
- ¿Se han hecho simulacros de recuperación (DR drills)? ¿con qué frecuencia?
- ¿Quién decide activar el plan de continuidad y cómo se comunica durante un desastre?
- ¿Cuándo fue la última restauración real y el último tabletop/failover? ¿Qué evidencia demostró
  RTO/RPO y quién es owner de las acciones pendientes?

---

## infrastructure-as-code/

### architecture.md (IaC)

**Hereda de:** proveedor de nube de `resources/architecture/`.

**Preguntas:**
- ¿Terraform, Pulumi, CloudFormation, Bicep, o una combinación?
- ¿Por qué esa herramienta (expertise del equipo, estándar corporativo, soporte multi-nube)?
- ¿Todo el despliegue vive como código, o hay recursos creados manualmente que quedan fuera
  (y por qué)?
- ¿Hay un repositorio dedicado a IaC, o vive junto al código de aplicación (monorepo)?
- ¿Qué política fija versiones de CLI/providers/módulos y conserva lockfiles? Si se evalúan
  Terraform/OpenTofu, ¿qué requisitos de compatibilidad, licencia y soporte deciden entre ellos?
- ¿Cómo se adopta infraestructura existente, se protegen destroys y se retiran recursos?
- ¿Hay policy as code sobre el `plan` de IaC (ej. OPA/Conftest) que bloquee antes de aplicar, o
  la gobernanza queda en revisión manual del PR? Si hay motor, ¿cuál y quién administra las
  políticas? Registra la respuesta como `decisions.policy_engine` (`opa` / `conftest` / `none`).
  No lo asumas desde la madurez declarada en la Fase 0.4: un equipo Avanzado puede seguir sin
  policy as code si el riesgo del proyecto no lo justifica todavía.

### terraform-structure.md

**Hereda de:** `01-architecture.md` (herramienta ya confirmada — Terraform, Pulumi, CloudFormation,
Bicep u otra; no vuelvas a preguntar cuál es, solo cómo se organiza el código de esa herramienta).

**Señal en el repo:** si ya hay carpetas `.tf` (u otro código de IaC), documenta la estructura
real encontrada en vez de preguntarla.

**Preguntas:**
- ¿Cómo se organizan las carpetas (por ambiente, por capa/servicio, por ambos)?
- ¿Cómo se separan los ambientes en el código de la herramienta confirmada (workspaces en
  Terraform, stacks en Pulumi, stack sets en CloudFormation, carpetas/backends separados)?
- ¿Hay una carpeta de módulos/componentes propia del proyecto además de los de terceros?
- ¿Cómo se referencian módulos/componentes externos (registro público, git tag, path local)?
- ¿Qué constraint de Terraform y de cada provider queda aprobado, sin asumir automáticamente
  la versión más reciente?
- ¿Los módulos siguen el estándar interno o deben cumplir Azure Verified Modules (AVM)?
- ¿La ejecución ocurre en Azure DevOps o HCP Terraform, y el Terraform MCP puede consultar el
  Registry en modo `read_only` o debe permanecer deshabilitado?
- ¿La estrategia exige pruebas `plan` con providers mockeados solamente, o también pruebas de
  integración autorizadas en pipeline? ¿Se adoptará infraestructura existente con moved/import?

### modules.md

**Hereda de:** `04-terraform-structure.md` (dónde viven los módulos).

**Preguntas:**
- ¿Qué módulos reutilizables existen o se planean (red, base de datos, cómputo, IAM, etc.)?
- Para cada módulo: ¿qué inputs recibe y qué outputs expone?
- ¿Algún módulo consume outputs de otro módulo del catálogo que un input no delata por nombre
  (ej. un rename)? Decláralo explícito en `Depende de` — `vulcano-bob` no adivina dependencias que
  no estén en el nombre del input o en esta anotación.
- ¿Los módulos son propios del proyecto, de un registro interno corporativo, o del registro
  público de Terraform?
- ¿Hay convención de versionado de módulos (semver, tags de git)?
- ¿Cómo se prueban, publican, deprecian y soportan los módulos? ¿Qué compatibilidad garantizan?

### state-management.md

**Hereda de:** `04-terraform-structure.md`, `02-environments.md` (IaC).

**Preguntas:**
- ¿Dónde vive el estado remoto (S3+DynamoDB, Azure Storage+lease, GCS, Terraform Cloud)?
- ¿Un state file por ambiente, o uno compartido con workspaces?
- ¿Cómo se maneja el locking para evitar aplicaciones concurrentes?
- ¿Quién tiene permiso de ejecutar `apply` contra el estado de producción?
- ¿Hay backup/versionado del state file en sí?
- **Política de no-drift:** ¿cómo se detecta si el estado real de la infraestructura se desvió
  de lo declarado en código (plan periódico programado, solo se detecta en el próximo `apply`)?
  ¿Qué se hace cuando se detecta drift — se corrige el código para reflejar la realidad, o se
  fuerza el estado real a coincidir con lo declarado?
- ¿Cómo se bootstrappea y recupera el backend de estado? ¿Hay restore test y acceso break-glass?
- ¿Cuál es el flujo format/validate/lint/security/test/plan/cost/policy/apply y cómo se evita
  aplicar un plan obsoleto?

### naming-conventions.md

**Preguntas:**
- ¿Existe ya un estándar de nombres para recursos de nube (patrón, ej.
  `<org>-<proyecto>-<ambiente>-<recurso>`)?
- ¿Qué tags obligatorios debe llevar todo recurso (costo/centro de costo, ambiente, dueño,
  proyecto)?
- ¿Hay restricciones de longitud o caracteres impuestas por el proveedor de nube que condicionen
  la convención?
- ¿Cómo se nombran los recursos de red, cómputo y datos de forma diferenciada?

### environments.md (IaC)

**Hereda de:** `devops-strategy/05-environments.md` — **no vuelvas a preguntar los nombres ni el
propósito de cada ambiente**, solo cómo se materializan en código.

**Preguntas:**
- ¿Cada ambiente es un workspace/stack (según la herramienta de IaC confirmada), una carpeta
  separada, o un state file distinto?
- ¿Qué variables cambian entre ambientes (tamaño de instancia, réplicas, SKU) y cómo se
  parametrizan (`.tfvars` por ambiente, variables de CI/CD)?
- ¿Los ambientes no productivos comparten alguna infraestructura (ej. misma VNet) o están
  totalmente aislados?

### networking.md

**Hereda de:** `02-environments.md` (IaC), lista de servicios de `resources/architecture/`.

**Preguntas:**
- ¿Topología de red (VNet/VPC único, uno por ambiente, hub-spoke)?
- ¿Segmentación en subnets (por capa: web/app/datos, o por servicio)?
- ¿Reglas de entrada/salida por defecto (deny-all con excepciones explícitas, o más permisivo)?
- ¿Hay conectividad híbrida (VPN site-to-site, ExpressRoute/Direct Connect) con on-premise u
  otro proveedor?
- ¿Algún servicio necesita exposición pública directa, o todo pasa por un API Gateway/Load
  Balancer/WAF?

### secrets-management.md

**Hereda de:** `02-environments.md` (IaC); debe alinearse con `devops-strategy/08-security.md`. Este
archivo cubre las 3 vías de **Gestión de Configuración**: configuración no sensible,
configuración sensible, y secretos — no solo secretos en sentido estricto, a pesar del nombre
del archivo (convención heredada de la estructura original).

**Preguntas — clasificación y herramienta por tipo:**
- ¿Qué va en variables de entorno/configuración no sensible (feature flags, URLs de servicios,
  timeouts), qué va en un gestor de configuración sensible, y qué va estrictamente en un
  gestor de secretos? Pide 2-3 ejemplos concretos del proyecto para cada categoría.
- ¿Qué herramienta gestiona secretos (Key Vault, AWS Secrets Manager, HashiCorp Vault, SOPS)?
  Registra la respuesta como `decisions.secrets_manager` en el manifiesto (`none` solo si el
  proyecto todavía no separa secretos de configuración no sensible — deja explícito el riesgo).
- ¿Qué herramienta gestiona configuración no sensible/sensible si es distinta a la de secretos
  (App Configuration, Consul, ConfigMaps de Kubernetes, archivos `.env` versionados solo para
  no-sensible)?

**Preguntas — runtime y ciclo de vida:**
- ¿Cómo llegan los secretos al pipeline/aplicación en runtime (inyección por variable de
  entorno, montaje de volumen, SDK en código)?
- ¿Cómo difiere la configuración entre Development/QA/Staging/Production (mismo mecanismo,
  valores distintos; o mecanismos distintos por ambiente)?
- ¿Hay rotación automática de secretos? ¿con qué frecuencia y quién es responsable por tipo de
  secreto (ej. credenciales de DB cada 90 días — equipo de plataforma)?
- ¿Quién tiene permiso de leer/escribir secretos de producción?
- ¿Los secretos de un ambiente son accesibles desde otro (¿aislamiento total dev/prod)?

---

## observability/

### monitoring.md

**Hereda de:** lista de servicios/contenedores de `resources/architecture/` (sección de
Contenedores C4 nivel 2), nivel de madurez DevOps de la Fase 0.4, `06-ci-cd.md` y
`09-release-management.md` (para calcular lead time y frecuencia de despliegue reales).

**Preguntas — métricas técnicas:**
- ¿Qué herramienta de monitoreo (Prometheus+Grafana, Datadog, New Relic, CloudWatch, Azure
  Monitor)?
- Para cada servicio crítico: ¿qué métricas clave se capturan (latencia, tasa de error,
  throughput, saturación de recursos)?
- ¿Hay monitoreo de infraestructura (CPU, memoria, disco) además del de aplicación?
- ¿Con qué frecuencia se recolectan/scrapean métricas?
- ¿Existe catálogo de servicios con owner/criticidad/dependencias? ¿Cómo se monitorea la pérdida
  de telemetría en collectors/exporters y cuánto cuesta observar cada servicio?
- ¿Aplican RUM, sintéticos o continuous profiling? ¿Qué límites de cardinalidad y volumen rigen?

**Preguntas — métricas DORA:**
- ¿Para qué aplicación o servicio se medirán? No agregues servicios con contextos distintos en
  una sola cifra. Para deployment frequency, change lead time, failed deployment recovery time,
  change fail rate y deployment rework rate: ¿cuál es la definición operacional, fórmula,
  población, fuente, ventana y calidad del dato? Si no se miden, registra "baseline desconocida"
  y el plan de instrumentación; no inventes una medición desde el nivel de madurez.
- ¿Qué meta es realista a 6 y 12 meses? Si se usan benchmarks externos, ¿qué fuente y año se
  adoptan? No hardcodees categorías históricas.
- ¿Qué equipo cross-functional es accountable del conjunto de las cinco métricas y qué roles
  participan? Evita asignar cada métrica a un silo; desarrollo, QA, plataforma, operaciones y
  release comparten el resultado aunque haya un accountable explícito.
- ¿Las cinco métricas se van a recolectar manualmente (planilla, revisión periódica) o mediante
  un mecanismo automatizado que lea eventos reales del pipeline/plataforma (runs, deployments,
  incidentes)? Registra la respuesta como `decisions.dora_collection_method`. No asumas
  `automated` solo porque el equipo es de madurez Avanzada — sin un mecanismo real confirmado, el
  valor correcto sigue siendo `manual`.

### logging.md

**Preguntas:**
- ¿Qué herramienta centraliza logs (ELK/OpenSearch, Loki, CloudWatch Logs, Azure Log
  Analytics, Datadog Logs)?
- ¿Formato de log estándar (JSON estructurado, texto plano con convención)?
- ¿Qué niveles de log se usan y cuál es el criterio para cada uno (debug/info/warn/error)?
- ¿Cómo se correlaciona un log con una request específica (correlation ID, trace ID)?
- ¿Política de retención de logs (por cuánto tiempo, por qué ese plazo — costo, cumplimiento)?
- ¿Qué campos se prohíben o redactan por contener PII, secretos o datos regulados? ¿Qué límites
  de cardinalidad/volumen y presupuesto de ingestión aplican?

### tracing.md

**Nota:** si el sistema es un monolito sin llamadas distribuidas relevantes, confirma con el
arquitecto si vale la pena este archivo ahora o si se pospone — no rellenes con contenido
genérico si no aporta valor real todavía.

**Preguntas:**
- ¿Se usa OpenTelemetry, Jaeger, Zipkin, X-Ray, Application Insights, u otro?
- ¿Cómo se propaga el contexto de traza entre servicios (headers estándar W3C Trace Context,
  propietario)?
- ¿Qué tasa de sampling se aplica (100% en dev, reducido en producción por costo/volumen)?
- ¿Qué operaciones o flujos críticos deben tener trazas siempre garantizadas, sin sampling?

### dashboards.md

**Hereda de:** `01-monitoring.md` (métricas ya definidas) y `04-slis-slos.md` si ya existe.

**Preguntas:**
- ¿Qué dashboards existen o se necesitan (uno por servicio, uno ejecutivo, uno de
  infraestructura, uno específico de on-call)?
- ¿Quién es la audiencia de cada dashboard (equipo de desarrollo, SRE/on-call, negocio)?
- ¿Hay un dashboard "single pane of glass" para incidentes, o se navega entre varios?

### alerting.md

**Hereda de:** `04-slis-slos.md` y `01-monitoring.md`. Las páginas por impacto usan preferentemente
síntomas/SLO; alertas preventivas pueden originarse en capacidad, cuotas, certificados, backups,
seguridad o salud de telemetría si son accionables.

**Preguntas:**
- ¿Qué condiciones disparan una alerta (umbral fijo, tasa de error, burn rate de error budget)?
- ¿Qué niveles de severidad existen y qué acción dispara cada uno (ticket, notificación,
  llamada de on-call)?
- ¿Por qué canal se notifica cada severidad (Slack, email, PagerDuty/Opsgenie, SMS)?
- ¿Existe rotación de on-call? ¿Cómo está organizada (equipos, horarios, escalamiento si no
  responde el primero)?
- ¿Cómo se evita fatiga de alertas (agrupación, deduplicación, umbrales ajustados)?
- Para cada alerta: ¿cuál es su owner, acción esperada, ventana, prueba y justificación? ¿Las de
  SLO usan burn rate multi-window cuando aplica?
- ¿Qué ID estable `ALT-NNN` identifica cada alerta para enlazarla sin ambigüedad con su runbook?

### slis-slos.md

**Hereda de:** RNF de disponibilidad/rendimiento de `resources/architecture/` si ya existen —
tradúcelos a SLIs/SLOs concretos en vez de inventar nuevos objetivos que los contradigan.

**Preguntas:**
- ¿Cuáles son los servicios/flujos de negocio críticos que necesitan un SLO explícito?
- Para cada uno: ¿qué SLI lo mide (disponibilidad, latencia p95/p99, tasa de éxito)?
- ¿Qué objetivo numérico tiene cada SLO (ej. 99.9% de disponibilidad mensual)?
- ¿Sobre qué ventana de tiempo se mide (30 días rodantes, mes calendario)?
- ¿Existe la noción de error budget y qué pasa cuando se agota (freeze de features, prioridad
  a estabilidad)?

### runbooks.md

**Hereda de:** cada alerta de severidad alta/crítica definida en `06-alerting.md` — debe existir
un runbook por cada una.

**Preguntas:**
- Para cada alerta crítica: ¿cuáles son los primeros pasos de diagnóstico (qué dashboard
  revisar, qué logs consultar)?
- ¿Cuáles son las acciones de mitigación conocidas (reiniciar servicio, escalar réplicas,
  rollback, activar failover)?
- ¿Cuándo escalar a otro equipo/persona si la mitigación inicial no resuelve?
- ¿Cómo se documenta el incidente después (postmortem, plantilla, plazo para publicarlo)?
- ¿Quién es owner del runbook, cuándo se probó por última vez, qué permisos/prerrequisitos exige
  y qué impacto puede causar cada mitigación?

---

## resources/ (cierre de sesión, fuera de las 3 carpetas)

### 02-madurez-devsecops.md

**No es parte del loop archivo-por-archivo de la Fase 2** — se genera una sola vez al cierre
(Fase 3, paso 2), derivado de los 26 archivos ya generados. Ver
`references/estandares-madurez.md` para el procedimiento completo de búsqueda de estándares y
construcción del checklist.

**La única pregunta nueva (y solo si el Paso 1 de `estandares-madurez.md` no encontró nada):**
- ¿Quieres que evalúe la madurez contra algún estándar formal específico (ISO 27001, SOC 2,
  PCI-DSS, NIST SSDF, OWASP DSOMM, CIS Benchmarks, CMMI), o prefieres el framework interno de
  madurez (Básico/Intermedio/Avanzado + DORA) usado en el resto de la sesión?

Si no hay respuesta, procede con el framework interno y decláralo explícitamente en el
documento — no bloquees el cierre de la sesión por esto.
