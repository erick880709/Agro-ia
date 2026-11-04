# Migraciones y drift

## Clasificación de drift

- `expected`: personalización prevista por un punto de extensión.
- `accepted`: divergencia revisada y documentada con owner.
- `migratable`: cambio que una migración soportada puede transformar.
- `conflicting`: arquetipo y proyecto modificaron la misma responsabilidad.
- `unknown`: no existe ancestro o evidencia suficiente.

El porcentaje de archivos iguales no determina compatibilidad. Prioriza contrato, ownership y semántica.

Para detectar drift `unknown` en archivos `managed` sin re-renderizar el arquetipo, usa `check-drift --root <repo>` (ver [quality-gates-and-handoff.md](./quality-gates-and-handoff.md#verificación-continua-de-archivos-managed)); solo compara hashes contra lo ya registrado en el receipt, así que corre en cada `reconcile`/`upgrade` y puede colgarse de un gate de CI.

## Ruta de upgrade

1. Valida receipt, versión origen y digest.
2. Resuelve una ruta continua de migraciones publicadas hasta la versión objetivo.
3. Comprueba precondiciones y compatibilidad de runtime/capabilities.
4. Reconstruye ancestro y versión objetivo en workspaces temporales.
5. Aplica migraciones en orden sobre una copia del estado actual.
6. Ejecuta validaciones y diff de tres vías.
7. Presenta conflictos, rollback y cambios de ownership.
8. Aplica al destino solo después de aprobación.
9. Repite validación y actualiza receipt.

No saltes versiones implícitamente. Si falta una migración declarada o falla una precondición, detén el upgrade con diagnóstico y alternativas.

## Transformaciones

Prefiere AST, parsers, codemods o APIs del framework. Usa reemplazo de texto solo para archivos declarativos simples, con precondiciones estrictas y verificación posterior. Toda migración debe ser idempotente o detectar de forma segura que ya fue aplicada.

## Rollback

Antes de aplicar, registra archivos afectados y hash actual. Declara compensación únicamente si restaura los cambios propios sin eliminar cambios posteriores. En Git, una rama/worktree o commit del usuario puede aportar recuperación, pero el skill no crea commits sin autorización.

