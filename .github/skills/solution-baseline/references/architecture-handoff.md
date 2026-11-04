# Handoff de brechas a arquitectura

`solution-baseline` materializa decisiones aprobadas; no inventa topología, límites, ownership, contratos públicos, modelo de seguridad, estilo o stack cuando esas decisiones faltan o se contradicen.

## Cuándo devolver control a `archi`

Emite un `architecture-gap` cuando una decisión pendiente cambiaría materialmente uno o más de estos elementos:

- topología o separación de repositorios;
- límites y responsabilidades de componentes;
- ownership de datos, APIs o eventos;
- contratos públicos o compatibilidad;
- trust boundaries, autenticación o controles de seguridad;
- estilo arquitectónico o stack obligatorio.

La ausencia de un arquetipo publicado no es por sí misma una brecha arquitectónica. Si la arquitectura define suficientemente el estado deseado, `solution-baseline` decide entre reutilizar, componer, crear un candidato reusable o producir una baseline específica.

## Artefacto

Crea `resources/.solution-baseline/architecture-gaps/<gap-id>.yaml` desde `architecture-gap.template.yaml`, valídalo con `--kind gap --strict` y añádelo a `run-manifest.architecture_gaps`. Agrega su ruta a `handoff.archi`.

Un gap abierto bloquea únicamente los componentes afectados. El trabajo independiente puede continuar. Para reanudar, `archi` debe registrar una resolución, actualizar o enlazar la fuente arquitectónica aprobada y cambiar el estado a `resolved` o `accepted`.

No aceptes una respuesta informal como resolución definitiva si no deja una fuente trazable.
