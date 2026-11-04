# Cuestionario de Línea Base para Arquitectura de Software

Este cuestionario se usa después de superar DR-01 según `references/guia-preparacion-dominio.md` y antes de proponer cualquier solución (Caso A) o diseñar el TO-BE (Caso C). Está dividido en bloques temáticos para poder usarlo como checklist: primero se marca qué bloques ya responde la documentación encontrada en `resources/architecture/definitions/`, `resources/design/models/` o `resources/functional/eventstorming/` (o el `.md` de especificaciones del usuario), y solo se pregunta lo que quede sin cubrir. No es un formulario que haya que disparar completo en cada corrida — es el inventario de preguntas posibles.

## 1. Contexto de negocio y alcance

- ¿Cuál es el objetivo del proyecto y qué problema de negocio resuelve?
- ¿Quiénes son los usuarios finales (internos, externos, B2B, B2C)?
- ¿Cuántos usuarios concurrentes/totales se esperan (actual y a 1-3 años)?
- ¿Existe un sistema legacy que se reemplaza o esto es greenfield puro?
- ¿Hay fecha límite (MVP, go-live) que condicione decisiones técnicas?
- ¿Cuál es el presupuesto disponible (licencias, infraestructura, personas)?

## 2. Lenguajes y stack tecnológico

- ¿Hay algún lenguaje/framework ya definido por política corporativa (Java, .NET, Node, Python, Go, etc.)?
- ¿El equipo tiene expertise previo en algún stack específico?
- ¿Se requiere reutilizar librerías, SDKs o componentes internos existentes?
- ¿Front-end: web, móvil nativo, híbrido, o los tres?
- ¿Se necesita soporte multiplataforma (iOS/Android/Web/Desktop)?
- Para web, ¿se espera una SPA modular, aplicaciones independientes por ruta, Microfrontends o aún debe evaluarse? ¿Qué evidencia lo motiva?

## 3. Arquitectura de la solución

- ¿Monolito, monolito modular, microservicios o serverless?
- ¿Se espera que el sistema escale horizontalmente?
- ¿Habrá comunicación síncrona (REST/gRPC) o asíncrona (eventos/colas)?
- ¿Se requiere arquitectura multi-tenant?
- ¿Hay integraciones con sistemas de terceros (ERP, CRM, pasarelas de pago)?
- ¿Se necesita API Gateway / BFF (Backend for Frontend)?
- Si se consideran Microfrontends, ¿qué capacidades UI, shell/compositor, owners y límites de despliegue independiente se esperan? Sigue `references/guia-microfrontends.md` y no asumas uno por microservicio.
- ¿La solución usa IA solo como inferencia puntual/copiloto o incorpora un sistema **agentic** que planifica o itera para alcanzar una meta, selecciona/invoca herramientas, conserva memoria, ejecuta acciones con efecto externo o se comunica con otros agentes?
- Si existe comportamiento agentic, ¿qué nivel de autonomía, herramientas, identidades/permisos, memoria, presupuestos/límites, aprobaciones humanas, condiciones de terminación y mecanismo de detención se esperan?
- ¿La topología es de agente único o multiagente? Si es multiagente, ¿qué agentes, protocolos, mensajes, delegaciones, fronteras de confianza y owners participan?

## 4. Nube e infraestructura

- ¿Cloud pública (AWS, Azure, GCP), on-premise, híbrida o multi-cloud?
- ¿Hay un proveedor ya contratado o preferido por la organización?
- ¿Se usarán contenedores (Docker) y orquestación (Kubernetes, ECS, etc.)?
- ¿Serverless (Lambda, Functions, Cloud Run) es una opción viable?
- ¿Requisitos de alta disponibilidad (SLA %, multi-región, multi-AZ)?
- ¿Estrategia de disaster recovery / RTO / RPO definidos?

## 5. DevOps y ciclo de entrega

- ¿Existe una cadena de CI/CD ya establecida? ¿Cuál herramienta (Jenkins, GitLab CI, GitHub Actions, Azure DevOps, ArgoCD)?
- ¿Infraestructura como código (Terraform, CloudFormation, Pulumi, Bicep)?
- ¿Gestión de configuración/secretos (Vault, AWS Secrets Manager, SOPS)?
- ¿Cuántos ambientes se manejan (dev, QA, staging, prod)?
- ¿Estrategia de branching (GitFlow, trunk-based)?
- ¿Frecuencia de despliegue esperada (continuo, semanal, por release)?
- ¿Los equipos frontend deben desplegar y revertir capacidades de UI sin coordinar una release conjunta? ¿Ya existen pipelines/unidades independientes?

## 6. Base de datos y almacenamiento

- ¿Relacional (PostgreSQL, MySQL, SQL Server, Oracle) o NoSQL (MongoDB, DynamoDB, Cassandra)?
- ¿Volumen de datos esperado y proyección de crecimiento?
- ¿Se requiere caché (Redis, Memcached)?
- ¿Necesidad de búsqueda avanzada (Elasticsearch, OpenSearch)?
- ¿Se maneja Big Data / analítica (Data Warehouse, Data Lake)?
- ¿Requisitos de retención y backup de datos?

Estas respuestas son solo el intake. Para comparar tipos de motor (relacional, documental, clave-valor, columnar, grafo, series de tiempo, búsqueda) con criterios y trade-offs, sigue `references/guia-catalogo-bases-de-datos.md` al generar `16.xx`.

