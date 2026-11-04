# Brownfield

## Regla principal

El repositorio existente es evidencia y contiene trabajo propiedad del proyecto. Inspecciona, clasifica y propone parches mínimos; no regeneres encima de él.

## Tres estados

Compara:

1. Ancestro conocido: arquetipo y receipt previos, si existen.
2. Estado deseado: nueva versión renderizada desde blueprint y catálogo.
3. Estado actual: repositorio con personalizaciones y drift.

Si no hay receipt, crea un baseline inferido sin adjudicar ownership al generador. Todo archivo se considera `project_owned` hasta que una revisión explícita lo clasifique.

## Ownership

| Categoría | Política |
|---|---|
| `managed` | Regenerar solo sin drift conflictivo o con resolución aprobada |
| `extendable` | Cambiar únicamente puntos de extensión declarados con transformación semántica |
| `project_owned` | No sobrescribir automáticamente |
| `generated_once` | Crear si falta; después pertenece al proyecto |
| `ignored` | No inspeccionar o modificar salvo validación explícita |

## Reconciliación

1. Detecta stack, comandos y comportamiento actual.
2. Calcula inventario y hashes; localiza receipt si existe.
3. Mapea arquitectura vigente contra código y reporta contradicciones.
4. Renderiza el estado deseado fuera del repo.
5. Calcula diff de tres vías y clasifica cambios.
6. Propón parches; usa AST/parsers para código cuando estén disponibles.
7. Conserva funcionalidades observables aunque un roadmap histórico las omita.
8. Aplica solo cambios revisados y ejecuta regresión relevante.
9. Registra drift aceptado, deuda y ownership en el receipt.

Detén únicamente el componente conflictivo. No uses eliminación/reescritura masiva como método de reconciliación.

## Deuda pre-existente no es lo mismo que "validado"

Un `reconcile` que encuentra lint/build/tests ya rotos o boundaries de
arquitectura sin cobertura real puede documentarlos como `accepted_drift`
con handoff a `builder` sin corregirlos en el mismo run — eso es correcto,
no reescribas código de negocio brownfield sin revisión. Lo que no es
correcto es registrar ese componente como `status: validated`/`completed`
en el run manifest mientras esos gates sigan en rojo: usa `status: partial`.
Antes de cerrar el receipt, corre también
[`check-gate-coverage` y `check-boundary-coverage`](./quality-gates-and-handoff.md#trazabilidad-de-quality-gates-declarados)
— un `reconcile` que no toca `eslint.config.js`/config equivalente porque es
`project_owned` puede dejar una lista de boundary ya desincronizada de las
carpetas reales sin que nada lo señale.

