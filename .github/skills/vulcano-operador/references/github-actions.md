# Operación de GitHub Actions por MCP

Descubrir una conexión MCP de GitHub con acceso al repositorio. Si no existe, registrar
`platform_mcp: missing` y detenerse; no pedir PAT ni sustituirla silenciosamente por REST o `gh`.

| Acción lógica | Riesgo | Lectura previa y verificación |
|---|---|---|
| `create_environment` | configure | Leer; crear si falta; releer reglas. |
| `update_actions_variable` | configure | Leer nombre/alcance; escribir valor no sensible; releer metadata. Cubre también rotar una referencia de secreto (URI/path del gestor externo) — nunca el valor del secreto en sí. |
| `configure_repository_ruleset` | configure | Leer rulesets/rama; aplicar diff mínimo; releer. |
| `dispatch_workflow` | execute | Resolver workflow/ref; despachar una vez; leer run. |
| `cancel_workflow_run` | execute | Leer run no terminal; cancelar; verificar estado. |
| `approve_deployment` | execute | Leer el deployment pendiente de revisión en el environment; aprobar o rechazar una vez; releer estado del deployment. Nunca aprobar un environment de producción (ver límites de `SKILL.md`). |
| `promote_release` | execute | Resolver el artefacto ya construido y el environment destino; redespachar el workflow de deploy fijado a ese artefacto (reusa el mecanismo de `dispatch_workflow`, pero se registra como acción distinta por su riesgo y evidencia); leer run resultante. |
| `rollback_deployment` | execute | Resolver el último artefacto/tag verificado como bueno; redespachar el workflow de deploy fijado a esa versión anterior; leer run y estado del environment tras el rollback. |
| `tag_release` | configure | Verificar que el tag no exista; crear el ref anotado sobre el commit liberado; releer el ref creado. |

Los workflows se versionan por Git; no existe `register_workflow`. Fuente:
[API de Actions](https://docs.github.com/en/rest/actions),
[environments](https://docs.github.com/en/actions/reference/workflows-and-actions/deployments-and-environments),
[pending deployments](https://docs.github.com/en/rest/actions/workflow-runs#review-pending-deployments-for-a-workflow-run) y
[Git refs](https://docs.github.com/en/rest/git/refs) para `tag_release`.