## 7. Seguridad y cumplimiento

- ¿Aplican regulaciones específicas (GDPR, PCI-DSS, HIPAA, ley local de datos personales)?
- ¿Estrategia de autenticación/autorización (OAuth2, SSO, MFA, IAM corporativo)?
- ¿Se requiere cifrado en tránsito y en reposo?
- ¿Hay políticas de seguridad ya definidas por un equipo de InfoSec?
- ¿Hay capacidades o evidencias de seguridad obligatorias (por ejemplo, análisis estático/dinámico, dependencias, pentest o supply chain) que condicionen la arquitectura? Registra la restricción; Vulcano selecciona herramientas, stages, umbrales y SLA del pipeline.
- ¿Qué activos, datos sensibles, superficies expuestas, actores privilegiados o fronteras de confianza requieren un modelo de amenazas y requisitos `SEC-xxx`?

## 8. Calidad y pruebas

- ¿Qué nivel de cobertura de pruebas automatizadas se exige?
- ¿Se usarán pruebas unitarias, integración, end-to-end, carga/performance?
- ¿Herramientas de testing ya adoptadas (JUnit, Jest, Selenium, k6, JMeter)?
- ¿Existe un equipo de QA dedicado o es responsabilidad del equipo de desarrollo?
- Para una UI compuesta, ¿cómo se validarán contratos shell-remote, accesibilidad, journeys E2E, rendimiento y fallos parciales?

## 9. Observabilidad y operación

- ¿Herramientas de monitoreo/logging (Prometheus, Grafana, Datadog, ELK, CloudWatch)?
- ¿Se requiere tracing distribuido (Jaeger, OpenTelemetry)?
- ¿Hay un equipo de soporte/operaciones (SRE, NOC) y cómo se maneja on-call?
- ¿Definición de SLIs/SLOs esperados?

## 10. Equipo y gobernanza

- ¿Tamaño y composición del equipo (frontend, backend, DevOps, QA)?
- ¿Existen dos o más equipos frontend con ownership estable por capacidad y capacidad operativa para releases independientes?
- ¿Metodología de trabajo (Scrum, Kanban, SAFe)?
- ¿Existen estándares de arquitectura corporativos (guías, comités de arquitectura) que deban seguirse?
- ¿Quién es el dueño del producto y quién aprueba decisiones técnicas críticas?

## 11. Restricciones adicionales

- ¿Hay restricciones de licenciamiento (solo open source, prohibición de ciertos proveedores)?
- ¿Requisitos de accesibilidad (WCAG)?
- ¿Requisitos de internacionalización/localización (idiomas, monedas, zonas horarias)?
- ¿Existen dependencias con otros proyectos o equipos en paralelo?

## Cómo usar este cuestionario dentro del skill

1. Después de superar DR-01, coteja cada bloque contra lo que ya encontraste en `resources/architecture/definitions/`, `resources/design/models/`, `resources/functional/eventstorming/` y el `.md` de especificaciones del usuario. Marca cada bloque como **cubierto**, **parcial** o **sin datos** — este mapeo no es para decidir si preguntas o no los bloques 1-4 (esos siempre se preguntan, ver punto 3), sino para saber qué precargar como recomendación en la pregunta.
2. Para los bloques **parciales** o **sin datos**, selecciona solo las preguntas relevantes al proyecto concreto (no todas aplican siempre — por ejemplo, "requisitos de accesibilidad" puede ser irrelevante para una API interna sin UI) y pregúntalas agrupadas por bloque, no una por una en mensajes separados.
3. **Los bloques 1 a 4 (contexto de negocio, stack, arquitectura de la solución, nube) se preguntan siempre**, incluso si quedaron "cubiertos" por la documentación existente — pero como confirmación de bajo costo, no como formulario en blanco: usa `AskUserQuestion` con la respuesta ya encontrada como primera opción, marcada "(Recomendado)", más las alternativas razonables y "Otro". El usuario confirma con un clic o corrige; nunca se salta la pregunta asumiendo en silencio. Motivo: la línea base de un proyecto (equipo, gobernanza, alcance, nube) cambia con el tiempo, y esta sesión ya tuvo casos reales donde un supuesto "obvio" (equipo pequeño, nube fija) resultó estar desactualizado.
4. Para los bloques **5 a 11** (DevOps, datos, seguridad, calidad, observabilidad, equipo/gobernanza, restricciones adicionales), si quedaron "cubiertos" por la documentación existente, no hace falta re-confirmarlos por defecto — pregunta solo lo que quede "parcial" o "sin datos", y documenta el resto como supuesto explícito en `04-Supuestos.md` si el usuario no tiene la respuesta a mano.
5. Genera `01-Linea-Base_<Proyecto>.md` dentro de `resources/architecture/`; las carpetas `definitions/`, `models/` y `eventstorming/` siguen siendo fuentes de entrada. En corridas posteriores, repite la confirmación de bloques 1-4 y vuelve a preguntar de los bloques 5-11 solo los pendientes o de baja confianza.
6. La detección agentic del bloque 3 es obligatoria en A/C y se registra en `01` como `Sí` o `No` con evidencia/decisión y responsable. En B se deriva del código, configuración, prompts, catálogo de herramientas, memoria, protocolos A2A/MCP o trazas observables y se confirma en `10.1`. No clasifiques como agentic una llamada única a un modelo sin planificación, iteración, herramientas, memoria ni acciones autónomas.
