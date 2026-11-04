# Contratos de artefactos

Los schemas canónicos viven en `../assets/schemas/` y las plantillas en `../assets/templates/`.

## Solution blueprint

Ruta recomendada: `resources/.solution-baseline/solution-blueprint.yaml`.

Representa el estado deseado estable: fuentes, componentes, contratos, relaciones, stacks, capabilities, restricciones, exclusiones y decisiones. No contiene intentos, locks o logs de ejecución.

Debe versionarse con la arquitectura y cambiar mediante revisión arquitectónica cuando se modifique el estado deseado.

Un componente `web` o `library` puede declarar `design_system`: ruta fuente del sistema de diseño del proyecto, `status`, tokens (`*.tokens.json`), catálogo de componentes y manifiesto de assets de marca —cada uno con `sha256` cuando está congelado—, paquete compartido opcional, `style_zones` donde se permiten literales de estilo, `literal_exemptions` y `max_literal_violations` (trinquete para brownfield). Es la referencia que verifica `check-design-conformance`; los valores de marca viven en esos artefactos del proyecto, nunca en el blueprint ni en el skill.

## Run manifest

Ruta recomendada: `resources/.solution-baseline/runs/<run-id>/run-manifest.yaml`.

Registra una ejecución: referencia y hash del blueprint, catálogo resuelto, versiones exactas, DAG, leases, idempotencia, pasos, evidencias, bloqueos, brechas arquitectónicas y handoff. El DAG contiene nodos con dependencias y barreras que liberan nodos; la validación estricta rechaza IDs duplicados, referencias desconocidas, ciclos y runs completados con nodos inconclusos. Puede conservarse como evidencia o archivarse según la política del equipo.

Un worker no edita este archivo. Devuelve un generator result y el orquestador consolida mediante escritura atómica.

## Architecture gap

Ruta: `resources/.solution-baseline/architecture-gaps/<gap-id>.yaml`.

Formaliza una decisión que `solution-baseline` no debe inventar y devuelve su control a `archi`: topología, límites, ownership, contratos, seguridad, estilo o stack. Incluye pregunta, impacto, decisión solicitada, fuentes y evidencia. Un gap abierto bloquea solo los componentes afectados. La falta de un arquetipo publicado no crea este artefacto si la arquitectura ya define suficientemente el estado deseado. Ver [architecture-handoff.md](./architecture-handoff.md).

## Receipt

Ruta: `<repository>/.solution-baseline/receipt.yaml`.

Es la memoria local de procedencia y actualización: familia, versión, fuente, digest, generador, parámetros no sensibles, capabilities, overlays, ownership, hashes, drift aceptado, migraciones y validaciones.

El receipt no convierte todo el repositorio en contenido administrado. Todo archivo no clasificado se trata como `project_owned` hasta que un plan revisado decida otra cosa.

## Vulcano handoff

Ruta: `<repository>/.solution-baseline/vulcano-handoff.yaml`.

Subconjunto estructuralmente compatible con el vocabulario de Score (score.dev/v1b1) para declarar, por componente, lo que la aplicación necesita para ejecutarse: variables de configuración (nombres, no valores), health probes, puertos y dependencias externas por tipo. `component_id` y `workload` son campos de enlace con el blueprint, no forman parte del vocabulario Score. No incluye `image`, `volumes`, `files` ni `resources.limits/requests` — build, capacidad y aprovisionamiento son de Vulcano. Ver [quality-gates-and-handoff.md](./quality-gates-and-handoff.md#handoff-a-vulcano).

## Generator result

Cada operación devuelve un resultado con:

- `operation`, `status`, `repository_id` y `idempotency_key`.
- `input_hash` y `output_hash` cuando aplique.
- `artifacts`, `decisions`, `warnings`, `evidence` y `next_steps`.
- `agent_context` suficiente para reanudar sin depender del historial de conversación.
- `compensation` solo si es segura y comprobada.

## Source verification

Ruta recomendada: `resources/.solution-baseline/verifications/<archetype-id>.yaml`.

Atesta material local contra `sha256` de archivo/árbol o commit `git`. Vincula identidad, origen, ruta material y digest esperado/observado. Se recalcula al resolver; no reemplaza la autorización para obtener la fuente ni habilita su ejecución.

## Routing observations

Registra resultados observados por un harness externo para los casos de `skill-routing.yaml`. `evaluate-routing` compara activación y modos; no invoca un modelo ni convierte ejemplos declarativos en evidencia de comportamiento real.

## Validación

```powershell
python "<skill-root>/scripts/solution_baseline.py" validate --kind blueprint --file <archivo>
python "<skill-root>/scripts/solution_baseline.py" validate --kind run --file <archivo>
python "<skill-root>/scripts/solution_baseline.py" validate --kind receipt --file <archivo>
python "<skill-root>/scripts/solution_baseline.py" validate --kind result --file <archivo>
python "<skill-root>/scripts/solution_baseline.py" validate --kind adapter --file "<skill-root>/adapters/registry.json"
python "<skill-root>/scripts/solution_baseline.py" validate --kind handoff --file <repo>/.solution-baseline/vulcano-handoff.yaml
python "<skill-root>/scripts/solution_baseline.py" validate --kind gap --file resources/.solution-baseline/architecture-gaps/<gap-id>.yaml --strict
```

Usa `--strict` antes de renderizar o aplicar. Las plantillas de ejemplo pueden contener evidencia pendiente o digests ilustrativos y solo deben superar validación estructural hasta que se resuelvan.
