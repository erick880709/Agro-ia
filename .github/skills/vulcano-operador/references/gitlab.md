# Operación de GitLab CI/CD por MCP

Descubrir una conexión MCP de GitLab con acceso al proyecto. Si falta, registrar
`platform_mcp: missing`; no solicitar tokens ni improvisar REST/CLI.

| Acción lógica | Riesgo | Lectura previa y verificación |
|---|---|---|
| `create_environment` | configure | Leer; crear solo si falta; releer. |
| `update_cicd_variable` | configure | Comparar metadata/scope; nunca persistir valor; releer metadata. Cubre también rotar una referencia de secreto (URI/path del gestor externo) — nunca el valor del secreto en sí. |
| `configure_protected_branch` | configure | Leer; aplicar diff mínimo; releer. |
| `run_pipeline` | execute | Resolver proyecto/ref; ejecutar una vez; leer pipeline. |
| `cancel_pipeline` | execute | Leer pipeline no terminal; cancelar; verificar estado. |
| `approve_deployment` | execute | Leer el deployment pendiente de aprobación en el protected environment; aprobar o rechazar una vez; releer estado. Nunca aprobar un environment de producción (ver límites de `SKILL.md`). |
| `promote_release` | execute | Resolver el artefacto ya construido y el environment destino; ejecutar el pipeline fijado a ese artefacto/ambiente (reusa el mecanismo de `run_pipeline`, pero se registra como acción distinta por su riesgo y evidencia); leer pipeline resultante. |
| `rollback_deployment` | execute | Resolver el último artefacto/tag verificado como bueno; ejecutar el pipeline fijado a esa versión anterior; leer pipeline y estado del environment tras el rollback. |
| `tag_release` | configure | Verificar que el tag no exista; crear el tag sobre el commit liberado; releer el tag creado. |

La configuración `.gitlab-ci.yml` se registra por Git. Fuentes:
[Pipelines API](https://docs.gitlab.com/api/pipelines/),
[protected environments](https://docs.gitlab.com/ci/environments/protected_environments/),
[deployment approvals](https://docs.gitlab.com/api/deployments/#approve-or-reject-a-blocked-deployment) y
[Tags API](https://docs.gitlab.com/api/tags/) para `tag_release`.
