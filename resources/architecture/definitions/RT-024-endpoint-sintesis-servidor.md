# RT-024: Endpoint de síntesis en servidor

**Tipo:** Requisito técnico
**Categoría:** Integración
**Fuente:** RFP-AGROIA-002 — Sección 10

## Descripción
Si la voz se genera en servidor, exponer un endpoint autenticado con límite de tamaño, tasa de peticiones y tiempo de espera; el audio se devuelve por transmisión (streaming) o en fragmentos.

## Criterio medible / restricción concreta
Endpoint autenticado con límites de tamaño, tasa de peticiones y timeout; salida streaming o por fragmentos.

## Impacto en la arquitectura
Nuevo endpoint de síntesis protegido (JWT), con control de abuso y entrega incremental de audio para respuestas largas.

## Notas del analista
El RFP no define el contrato exacto del endpoint ni si se reutiliza la autenticación existente (JWT); debe alinearse con RT-018/RT-006 de RFP-AGROIA-001.
