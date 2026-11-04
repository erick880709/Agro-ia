# Estándares operativos actuales

**Última revisión:** 2026-07-14. Antes de afirmar que una versión o benchmark sigue vigente,
verificar la fuente primaria.

## Fuentes normativas y de referencia

- [DORA software delivery performance metrics](https://dora.dev/guides/dora-metrics/)
- [SLSA specification](https://slsa.dev/spec/v1.2/)
- [NIST SP 800-218 SSDF](https://csrc.nist.gov/pubs/sp/800/218/final)
- [OpenTelemetry Semantic Conventions](https://opentelemetry.io/docs/specs/semconv/)
- [Google SRE Workbook](https://sre.google/workbook/table-of-contents/)

Usar la fuente que corresponda al control; no presentar esta síntesis como texto normativo ni
como certificación.

## Uso

Consultar solo las secciones pertinentes al archivo en curso. Estas son capacidades a evaluar,
no una lista de productos obligatorios. Toda omisión debe responder al contexto, riesgo y
madurez del proyecto.

## CI/CD y cadena de suministro

- Construir una vez y promover el mismo artefacto inmutable por digest.
- Definir concurrencia, cancelación, timeout, retry y cache; medir queue time, duración, éxito y
  flaky tests.
- Aplicar permisos mínimos, tokens de corta vida y OIDC/workload identity; documentar aislamiento
  y parcheo de runners self-hosted.
- Fijar actions/plugins y dependencias por versión inmutable; gobernar excepciones.
- Generar SBOM, vulnerability scan, firma y provenance/attestation; verificar antes del deploy.
- Separar CI, delivery y deployment. Definir approvals, segregation of duties, break-glass,
  rollback y roll-forward.
- Usar policy as code cuando el riesgo lo justifique. SAST, SCA, DAST, IAST y escaneos no son
  automáticamente bloqueantes: decidir por señal, confiabilidad y severidad.
- Evaluar despliegue progresivo (canary/blue-green) con análisis automático por métrica y abort/
  rollback disparado por esa señal, no solo por fallo del health check; no proponerlo de entrada a
  un equipo Básico (ver `orden-y-dependencias.md`, "Progresión por madurez").
- Evaluar el modelo de despliegue como decisión explícita: pipeline push-based (el CI/CD ejecuta
  el deploy) frente a GitOps (un controlador reconcilia contra un repositorio de manifiestos) —
  GitOps suele ser el patrón más maduro cuando el target es Kubernetes/contenedores orquestados,
  pero no es superior por defecto en otros targets.
- Evaluar feature flags como mecanismo para desacoplar deploy de release cuando la cadencia o el
  riesgo del negocio lo justifique.

## Inspección continua y deuda técnica

- Mantener la selección neutral respecto al producto: fijar primero capacidades, fuentes,
  lenguaje/stack, costo y operación; confirmar la herramienta después.
- Definir cada métrica con unidad, alcance, fuente, baseline, umbral, consecuencia y owner.
  Evaluar cobertura de código nuevo, duplicación, complejidad, mantenibilidad/confiabilidad e
  issues bloqueantes; declarar con justificación lo que no aplique.
- Preferir gates diferenciales sobre código nuevo y un ratchet contra la baseline. No paralizar
  el delivery por deuda histórica ni permitir que el legado justifique deuda nueva.
- Publicar feedback accionable en el PR y separar calidad, pruebas y seguridad aunque compartan
  una herramienta o etapa del pipeline.
- Registrar deuda aceptada con impacto, componente, owner, prioridad/SLA, criterio de salida y
  revisión periódica; no usar un único porcentaje o rating como sustituto de la política.
- Tratar falsos positivos y excepciones como temporales: ID, alcance, riesgo aceptado, aprobador,
  vencimiento/revalidación y control compensatorio.

## Infraestructura como código

- Evaluar Terraform, OpenTofu y alternativas sin asumir equivalencia ni migración automática.
- Fijar versiones de CLI/providers/modules y conservar lockfiles.
- Flujo mínimo: format, validate, lint, security, test, plan, cost, policy, approval y apply.
- Separar plan/apply, proteger planes contra obsolescencia y limitar apply de producción.
- Cubrir bootstrap del backend, cifrado, locking, backup, restauración y acceso break-glass.
- Definir import/adopción, refactors/moves, deprecación, destroy protection y recursos huérfanos.
- Probar módulos; publicar versiones inmutables; declarar compatibilidad y ciclo de soporte.
- Detectar drift con owner, frecuencia, SLA y manejo de excepciones temporales.
- Incorporar estimación de costo/FinOps, budgets/tags y control de recursos efímeros.

## Observabilidad

- Mantener catálogo de servicios con owner, criticidad, dependencias, dashboards, SLOs y runbooks.
- Aplicar RED a servicios y USE a recursos, además de señales de negocio relevantes.
- Definir convenciones semánticas, versión del esquema y propagación W3C Trace Context.
- Controlar cardinalidad, volumen, sampling, retención, costo y redacción de PII/secretos.
- Evaluar métricas, logs, traces, perfiles, RUM y sintéticos según el sistema.
- Monitorear collectors, exporters, colas y pérdida de telemetría; observabilidad también debe ser
  observable.
- Las páginas por impacto usan preferentemente síntomas, SLO y multi-window/multi-burn-rate.
  Alertas preventivas son válidas para límites duros, capacidad, cuotas, certificados, backups,
  seguridad y salud de telemetría si son accionables.
- Cada alerta define owner, acción, canal, deduplicación, ventana, prueba y runbook cuando requiere
  intervención inmediata.

## DORA

Usar las cinco métricas vigentes: deployment frequency, change lead time, failed deployment
recovery time, change fail rate y deployment rework rate. Medirlas por aplicación o servicio;
no agregar contextos dispares. Para cada una registrar definición operacional, fórmula,
población, fuente, ventana y calidad del dato. Asignar accountability al equipo cross-functional
y registrar participantes, sin crear ownership aislado por métrica. No inferir valores medidos
desde la madurez; si no hay dato, registrar baseline desconocida y plan de instrumentación. No
hardcodear bandas Elite/High/Medium/Low: citar el benchmark y año que el proyecto decida usar.

## Incidentes y recuperación

- Definir Incident Commander, operaciones, comunicaciones, enlace técnico y scribe según tamaño.
- Separar canal técnico, comunicación a stakeholders y status page.
- Registrar timeline, decisiones, mitigación, criterio de cierre y handoff.
- Ejecutar postmortem sin culpa; cada acción tiene owner, fecha, prioridad y seguimiento.
- Definir backups con frecuencia, retención, cifrado, inmutabilidad y prueba de restauración.
- Incluso en madurez básica ejecutar al menos tabletop y restore test proporcional al riesgo; no
  declarar un backup confiable solo porque el job terminó correctamente.
- Validar RTO/RPO mediante ejercicios y registrar resultados, gaps y siguiente prueba.
