# Estado y migración

`resources/.vulcano/operations-manifest.yaml` usa schema v2 y pertenece al núcleo operador.
Incluye `operator_selection`, capacidades genéricas `platform_mcp`/`cloud_mcp`, snapshot,
acciones, autorizaciones y evidencia.

Para migrar cualquier manifiesto operacional schema v1:

```powershell
node .claude/skills/vulcano-operador/scripts/init-operations-manifest.mjs --migrate
```

La migración:

- resuelve adaptadores desde Bob;
- traduce `azure_devops_mcp` a `platform_mcp` y `azure_mcp` a `cloud_mcp`;
- conserva acciones y evidencia;
- invalida autorizaciones activas y vuelve a `reconcile`;
- deja el gate `pending` hasta una reconciliación nueva.

No usar `--force` como migración: recrea el estado desde plantilla y perdería el historial.
