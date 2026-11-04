# Instalación, aislamiento y concurrencia de agentes

## Instalación portable

Resuelve `<skill-root>` desde el `SKILL.md` cargado. No presupongas una carpeta `.claude` en el proyecto consumidor.

```powershell
python "<skill-root>/scripts/solution_baseline.py" agents install `
  --project-root <repo> `
  --platform codex claude `
  --configure-runtime

python "<skill-root>/scripts/solution_baseline.py" agents check `
  --project-root <repo> `
  --platform codex claude
```

`install` valida primero las cinco definiciones empaquetadas. Crea únicamente los archivos de agente esperados y registra hashes en `<repo>/.solution-baseline/agent-installation.json`. Una definición existente con contenido diferente bloquea la operación. `--force` y `--force-config` son operaciones explícitas y requieren revisión del conflicto; no las uses por defecto.

Para Codex, `--configure-runtime` crea o completa `.codex/config.toml` con `agents.max_concurrent_threads_per_session` igual a `max_parallel_agents`. Conserva las demás opciones. Si ya existe otro límite, se detiene en vez de reemplazarlo silenciosamente.

## Aislamiento obligatorio

Antes de iniciar `archetype-curator`, `repository-baseline-worker` o `baseline-validator`, valida el workspace asignado:

```powershell
python "<skill-root>/scripts/solution_baseline.py" verify-workspace `
  --workspace <worktree> `
  --main-checkout <checkout-principal>
```

La validación normal exige que ambos directorios sean worktrees Git enlazados al mismo repositorio y que tengan raíces distintas. `--allow-non-git` solo aplica a un workspace temporal o catálogo que explícitamente no use Git; aun así debe estar fuera del checkout principal. No inicies el agente cuando el resultado sea inválido.

## Ola de ejecución

Materializa la ola propuesta desde `assets/templates/agent-assignments.template.yaml` y valida antes de delegar:

```powershell
python "<skill-root>/scripts/solution_baseline.py" check-concurrency `
  --assignments <agent-assignments.yaml>
```

Los estados `scheduled` y `running` consumen capacidad. La política canónica permite como máximo cuatro subagentes activos, cuatro readers, dos writers, un writer por repositorio y un writer de catálogo. Un límite menor impuesto por el runtime prevalece. Worker y validator del mismo repositorio pertenecen a olas distintas.

El orquestador conserva el único ownership del run manifest. Los agentes devuelven resultados estructurados; terminar un hilo no transfiere ownership ni libera un lease automáticamente.
