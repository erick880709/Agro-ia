# Estado persistente y reconciliación

Leer esta referencia al iniciar, reanudar y cerrar una generación.

## Índice

- [Manifiesto de Bob](#manifiesto-de-bob)
- [Hashes de fuentes](#hashes-de-fuentes)
- [Reconciliación](#reconciliación)
- [Automatización de estado](#automatización-de-estado)
- [Validador](#validador)

## Manifiesto de Bob

Crear `resources/.vulcano/bob-manifest.yaml` desde
`assets/bob-manifest.template.yaml`. No modificar el manifiesto de Vulcano para guardar estado de
implementación.

El esquema vigente es `schema_version: 4` y se describe además en
`assets/bob-manifest.schema.json`:

- `source_snapshot`: decisiones de herramienta y fecha del manifiesto fuente observadas durante
  el preflight.
- `adapter_selection`: IDs canónicos de nube, IaC y pipeline, estado de implementación y operador
  remoto. Debe coincidir con la resolución del registro; no se edita a mano.
- `terraform_profile`: copia exacta de `decisions.terraform`; fija versiones, providers, estándar,
  pruebas, Registry/MCP y adopción sin que Bob los redecida.
- `preflight.status`: `pending`, `ready` o `blocked`.
- `preflight.capabilities`: disponibilidad comprobada de skills HashiCorp y Terraform MCP.
- `preflight.conflicts`: contradicciones concretas; cada una contiene `id`, `description`,
  `source_docs` y `affected_artifacts`.
- `artifacts`: catálogo de archivos físicos. Una ruta física aparece una sola vez.
- `depends_on`: grafo acíclico de implementación.
- `contract.inputs`/`contract.outputs`: interfaz verificable de cada artefacto.
- `source_hashes`: SHA-256 de cada documento al marcar un artefacto `generated`.
- `operational_pending`: datos no arquitectónicos con ID `OP-NNN`.
- `validation`: resultado del último cierre real.

Estados de artefacto:

| Estado | Uso |
|---|---|
| `pending` | Aún no existe o no está validado. |
| `generated` | Existe, no tiene placeholders, coincide con sus fuentes y fue validado. |
| `conflict` | La fuente o el código contradicen el contrato. Siempre bloquea dependientes. |
| `omitted` | No aplica; exige `reason`. |

No guardar secretos, tokens, credenciales ni connection strings en el manifiesto.

## Hashes de fuentes

Al generar un artefacto, calcular SHA-256 sobre el archivo completo y registrar el hash
hexadecimal de 64 caracteres:

```powershell
(Get-FileHash resources/infrastructure-as-code/06-modules.md -Algorithm SHA256).Hash.ToLower()
```

Usar como clave la misma ruta relativa incluida en `source_docs`. Si el hash cambia después, el
validador reporta drift y el artefacto vuelve a revisión; no se regenera silenciosamente.

## Reconciliación

1. El código real determina qué existe.
2. Los documentos de Vulcano determinan el diseño aprobado.
3. El manifiesto de Bob determina qué se generó y con qué snapshot.
4. Si código y documento difieren, marcar `conflict` antes de editar.
5. Si un documento cambió, volver a ejecutar el preflight y renovar hashes solo después de
   revisar el artefacto.
6. Un conflicto de arquitectura se corrige en Vulcano; Bob no altera el contrato para sortearlo.

## Automatización de estado

Inicializar sin sobrescribir un manifiesto existente:

```powershell
node .claude/skills/vulcano-bob/scripts/init-bob-manifest.mjs
```

Para un `bob-manifest.yaml` schema v3, migrar sin perder el catálogo ni sus estados. La migración
agrega `source_snapshot.cloud_provider`, `adapter_selection`, actualiza a schema v4 y vuelve el
preflight a `pending`:

```powershell
node .claude/skills/vulcano-bob/scripts/init-bob-manifest.mjs --migrate-adapters
```

Registrar un artefacto después de ejecutar sus validaciones reales:

```powershell
node .claude/skills/vulcano-bob/scripts/validate-and-record-bob-artifact.mjs `
  --logical-id module-networking
```

El script calcula hashes y fecha, verifica dependencias y rechaza rutas inexistentes. No usarlo
para fabricar resultados: `true` significa que el comando correspondiente se ejecutó y terminó en
cero; `skipped` exige que el cierre reporte la herramienta ausente.

Registrar capacidades sin guardar tokens ni respuestas MCP:

```powershell
node .claude/skills/vulcano-bob/scripts/record-bob-capability.mjs `
  --capability terraform_style_guide --status available
```

Generar el índice desde el mismo manifiesto, sin mantener una lista manual duplicada:

```powershell
node .claude/skills/vulcano-bob/scripts/generate-bob-index.mjs
```

## Validador

Validación normal:

```powershell
node .claude/skills/vulcano-bob/scripts/validate-vulcano-bob.mjs
```

Cierre, donde no se permiten `pending` ni `conflict`:

```powershell
node .claude/skills/vulcano-bob/scripts/validate-vulcano-bob.mjs --strict-completeness
```

Opciones para fixtures o diagnósticos:

```text
--root <ruta>           raíz del repositorio
--resources-dir <ruta> carpeta resources alternativa
--skip-tools            omite binarios externos; solo para pruebas no estrictas
```

La ausencia de cualquiera de los dos manifiestos es siempre un error. La ausencia de herramientas
opcionales produce warning; no se registra como validación exitosa.
