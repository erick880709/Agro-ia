# RNF-033: Trazabilidad de la medición

**Tipo:** Requerimiento no funcional
**Categoría:** Trazabilidad
**Fuente:** RFP-AGROIA-003 §7 (Requerimientos no funcionales)

## Descripción
Versión de regla, calibración y firmware asociadas a cada lectura; reproducibilidad de cualquier reporte (conservando la versión de regla vigente al momento de su emisión).

## Criterio medible / restricción concreta
Cada lectura y reporte deben poder reproducirse con la versión exacta de regla/calibración/firmware aplicada.

## Impacto en la arquitectura
Requiere `version_regla` y `motivos_calidad[]` en sensor_readings y versionado de parámetros (RD-011).

## Notas del analista
No aplican — el RFP define el requisito de forma concreta.
