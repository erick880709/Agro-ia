# Señales de modernización por pilar

## Índice

- [Repositorio, tareas e incidentes](#gestión-de-repositorio-tareas-e-incidentes)
- [DevOps y CI/CD](#devops--ci-cd)
- [Infraestructura como Código](#infraestructura-como-código)
- [Observabilidad](#observabilidad)
- [Uso en la Fase 0.3](#cómo-usar-este-checklist-en-la-fase-03)

Checklist de heurísticas para la Fase 0.3 del `SKILL.md`. No es una lista para marcar
mecánicamente contra todos los proyectos — es el inventario de qué mirar cuando ya hay algo
implementado, para decidir si vale la pena ofrecer un TO-BE. Aplica solo lo relevante al
contexto y criticidad real del proyecto; un hallazgo que no tiene impacto de negocio real no es
un hallazgo, es ruido.

Para cada señal detectada, no te quedes en "esto está desactualizado" — arma el trío
**hallazgo → riesgo concreto si no se atiende → propuesta**. Un hallazgo sin riesgo concreto no
justifica un TO-BE.

---

## Gestión de Repositorio, Tareas e Incidentes

- **Documentación y código en el mismo repositorio sin separación clara, cuando el equipo crece
  más allá de unas pocas personas.** Riesgo: ruido en el historial de commits de código,
  dificulta permisos diferenciados (no todo el equipo de negocio necesita acceso al código).
- **Sin convención de nombres para ítems del tablero, o sin vínculo entre el ID del ítem y el
  nombre de la rama/commit.** Riesgo: imposible trazar qué commit resolvió qué tarea sin buscar
  manualmente.
- **Sin Definition of Ready ni Definition of Done documentadas** (cada persona interpreta
  "listo" distinto). Riesgo: ítems que entran a un sprint sin estar realmente listos, o que se
  cierran sin cumplir criterios reales — genera retrabajo no visible en el tablero.
- **Sin clasificación de severidad para incidentes/bugs, o clasificación que no tiene SLA de
  respuesta asociado.** Riesgo: incidentes críticos compiten por atención con bugs cosméticos,
  sin criterio objetivo de priorización.
- **Sin plantilla de reporte de bug** (cada reporte trae información distinta). Riesgo: tiempo
  perdido pidiendo información faltante antes de poder diagnosticar.

## DevOps / CI-CD

- **Versión de la herramienta de CI/CD o de sus runners/agentes desactualizada o sin soporte.**
  Riesgo: vulnerabilidades sin parchar, incompatibilidad futura con actions/plugins.
- **Sin protección de rama** (cualquiera puede hacer push directo a `main`/producción).
  Riesgo: cambios sin revisión llegan a producción, imposible auditar quién aprobó qué.
- **Pipeline sin quality gates de seguridad** (sin SAST/DAST/SCA, sin escaneo de imágenes).
  Riesgo: vulnerabilidades conocidas llegan a producción sin detección automática.
- **Sin inspección continua de calidad, o con un gate sin métrica, baseline ni consecuencia.**
  Riesgo: el resultado no es reproducible y la calidad puede degradarse sin una señal objetiva.
- **El gate bloquea por toda la deuda histórica en vez de evaluar código nuevo con baseline y
  ratchet.** Riesgo: el equipo termina desactivando el control para poder entregar, perdiendo
  también la protección frente a deuda nueva.
- **Deuda técnica y excepciones sin owner, prioridad/SLA o vencimiento.** Riesgo: los hallazgos
  aceptados se vuelven permanentes y el riesgo acumulado queda invisible.
- **Todas las aprobaciones son manuales, incluso para cambios triviales** (cuello de botella) —
  o **ninguna aprobación existe, ni para producción** (riesgo de cambios no controlados). Ambos
  extremos son señales, no solo la ausencia total.
- **Sin ambiente de staging que espeje producción** (mismo tamaño, misma configuración).
  Riesgo: bugs que solo aparecen en producción por diferencias de ambiente.
- **Sin estrategia de rollback automatizada** — el rollback depende de que alguien recuerde los
  pasos manuales bajo presión. Riesgo: tiempo de recuperación (MTTR) alto ante un mal deploy.
- **RTO/RPO no definidos, o definidos pero nunca probados con un simulacro real.**
  Riesgo: la organización descubre en un incidente real que el plan no funcionaba como se creía.
- **Builds lentos sin cache** (build completo desde cero en cada corrida). Riesgo: no es un
  riesgo de negocio directo, pero degrada la velocidad de entrega — inclúyelo solo si el
  arquitecto menciona que es un dolor real, no como hallazgo automático.
- **Sin ninguna métrica DORA medida, ni siquiera de forma manual.** Riesgo: no hay forma
  objetiva de saber si los cambios recientes al proceso (nuevo pipeline, nueva estrategia de
  branching) mejoraron o empeoraron la entrega — solo hay percepción subjetiva.
- **Solo pruebas unitarias, sin integración ni E2E en el pipeline** (o al revés: todo E2E, sin
  base de pruebas rápidas). Riesgo en el primer caso: bugs de integración llegan a producción;
  en el segundo: pipeline lento, feedback tardío al desarrollador.
- **Sin criterio de cobertura mínima, o cobertura medida pero no aplicada como gate.**
  Riesgo: la cobertura decae con el tiempo sin que nadie lo note hasta que ya es un problema.
- **Artefactos reconstruidos por ambiente o promovidos por tag mutable.** Riesgo: staging y
  producción no ejecutan el mismo binario auditado; rollback y trazabilidad dejan de ser fiables.
- **Credenciales persistentes y privilegiadas en CI/CD, sin OIDC/workload identity.** Riesgo:
  una filtración del pipeline entrega acceso de larga duración a infraestructura.
- **Sin SBOM, firma/provenance o verificación previa al deploy.** Riesgo: no se puede demostrar
  qué componentes contiene el artefacto ni si fue sustituido después del build autorizado.
- **Actions/plugins/runners sin pinning, aislamiento o mantenimiento.** Riesgo: compromiso de la
  cadena de build o ejecución de código no confiable con acceso a secretos.

## Infraestructura como Código

- **Recursos creados manualmente ("click-ops") mezclados con recursos gestionados por IaC.**
  Riesgo: drift no detectado, el próximo `apply` puede revertir un cambio manual crítico sin
  que nadie lo note.
- **Un solo state file compartido entre todos los ambientes** (en vez de uno por ambiente).
  Riesgo: un cambio pensado para dev puede aplicarse contra producción por error humano.
- **Sin locking del estado remoto.** Riesgo: dos aplicaciones concurrentes corrompen el state.
- **Secretos hardcodeados en el código de IaC o en `.tfvars` versionados en git.**
  Riesgo: exposición de credenciales en el historial de git, imposible de revocar solo con
  rotarlas si el repo ya fue clonado.
- **Sin convención de naming/tags, o convención inconsistente entre recursos.**
  Riesgo: imposible hacer cost allocation por proyecto/ambiente, gobernanza y auditoría manual.
- **Módulos duplicados** (el mismo patrón de recurso copiado y pegado en vez de un módulo
  reutilizable). Riesgo: un fix de seguridad hay que aplicarlo N veces y es fácil olvidar una.
- **Red plana sin segmentación** (todos los recursos en la misma subnet, sin reglas de acceso
  diferenciadas). Riesgo: blast radius amplio — comprometer un componente de bajo riesgo da
  acceso lateral a componentes críticos.
- **Versión de la herramienta de IaC o del proveedor (API version, provider version)
  desactualizada o próxima a EOL.** Riesgo: pérdida de soporte, incompatibilidad con features
  nuevas que el proyecto podría necesitar.
- **Sin ambientes efímeros ni aislamiento real entre dev/qa/prod** (comparten recursos que
  deberían estar separados, ej. misma base de datos). Riesgo: pruebas en dev afectan datos o
  disponibilidad de otro ambiente.
- **Sin política de detección de drift** (nadie verifica si el estado real diverge de lo
  declarado en código). Riesgo: un cambio manual de emergencia queda invisible hasta que un
  `apply` posterior lo revierte sin aviso, en el peor momento posible.
- **Configuración no sensible mezclada con secretos en el mismo mecanismo** (todo en el gestor
  de secretos, o todo en variables de entorno planas sin distinción). Riesgo: sobre-uso costoso
  del gestor de secretos para datos triviales, o exposición de datos sensibles en configuración
  de bajo control de acceso.
- **Versiones de CLI/providers/módulos flotantes o sin lockfile.** Riesgo: un plan cambia sin
  modificación del código y rompe reproducibilidad.
- **Sin pruebas, policy as code, estimación de costo o protección contra destroy.** Riesgo:
  cambios sintácticamente válidos pueden violar controles, disparar costo o borrar recursos.
- **Sin proceso de import/refactor/retiro ni recuperación probada del backend.** Riesgo: la
  adopción y evolución de recursos causa recreaciones, huérfanos o pérdida de capacidad operativa.

## Observabilidad

- **Solo hay logs crudos, sin dashboards ni métricas agregadas.** Riesgo: diagnosticar un
  incidente requiere buscar manualmente en logs bajo presión, sin visibilidad agregada.
- **Sin SLOs definidos para servicios críticos.** Riesgo: no hay forma objetiva de saber si el
  sistema está "suficientemente bien" — las decisiones de priorización (estabilidad vs.
  features) se toman a criterio subjetivo.
- **Alertas basadas en umbrales estáticos que generan fatiga** (falsos positivos frecuentes, el
  equipo empieza a ignorarlas). Riesgo: una alerta real relevante se pierde entre el ruido.
- **Sin tracing distribuido en un sistema con múltiples servicios que se llaman entre sí.**
  Riesgo: debugging a ciegas cuando la latencia o el error está en la cadena de llamadas, no en
  un servicio aislado.
- **Logs sin correlation ID / trace ID.** Riesgo: imposible reconstruir el camino completo de
  una request específica a través de varios servicios.
- **Sin runbooks — cada incidente se resuelve con conocimiento tribal** (solo una persona sabe
  cómo mitigar cierta alerta). Riesgo: MTTR alto cuando esa persona no está disponible; riesgo
  de continuidad si la persona deja el equipo.
- **Retención de logs/métricas no alineada con necesidades reales** (muy corta para auditoría o
  troubleshooting de incidentes intermitentes, o innecesariamente larga generando costo sin uso).
- **Cardinalidad, PII/secretos y volumen sin gobierno.** Riesgo: explosión de costo, degradación
  del backend y exposición de datos sensibles.
- **El pipeline de telemetría no se monitorea.** Riesgo: una caída del collector produce falsa
  sensación de salud precisamente durante un incidente.
- **Sin catálogo de servicios u ownership.** Riesgo: alertas, SLOs y acciones carecen de un
  equipo responsable y aumentan el MTTR.
- **Alertas técnicas de paging sin impacto/acción, o regla absoluta que excluye alertas
  preventivas necesarias.** Riesgo: fatiga por ruido o ausencia de aviso ante certificados,
  backups, cuotas y límites duros.

---

## Cómo usar este checklist en la Fase 0.3

1. Recorre el pilar/archivo que tiene evidencia real (código/config encontrado) contra las
   señales de su sección.
2. Descarta las que no aplican al contexto (ej. "sin multi-región" no es un hallazgo en un
   sistema interno de bajo tráfico sin requisito de alta disponibilidad).
3. Para cada señal que sí aplica, redacta el trío hallazgo/riesgo/propuesta como se indica en
   el `SKILL.md`.
4. Prioriza: si hay más de 5-6 hallazgos para un mismo archivo, preséntalos ordenados por
   riesgo (más alto primero) y dile al arquitecto que puede optar por atender solo los
   principales en el TO-BE, no todos.
