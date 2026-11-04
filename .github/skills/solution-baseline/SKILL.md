---
name: solution-baseline
metadata:
  display-name: "Generador de bases de proyecto"
  capability: "Bases de aplicaciones"
  capability-summary: "Crea repositorios listos para desarrollar y los actualiza desde una arquitectura aprobada."
description: 'Materializa una arquitectura aprobada en líneas base de aplicación reproducibles. Úsala para crear, reconciliar o actualizar frontends, APIs, workers, agentes e integraciones; resolver o crear arquetipos gobernados; y coordinar soluciones multi-repositorio. No la uses para backlog funcional, DevOps, IaC o despliegue.'
---

# Solution Baseline

Convierte arquitectura aprobada en repositorios de aplicación reproducibles y listos para desarrollo. Trata al skill como fuente de verdad de políticas y coordinación; usa generadores nativos para materializar cada stack.

## Cuándo usar

- Crear uno o varios proyectos desde una arquitectura greenfield.
- Ajustar un frontend o backend existente a una arquitectura vigente.
- Resolver requisitos `ARQ-xxx` contra catálogos de arquetipos.
- Crear y publicar un arquetipo reusable cuando exista una brecha real.
- Instanciar una versión de arquetipo en múltiples repositorios.
- Calcular drift o actualizar una baseline a otra versión.
- Validar que una solución esté lista para que `builder` continúe el desarrollo.

No usar para implementar backlog funcional, pipelines, IaC, Dockerfiles operacionales, aprovisionamiento o despliegue.

## Invariantes

