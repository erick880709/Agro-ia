# Modos y estados

## Modos

| Modo | Entrada mínima | Escritura permitida | Salida |
|---|---|---|---|
| `discover` | Fuentes y repositorios | Ninguna | Inventario y vacíos |
| `plan` | Blueprint válido | Run manifest si fue solicitado | DAG, selección, riesgos y autorizaciones |
| `dry-run` | Plan y versiones exactas | Solo workspace temporal | Render, validación y diff |
| `create` | Destino sin código y plan aprobado | Repositorio asignado | Baseline greenfield y receipt |
| `reconcile` | Repositorio existente y plan aprobado | Cambios acotados por ownership | Parches, drift y receipt actualizado |
| `upgrade` | Receipt y ruta de migración | Cambios acotados por ownership | Baseline migrada y evidencia |
| `archetype-create` | Brecha reusable aprobada | Workspace exclusivo de catálogo | Candidato probado; publicación aparte |
| `validate` | Repositorio o render | Solo reportes solicitados | Evidencia y gate |
| `status` | Run manifest | Ninguna | Estado consolidado |
| `resume` | Manifest con checkpoints | Según plan original | Continuación idempotente |

## Estados del run

```text
discovered → planned → rendered → reviewed → applying → validating → completed
                    ↘ blocked         ↘ partial       ↗
```

- `blocked`: no se puede continuar el componente sin una decisión o autoridad nueva.
- `partial`: otros componentes válidos se conservan; registra el fallo y la compensación disponible.
- `completed`: todos los gates del alcance solicitado pasaron y existen receipts.

No marques `completed` por agotar tiempo o porque el plan fue generado. Un dry-run exitoso termina en `reviewed`, no en `completed`.

## Reanudación

Antes de reanudar, verifica que blueprint, catálogo, contratos, destino y versiones sigan teniendo los hashes registrados. Si cambió una entrada, invalida los pasos dependientes y vuelve a `plan`; no reutilices resultados obsoletos.

