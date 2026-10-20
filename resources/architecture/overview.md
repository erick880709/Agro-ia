# AgroIA — Documentos vivos de arquitectura y diseño

> Generado por `genesis` a partir de `Documento_Arquitectura_AgroIA.md`.
> `builder` debe actualizar estos archivos incrementalmente, no regenerarlos desde cero.

## Índice de documentos

| Documento | Propósito |
|-----------|----------|
| [../functional/catalogo-funcional-agroia.md](../functional/catalogo-funcional-agroia.md) | Inventario funcional detallado de la SPA, los perfiles, los procesos agrícolas y las capacidades administrativas |
| [Documento_Menus_Pantallas_AgroIA.md](Documento_Menus_Pantallas_AgroIA.md) | Navegación de la aplicación y descripción de pantallas por perfil |
| [Documento_Funcional_Tecnico_AgroIA.md](Documento_Funcional_Tecnico_AgroIA.md) | Funcionamiento técnico, servicios y motor de recomendaciones |
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
- **Voz (2026-10-19, RFP-AGROIA-001):** `api/voz.py` (transcripción en servidor, parámetros y
  métricas), `services/transcripcion.py` (proveedor intercambiable), `models/parametro_voz.py`
  y `models/metrica_voz.py`. Frontend en `apps/frontend-web/voz.js` (Web Speech API por
  defecto + respaldo en servidor). Variación: la transcripción es híbrida — la mayor parte de
  la lógica vive en el cliente y el servidor solo provee respaldo; el audio nunca se persiste.