1. Lee primero arquitectura, contratos y código existente; la arquitectura aprobada define el estado deseado y el repositorio demuestra el estado real.
2. Distingue especificación arquitectónica, arquetipo reusable, capability, overlay e instancia.
3. Busca en catálogos autorizados antes de crear un arquetipo.
4. Resuelve runtime, framework, generador, arquetipo y capabilities a versiones exactas antes de aplicar. Nunca dejes `latest` como versión efectiva.
5. Mantén separados catálogo/arquetipo e instancias. Una instancia nunca consume una plantilla mutable ni modifica su fuente.
6. Toda escritura sigue `inspect → plan → render temporal → validate → diff → review/approve → apply → validate → receipt`.
7. Nunca sobrescribas silenciosamente contenido brownfield ni código `project_owned`.
8. No ejecutes hooks o tareas arbitrarias de un catálogo por defecto. Verifica fuente, licencia, commit/digest, permisos e integridad.
9. Un solo writer posee cada repositorio o zona durante una fase. Congela contratos antes de generar consumidores en paralelo; para componentes `web`/`library`, congela también el sistema de diseño declarado (tokens, catálogo de componentes y assets de marca) y no fijes valores de marca en el código generado — ver [capabilities-and-overlays.md](./references/capabilities-and-overlays.md#capability-design-system).
10. No hagas commits, push, publicación de arquetipos ni creación de repositorios remotos sin autorización explícita.
11. No generes DevOps, IaC, empaquetado operacional ni despliegue. Entrega metadatos a Vulcano sin invocarlo automáticamente.
12. Si falta una decisión arquitectónica material, emite un `architecture-gap` y devuelve ese control a `archi`; no confundas esa brecha con la ausencia de un arquetipo publicado.

## Resolver el modo

| Situación | Modo | Referencia obligatoria |
|---|---|---|
| Solo inventario o diagnóstico | `discover` / `status` | [modes.md](./references/modes.md) |
| Plan sin escritura en destinos | `plan` / `dry-run` | [generator-protocol.md](./references/generator-protocol.md) |
| Repositorio vacío | `create` | [greenfield.md](./references/greenfield.md) |
| Repositorio con código | `reconcile` | [brownfield.md](./references/brownfield.md) |
| Cambio de versión de arquetipo | `upgrade` | [migrations-and-drift.md](./references/migrations-and-drift.md) |
| No existe patrón reusable | `archetype-create` | [archetype-lifecycle.md](./references/archetype-lifecycle.md) |
| Múltiples repositorios o ejecución larga | `orchestrate` / `resume` | [multi-repository.md](./references/multi-repository.md) |

Lee además [security-and-trust.md](./references/security-and-trust.md) antes de ejecutar código obtenido de catálogos o realizar acciones con red.

## Raíz portable

Resuelve `<skill-root>` como el directorio absoluto que contiene este `SKILL.md`. Todas las invocaciones incluidas son relativas a esa raíz; nunca asumas que el consumidor usa `.claude/skills/solution-baseline`. Al instalarse como plugin, los scripts y referencias deben funcionar desde su ubicación real sin copiar el skill dentro del proyecto.

## Flujo obligatorio

### 1. Descubrir

1. Localiza las fuentes arquitectónicas aprobadas y léelas completas.
2. Inspecciona todos los repositorios destino antes de decidir greenfield o brownfield.
3. Identifica componentes, dependencias, contratos ejecutables, stacks, restricciones y vacíos.
4. Usa `scripts/solution_baseline.py inspect --root <repo>` para obtener evidencia reproducible del estado técnico.
5. Marca cada dato como `confirmed`, `inferred` o `pending`. Pregunta solo por pendientes que cambien materialmente el resultado.

Si una contradicción o ausencia afecta topología, límites, ownership, contratos, seguridad, estilo o stack, sigue [architecture-handoff.md](./references/architecture-handoff.md). Registra un gap trazable, bloquea solo los componentes afectados y permite que los independientes continúen.

Lee [architecture-discovery.md](./references/architecture-discovery.md) para construir la entrada normalizada.

### 2. Construir el blueprint

Crea `resources/.solution-baseline/solution-blueprint.yaml` conforme a [artifact-contracts.md](./references/artifact-contracts.md). Incluye trazabilidad hacia las fuentes, topología, componentes, contratos, versiones solicitadas, capabilities, exclusiones y decisiones pendientes. No incluyas estado transitorio del run ni secretos. Las brechas que requieren decisión de `archi` viven separadas en `architecture-gaps/` y se referencian desde el run manifest.

Valida:

```powershell
python "<skill-root>/scripts/solution_baseline.py" validate --kind blueprint --file resources/.solution-baseline/solution-blueprint.yaml
```

### 3. Resolver arquetipos y versiones

Consulta únicamente catálogos autorizados. Aplica gates antes de puntuar compatibilidad. Prefiere, en orden:

1. Familia compatible en versión soportada.
2. Familia compatible más capabilities u overlay declarativo.
3. Nuevo arquetipo reusable, solo con evidencia de generalización y publicación gobernada.
4. Baseline específica no promovida cuando el patrón sea exclusivo de la solución.

Lee [archetype-selection.md](./references/archetype-selection.md) y [capabilities-and-overlays.md](./references/capabilities-and-overlays.md). Antes de seleccionar, genera una verificación local de la fuente y exige que identidad, origen y digest coincidan. Registra la versión, digest y evidencia resueltos en el run manifest.

### 4. Planear y hacer dry-run

Crea un `run-manifest.yaml` por ejecución. Construye el DAG, congela contratos y asigna ownership exclusivo. Para cada repositorio:

1. Invoca `metadata`, `inspect` y `plan` del adaptador.
2. Ejecuta validación estricta de blueprint, catálogo y requisitos; luego renderiza en un directorio temporal aislado.
3. Ejecuta las validaciones del stack sobre el render.
4. Compara render, ancestro conocido y destino actual.
5. Presenta cambios, riesgos, conflictos y autorizaciones antes de `apply`.

Audita las rutas del change set con `audit-scope`; una violación indica que el plan invadió responsabilidades de Vulcano.

No uses generación textual ad hoc cuando exista un motor nativo compatible. Lee [generator-protocol.md](./references/generator-protocol.md) y [stack-adapters.md](./references/stack-adapters.md).

### 5. Aplicar

Aplica únicamente el diff aprobado. En brownfield respeta estas categorías del receipt:

- `managed`: regenerable si no existe drift conflictivo.
- `extendable`: modificable solo en puntos declarados y mediante transformación semántica.
- `project_owned`: nunca sobrescribir automáticamente.
- `generated_once`: crear si falta y transferir al proyecto.
- `ignored`: no inspeccionar ni modificar salvo validación explícita.

Prefiere AST, parsers o APIs del framework para código. Conserva cambios ajenos y detén solo el componente afectado si aparece un conflicto no resoluble.

### 6. Validar y registrar

Ejecuta instalación, lint, análisis estático, build, pruebas unitarias, integración y contratos que correspondan al stack y al alcance. Valida un vertical slice mínimo y los controles arquitectónicos aplicables. No declares éxito con una comprobación meramente estructural.

Actualiza `.solution-baseline/receipt.yaml` por repositorio con procedencia, ownership, hashes, validaciones, migraciones y drift aceptado. Emite `.solution-baseline/vulcano-handoff.yaml` por componente y valídalo con `--kind handoff --strict`. Registra resultados estructurados en el run manifest y prepara el handoff descrito en [quality-gates-and-handoff.md](./references/quality-gates-and-handoff.md).

## Multi-repositorio y paralelismo

- Paraleliza descubrimiento de solo lectura.
- Publica un arquetipo antes de abrir instancias consumidoras.
- Congela OpenAPI, AsyncAPI, schemas y eventos antes de generar productores/consumidores, y el sistema de diseño (tokens, catálogo de componentes, assets de marca) antes de generar frontends o librerías de UI.
- Asigna un writer por repositorio o zona disjunta y usa worktrees/workspaces separados.
- Antes de iniciar cada agente mutable, ejecuta `verify-workspace`; no delegues si el workspace coincide con el checkout principal o no pertenece al worktree esperado.
- Valida cada ola de assignments con `check-concurrency`. Los límites canónicos viven en `assets/policies/concurrency-limits.yaml`; el runtime puede imponer un límite menor, nunca uno mayor para este flujo.
- Centraliza el manifest en el orquestador; los workers devuelven resultados estructurados.
- Trata el run como saga: pasos idempotentes, hashes, checkpoints y compensación solo cuando sea segura.
- Preserva éxitos parciales y permite `resume`; no simules atomicidad borrando repositorios.

## Agentes disponibles

| Agente | Archivo | Uso |
|---|---|---|
| Solution Baseline Orchestrator | `../../agents/solution-baseline-orchestrator.agent.md` | Coordinar el flujo completo y multi-repositorio |
| Architecture Mapper | `../../agents/architecture-mapper.agent.md` | Descubrimiento de solo lectura |
| Archetype Curator | `../../agents/archetype-curator.agent.md` | Crear/evolucionar arquetipos en catálogo aislado |
| Repository Baseline Worker | `../../agents/repository-baseline-worker.agent.md` | Crear/reconciliar/actualizar un repositorio asignado |
| Baseline Validator | `../../agents/baseline-validator.agent.md` | Validación independiente en worktree aislado, sin corregir código |

Para una ejecución amplia invoca el orquestador. Los cuatro especialistas son subagentes internos y no sustituyen las reglas de este skill.

Antes de instalarlos o delegar trabajo, lee [agent-operations.md](./references/agent-operations.md). La instalación debe verificar hashes, y cada agente mutable debe superar aislamiento y límites de concurrencia.

## Herramientas incluidas

```powershell
# Ayuda general
python "<skill-root>/scripts/solution_baseline.py" --help

# Inicializar blueprint y run manifest sin sobrescribir existentes
python "<skill-root>/scripts/solution_baseline.py" init --solution-id <id> --architecture-root resources/architecture --output-root resources/.solution-baseline

# Validar artefactos
python "<skill-root>/scripts/solution_baseline.py" validate --kind <blueprint|run|receipt|catalog|result|adapter|requirement|handoff|gap|evaluation|observations|verification|scope-policy|concurrency-policy|assignments|agent-installation> --file <ruta>

# Inspeccionar, comparar árboles y resolver catálogo
python "<skill-root>/scripts/solution_baseline.py" inspect --root <repo>
python "<skill-root>/scripts/solution_baseline.py" diff --expected <render> --actual <repo>
python "<skill-root>/scripts/solution_baseline.py" verify-source --archetype-id <id> --source <origen> --material <cache-local> --digest <sha256:...|git:...> --output <verification.yaml>
python "<skill-root>/scripts/solution_baseline.py" resolve --catalog <catalog.yaml> --requirement <requirement.yaml> --verification <verification.yaml>
python "<skill-root>/scripts/solution_baseline.py" audit-scope --changes <changes.yaml>
python "<skill-root>/scripts/solution_baseline.py" check-drift --root <repo>
python "<skill-root>/scripts/solution_baseline.py" check-design-conformance --root <repo> --blueprint <blueprint.yaml> --component <id> --solution-root <raíz-de-la-solución>
python "<skill-root>/scripts/solution_baseline.py" verify-genesis-migration --genesis-root <repo>/.claude/skills/genesis
python "<skill-root>/scripts/solution_baseline.py" evaluate-routing --evaluation <cases.yaml> --observations <observations.yaml>

# Instalar/verificar agentes y límite de runtime en un proyecto consumidor
python "<skill-root>/scripts/solution_baseline.py" agents install --project-root <repo> --platform codex claude --configure-runtime
python "<skill-root>/scripts/solution_baseline.py" agents check --project-root <repo> --platform codex claude

# Verificar aislamiento y una ola de ejecución antes de delegar
python "<skill-root>/scripts/solution_baseline.py" verify-workspace --workspace <worktree> --main-checkout <checkout-principal>
python "<skill-root>/scripts/solution_baseline.py" check-concurrency --assignments <agent-assignments.yaml>

# Administrar lease local y registrar un paso idempotente
python "<skill-root>/scripts/solution_baseline.py" lease acquire --file <lease.json> --owner <worker> --ttl-seconds 900
python "<skill-root>/scripts/solution_baseline.py" record-step --manifest <run-manifest.yaml> --result <generator-result.yaml>

# Pruebas contractuales del skill
python "<skill-root>/scripts/test_solution_baseline.py" -v
```

Los scripts requieren Python 3.11+ y las dependencias fijadas en `scripts/requirements.txt`: PyYAML, `jsonschema`, `referencing`, `packaging` y `filelock`. Son auxiliares deterministas; no sustituyen la interpretación arquitectónica ni descargan o ejecutan generadores remotos.

## Gotchas

- **“Arquetipo” en un documento no prueba que exista una plantilla.** Trátalo primero como requisito `ARQ-xxx`.
- **Un repositorio con código no es greenfield.** Inspecciona antes de crear y usa `reconcile` aunque el roadmap diga lo contrario.
- **Una versión nueva no actualiza instancias.** Requiere `upgrade` explícito y ruta de migración soportada.
- **Un overlay no es un fork silencioso.** Declara alcance, orden, ownership y compatibilidad.
- **El catálogo queda de solo lectura durante instanciación.** Nunca generes directamente desde un workspace mutable del arquetipo.
- **La arquitectura puede estar desactualizada respecto al código.** Conserva funcionalidad observable y eleva la inconsistencia documental.
- **Genesis es compatibilidad greenfield.** No mantengas un segundo proceso divergente; enruta su intención a este skill.
- **Declarar `managed` en el receipt no lo hace inmutable.** Corre `check-drift` para detectar edición manual fuera del skill; no confíes solo en la categoría declarada.
- **El handoff a Vulcano no es un archivo de despliegue.** Es intención de aplicación compatible con el vocabulario de Score (puertos, health, dependencias por tipo); no le agregues `image`, `volumes` ni límites de recursos.

## Referencias

- [Límites y responsabilidades](./references/boundaries.md)
- [Modos y estados](./references/modes.md)
- [Descubrimiento arquitectónico](./references/architecture-discovery.md)
- [Handoff de brechas a arquitectura](./references/architecture-handoff.md)
- [Contratos de artefactos](./references/artifact-contracts.md)
- [Selección de arquetipos](./references/archetype-selection.md)
- [Lifecycle de arquetipos](./references/archetype-lifecycle.md)
- [Capabilities y overlays](./references/capabilities-and-overlays.md)
- [Protocolo de generadores](./references/generator-protocol.md)
- [Greenfield](./references/greenfield.md)
- [Bootstrap greenfield por stack](./references/greenfield-stack-bootstrap.md)
- [Convenciones greenfield](./references/greenfield-conventions.md)
- [Plomería base de aplicación](./references/application-plumbing.md)
- [Brownfield](./references/brownfield.md)
- [Migraciones y drift](./references/migrations-and-drift.md)
- [Multi-repositorio](./references/multi-repository.md)
- [Instalación, aislamiento y concurrencia de agentes](./references/agent-operations.md)
- [Seguridad y confianza](./references/security-and-trust.md)
- [Adaptadores por stack](./references/stack-adapters.md)
- [Calidad y handoff](./references/quality-gates-and-handoff.md)
- [Evaluación de routing](./assets/evaluations/skill-routing.yaml)
- [Equivalencia contractual de Genesis](./assets/evaluations/genesis-greenfield-equivalence.yaml)

## Registro de avance en memoria

Al terminar tu tarea, deja un nodo de avance en la memoria del proyecto (skill
[`memoria`](../memoria/SKILL.md)) con el payload mínimo
`{ "skill": "solution-baseline", "type": "avance", "title": "...", "summary": "..." }`:

    node .claude/skills/memoria/scripts/memoria.mjs record \
      --skill solution-baseline --type avance --title "..." --summary "..." \
      --file <ruta del artefacto> [--link <id-del-nodo-previo>]

O escribe ese payload como JSON en `.memoria/pending/<timestamp>.json`: el hook de Stop
lo consolida en `.memoria/graph.json` al cerrar el turno. Si la misma tarea ya tiene nodo
(mismo `skill` + `title`), actualízalo en vez de duplicarlo.
