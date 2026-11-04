# Prácticas de implementación experta

Leer al reconciliar código existente, diseñar módulos y cerrar una generación.

## Idempotencia y cambios seguros

- Preferir recursos declarativos y nombres estables.
- No usar timestamps, sufijos aleatorios ni valores dependientes de la máquina salvo que la
  definición los exija.
- Proteger base de datos, state, Key Vault y recursos compartidos con lifecycle acorde a la
  definición; no usar `prevent_destroy` como sustituto de una estrategia de migración.
- Para renombrar direcciones Terraform, generar `moved` blocks.
- Para adoptar recursos existentes, generar una lista de `import`/import blocks y validarla en un
  ambiente controlado; no ejecutar imports desde Bob.
- Separar cambios de backend/provider de cambios funcionales cuando mezclarlos aumente el riesgo.

## Root modules y providers

- Cada `environments/<ambiente>` contiene `versions.tf`, provider configuration,
  `.terraform.lock.hcl`, backend, variables, locals, composición y outputs.
- Generar el lockfile con `terraform providers lock` para las plataformas de los agentes
  documentadas. Versionarlo en Git.
- Los módulos reutilizables no versionan su propio lockfile; validarlos en una copia temporal con
  un harness/root mínimo.
- Usar constraints compatibles pero no seleccionar versiones que Vulcano no aprobó.
- Consultar Registry mediante Terraform MCP solo como documentación actualizada; nunca reemplazar
  el constraint aprobado ni `.terraform.lock.hcl` por una recomendación `latest`.
- Probar módulos con `terraform test` en plan mode y providers mockeados antes de generar pipelines.

## Seguridad

- Preferir RBAC y managed identities sobre access policies/secretos estáticos cuando la definición
  lo permita.
- Marcar datos sensibles, pero recordar que `sensitive` solo oculta presentación: el valor sigue
  en state.
- Evitar secretos en argumentos de procesos, logs, `.tfvars`, artefactos y YAML.
- Ejecutar `shellcheck`, `gitleaks`, `tflint` y `trivy config` (o `tfsec`/`checkov` si `trivy` no
  está disponible) cuando estén disponibles.
- Aplicar mínimo privilegio por ambiente y separar identidades de plan/apply/deploy si la
  definición lo exige.

## Observabilidad implementable

Materializar explícitamente:

- Log Analytics Workspace y retención por ambiente;
- Application Insights y connection string sensible;
- diagnostic settings de App Service, PostgreSQL y Key Vault;
- Action Group con receivers parametrizados;
- reglas de alerta trazables a `ALT-NNN`;
- disponibilidad sintética cuando el documento la defina.

No crear una alerta sin scope, severidad, ventana, frecuencia, condición y Action Group.

## Pipelines reproducibles

- Construir una vez y promover el mismo artefacto por Build ID.
- Publicar checks/tests aunque un gate falle, usando condiciones que no oculten el código de salida.
- Cachear dependencias por lockfile; nunca cachear secretos ni outputs mutables.
- Usar Environments para approvals y exclusión mutua de despliegues.
- Mantener plan/apply enlazados por artefacto inmutable y commit SHA.
- Incluir health check y rollback documentado después de cada despliegue.
- Prohibir parámetros operativos vacíos antes de entrar al primer stage que los consume.

## Despliegue progresivo (canary / blue-green)

Aplicar solo cuando `decisions.deployment_strategy` (manifiesto de Vulcano) sea distinto de
`rolling` y el adaptador `pipeline` seleccionado declare soporte (`references/adapters.md`); en
otro caso, generar el job de deploy simple y no inventar un paso de análisis que nadie definió.

- Todo job de deployment con canary o blue-green declara explícitamente bake time y gate de
  análisis antes de promover al siguiente ambiente — nunca una promoción automática inmediata
  tras el health check básico.
- El gate de análisis lee la métrica y ventana confirmadas en `06-ci-cd.md` (input
  `ANALYSIS_METRICS_SOURCE` del contrato de `pipeline-app`); si esos datos no están definidos, el
  artefacto queda `conflict` — no se sustituye por un umbral inventado.
- El abort/rollback disparado por el gate reutiliza el mismo mecanismo de rollback documentado en
  `09-release-management.md`, no uno paralelo definido solo en el pipeline.
- Un adaptador `pipeline` sin `supports_progressive_delivery: true` no puede declarar este job:
  generar en su lugar el despliegue simple y registrar la brecha como `missing_capability`.

## Policy as code y notificaciones en el pipeline

Ambos son opt-in, condicionados a decisiones ya registradas por Vulcano — nunca generar el step
si la decisión sigue en `none`/sin resolver:

- **Policy as code** (`decisions.policy_engine`): el gate vive en el job/stage de `plan`, después
  de producir el `tfplan` y antes de publicarlo como artifact — un plan que no pasa política nunca
  llega al job de `apply`. Delegar la evaluación real a `./scripts/ci-policy-check.sh`, nunca
  inline el motor completo en el YAML.
- **Notificaciones** (`decisions.notification_channel`): vive en un job/stage final del pipeline
  de aplicación, separado del deploy, con `if: always()` / `when: always` / `condition: always()`
  según la plataforma — debe notificar tanto éxito como fallo, no solo el camino feliz. Delegar a
  `./scripts/ci-notify.sh`.

## Criterio de terminado

Un artefacto está terminado cuando existe, es ejecutable, sus contratos coinciden, sus dependencias
están cerradas, no contiene placeholders, pasa validación local y tiene hash de fuentes registrado.
Un fixture, comentario o YAML con jobs vacíos sigue siendo `pending` o `conflict`.
