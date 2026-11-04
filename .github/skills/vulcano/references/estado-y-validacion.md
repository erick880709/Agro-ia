# Estado persistente y validación

## Índice

- [Cuándo leer](#cuándo-leer-esta-referencia)
- [Manifiesto](#manifiesto)
- [Reconciliación](#reconciliación)
- [Validador](#validador)

## Cuándo leer esta referencia

Leer al iniciar o reanudar Vulcano, después de confirmar una decisión transversal y antes del
cierre. El manifiesto complementa los documentos; nunca sustituye la evidencia del repositorio.

## Manifiesto

Crear `{resources_root}/.vulcano/manifest.yaml` (siendo `{resources_root}` la carpeta de
trabajo confirmada en la Fase 0.0 del `SKILL.md` — `resources/` por defecto) copiando
`assets/manifest.template.yaml` y completar sus valores. El esquema mínimo es:

```yaml
schema_version: 1
project: "nombre"
updated_at: "YYYY-MM-DD"
resources_root: "resources"
baseline:
  sources: []
  cloud_providers: []
  services: []
  environments: []
constraints:
  compliance: []
  corporate_tools: []
  budget: null
decisions:
  cloud_provider: null
  devops_platform: null
  iac: null
  terraform:
    required_version: null
    provider_constraints: {}
    module_standard: null
    execution_backend: null
    test_strategy: null
    registry_source: null
    registry_mcp: null
    adoption_mode: null
  observability: null
  artifact_registry: null
  workload_identity: null
files: {}
assumptions: []
pending_decisions:
  - id: PD-001
    owner: plataforma
    exit_criteria: "Confirmar la decisión y actualizar los documentos afectados"
intentional_omissions: []
validation:
  last_run: null
  errors: 0
  warnings: 0
```

Cada entrada de `files` usa un `logical_id` estable como clave. Registrar los 26 IDs definidos
por `orden-y-dependencias.md`; `iac-structure` puede apuntar a `04-terraform-structure.md`,
`04-pulumi-structure.md` u otro nombre confirmado, conservando el prefijo `04-`:

```yaml
files:
  iac-structure:
    path: infrastructure-as-code/04-pulumi-structure.md
    status: generated
    mode: greenfield
    sources: ["resources/architecture/10.1-Arquetipo-de-Solucion_ACME.md @ sha256:<hash> @ aprobado"]
    owner: plataforma
    validated_at: "YYYY-MM-DD"
    summary: "Estructura Pulumi por stacks"
  tracing:
    path: observability/03-tracing.md
    status: omitted
    mode: null
    reason: "Monolito sin llamadas distribuidas"
```

Usar `status` (`pending`, `generated`, `existing`, `omitted`). Solo `generated` y `existing`
exigen archivo físico; `omitted` exige `reason`. Representar un pendiente aceptado como
`[PENDIENTE DE DEFINIR: PD-001]` y registrar ese ID con `owner` y `exit_criteria`. No guardar
secretos, tokens, connection strings, datos personales ni credenciales.

Para fuentes Archi materiales, cada texto de `sources` registra ruta, versión o SHA-256 y
estado (`aprobado`, `aprobado con condiciones` o `borrador`) siguiendo
`references/contrato-handoff-archi.md`. No trates un borrador como decisión aprobada.

## Reconciliación

1. Leer manifiesto, arquitectura, documentos Vulcano y evidencia del repositorio.
2. Considerar código/configuración actual como fuente de hechos observables.
3. Considerar el manifiesto como fuente de intención, decisiones pendientes y omisiones.
4. Informar contradicciones; no sobrescribir decisiones silenciosamente.
5. Actualizar el manifiesto después de cada decisión o archivo confirmado.

## Validador

Ejecutar desde la raíz. Por defecto el validador busca la carpeta `resources/` dentro de
`--root` (la raíz del workspace si no se indica `--root`):

```powershell
node .claude/skills/vulcano/scripts/validate-vulcano.mjs
# En el cierre, exigir los 26 logical_id:
node .claude/skills/vulcano/scripts/validate-vulcano.mjs --strict-completeness
```

Si `resources_root` (Fase 0.0 del `SKILL.md`) no es `resources/` en la raíz — por ejemplo, un
subproyecto de monorepo o una carpeta con otro nombre — apunta directo a esa carpeta con
`--resources-dir` (ruta absoluta o relativa al cwd; ignora `--root`):

```powershell
node .claude/skills/vulcano/scripts/validate-vulcano.mjs --resources-dir services/auth/resources --strict-completeness
```

Requisito: Python 3 con PyYAML disponible para parsear el manifiesto y los frontmatters.
Errores bloqueantes:
manifiesto ausente en modo estricto; frontmatter o YAML inválido; `resources_root` distinto de
la carpeta validada; ruta absoluta, duplicada o fuera de esa raíz; estado/modo desconocido o
modo distinto entre manifiesto y documento; pendiente sin ID registrado; archivo
`generated`/`existing` ausente; omisión sin razón; secreto probable; marcador semántico de
plantilla sin completar (checkboxes, índices de arrays, links y nodos Mermaid son válidos);
`06-ci-cd.md` sin inspección continua, métricas completas o política de deuda técnica; métrica
DORA ausente o con campos obligatorios vacíos; alerta alta/crítica sin `07-runbooks.md` o
sin el mismo ID; nombres u orden de promoción distintos entre DevOps `05-environments.md` e
IaC `02-environments.md`; o Mermaid
que no compila cuando Mermaid CLI está disponible.

Con `--strict-completeness`, exigir además que las rutas usen el prefijo canónico de su carpeta,
`validation.last_run/errors/warnings`, `01-devops-index.md` con enlaces a todos los documentos
`generated`/`existing`, y `02-madurez-devsecops.md` con sus secciones obligatorias.

Warnings: links locales rotos, manifiesto ausente durante una sesión parcial, logical IDs
faltantes sin modo estricto o Mermaid no compilado porque Mermaid CLI no está disponible. Un
warning puede aceptarse solo con justificación registrada.
