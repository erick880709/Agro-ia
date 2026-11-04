# Alcance y contexto de la revisión

## Obtener el cambio

| El usuario dice | Fuente del diff |
|---|---|
| Pega un diff o fragmento | Ese texto; pide el archivo completo si el contexto es indispensable |
| "mis cambios", "sin commit" | `git diff` + `git diff --staged` (y `git status` para archivos nuevos sin trackear) |
| "esta rama", "mi PR" | `git diff <base>...HEAD` donde `<base>` es la rama destino real (`main`, `develop`, `trunk`); confírmala con `git merge-base` o la config del repo |
| Commit concreto / rango | `git show <sha>` / `git diff <a>..<b>` |
| Builder entrega un cambio | Revisión indicada en su evidencia; si hay cambios sin commit, diff + hashes de archivos |

Registra en el reporte la revisión exacta revisada (SHA, rama o "sin commit +
hash"). Un reporte sin revisión no sirve para saber si sigue vigente.

Lee siempre los archivos completos tocados, no solo los hunks: la validación
que falta suele estar diez líneas arriba. Para símbolos cambiados, busca sus
usos (`grep -rn`) para detectar consumidores rotos fuera del diff.

## Fuente funcional

Busca en este orden y usa la primera que exista:

1. `docs/changes/<id>/spec.md` (expediente de Builder) y su `evidence.md`.
2. OpenSpec (`openspec/changes/<id>/`) o Spec Kit (`specs/`), respetando su
   ubicación; no los sincronices ni archives.
3. Issue/historia accesible (ID, URL) y su padre si es necesario para el alcance.
4. La descripción del PR o el encargo del usuario.

Extrae los criterios (`AC-01`, …) y el comportamiento a preservar. Si no hay
criterios explícitos, escribe en el reporte "Intención reconstruida" con lo que
inferiste y márcalo como inferencia: no lo presentes como requisito aprobado.

## Reglas del proyecto

Lee, si existen: `CLAUDE.md`, `AGENTS.md`, `REVIEW.md`, `CONTRIBUTING.md`, ADR
(`docs/adr/`), configuración de lint/format (`.editorconfig`, checkstyle,
spotless, eslint, sonar), y `.solution-baseline/receipt.yaml`. `REVIEW.md`, si
existe, define reglas propias de revisión del equipo (qué siempre señalar, qué
ignorar): aplícalas encima de esta skill sin violar sus invariantes.

Archivos `managed` de una baseline no deben haber sido editados por el cambio;
si lo fueron, es hallazgo `mayor` (o `bloqueante` si se actualizó el hash del
receipt para ocultarlo).

## Triage automático

```bash
git diff <base>...HEAD | python <skill-root>/scripts/diff_triage.py
python <skill-root>/scripts/diff_triage.py --diff-file cambio.diff --json
```

Devuelve tamaño, archivos por categoría (fuente, test, build, config,
migración, lockfile, sensible), señales de riesgo y una profundidad sugerida.
Cada señal es una pista para mirar, no un hallazgo: verifícala (paso 4).

## Profundidad

| Rigor | Cuándo | Qué implica |
|---|---|---|
| Ligero | Cambio localizado, declarativo o textual | Una lectura con las pasadas A–G como preguntas; reporte breve |
| Estándar | Feature, bug con lógica, varias capas | Todas las pasadas, verificación de hallazgos, reporte completo |
| Reforzado | Authz/permisos, datos persistentes o migraciones, dinero, PII, concurrencia, contratos públicos, varios repos | Además: escenarios negativos explícitos, compatibilidad de contrato, prueba de mutación en lógica crítica, revisión de rollback |

El rigor lo decide el riesgo, no el número de líneas. Una línea que cambia una
regla de autorización es reforzado.

## Tamaño

~100 líneas: una sesión. ~300: aceptable si es un solo cambio lógico. ~1000+:
recomienda dividir (stack, por grupo de archivos, horizontal o vertical) y, si
igual hay que revisarlo, hazlo por componentes declarando el orden. Mezclar
refactor y feature en un mismo cambio es hallazgo `menor` (o `mayor` si impide
verificar que el refactor preserva comportamiento).
