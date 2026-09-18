# AgroIA — Documentos vivos de arquitectura y diseño

> Generado por `genesis` a partir de `Documento_Arquitectura_AgroIA.md`.
> `builder` debe actualizar estos archivos incrementalmente, no regenerarlos desde cero.

## Índice de documentos

| Documento | Propósito |
|-----------|----------|
| [stack.md](stack.md) | Stack tecnológico por contenedor |
| [design/data-model.md](../design/data-model.md) | Modelo de datos (entidades y relaciones) |
| [design/api.md](../design/api.md) | Convenciones de API REST |
| [design/openapi.yaml](../design/openapi.yaml) | Contrato OpenAPI (acumulativo) |

## Módulos de referencia y variaciones

- CRUD con estados: `apps/backend/agroia_backend/api/comisiones.py` + `models/comision.py`.
- Cálculo puro: `apps/backend/agroia_backend/services/economia.py`.
- **AGC-COST (2026-09-18):** `services/costeo_motor.py` (motor puro, sin valores de negocio en
  código), `api/costeo.py`, `models/costeo.py`. Variación: el dominio vive en un catálogo de
  parámetros versionado (`costeo_*`); el código solo interpreta componentes y factores.
