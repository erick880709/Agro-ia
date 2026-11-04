# Contrato de adaptadores

El operador resuelve `platform` desde `bob.adapter_selection.pipeline` y `cloud` desde
`bob.adapter_selection.cloud`. No existe un adaptador por combinación.

## Descriptor de plataforma

Declarar:

- `status`: `implemented` o `planned`.
- `mcp_capability`: nombre humano de la capacidad que debe descubrirse.
- `required_target_fields`: coordenadas obligatorias para cierre estricto.
- `allowed_actions`: mapa acción → riesgo `configure` o `execute`.
- `reference`: reglas MCP específicas.

El núcleo deriva el riesgo desde `allowed_actions`. Una acción ausente está prohibida aunque el
MCP exponga una herramienta con nombre similar.

Además de las acciones de configuración de repositorio/pipeline, `allowed_actions` cubre el ciclo
de vida del release una vez desplegado: `approve_deployment`, `promote_release`,
`rollback_deployment` y `tag_release`. `approve_deployment` nunca puede resolver un approval de
producción — esa regla vive en `SKILL.md` §Límites no negociables y no la reemplaza esta tabla.

## Descriptor cloud

Declarar capacidad MCP, modo y referencia. El modo actual es `read_only_verification`: la nube
sirve para observar salud/configuración posterior, no para sustituir Terraform. `cloud/gcp` está
`implemented` en el mismo modo (ver `references/gcp.md`); igual que Azure/AWS, nunca sustituye a
Terraform ni autoriza mutaciones.

## Descriptores `gitops` y `chatops`

Dos dimensiones adicionales, independientes de `platform` y `cloud`, resueltas solo cuando
`vulcano-bob` las declaró en `bob-manifest.yaml` (`decisions.deployment_model: gitops` /
`decisions.notification_channel` ≠ `none`):

- **`gitops`** (ej. `adapters/gitops/argocd.json`): mismo formato que un descriptor de
  plataforma. `allowed_actions` distingue `reconcile_gitops_app` (`configure` — forzar una
  resincronización) de `sync_gitops_app` (`execute` — aplicar el estado deseado ya reconciliado).
  No sustituye a `platform`: la reconciliación GitOps opera sobre el repositorio de manifiestos
  que `gitops-manifests` de Bob ya generó, mientras que `platform` sigue gobernando CI y el
  repositorio de código. Ver `references/gitops-argocd.md` para el mapeo REST objetivo y los
  requisitos antes de pasar de `planned` a `implemented`.
- **`chatops`** (ej. `adapters/chatops/slack.json`): descriptor liviano con una sola acción,
  `post_notification` (`configure` — publicar, no persiste estado mutable de la plataforma). No
  requiere `required_target_fields` de repositorio, solo canal/organización del proveedor de
  mensajería.

Ambas dimensiones están catalogadas como `planned` en `adapters/registry.json`: existen para que
`resolve-operator-adapters.mjs` reconozca la decisión del arquitecto y falle con
`missing_capability` en vez de ignorarla — habilitarlas como `implemented` sigue el mismo
procedimiento de la sección "Habilitar un adaptador" de abajo.

## Habilitar un adaptador

1. Completar routing MCP y allowlist mínimo.
2. Definir sanitización, idempotencia y lectura previa/posterior.
3. Agregar fixtures de reconcile, autorización, ejecución ambigua y verificación.
4. Probar ausencia de secretos y expansión de alcance.
5. Cambiar a `implemented` solo después de pasar las pruebas.

`--allow-planned` solo inspecciona una resolución futura; nunca permite crear el manifiesto
operacional ni ejecutar acciones.
