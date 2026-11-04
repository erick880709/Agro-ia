# RNF-034: Compatibilidad y migraciones reversibles

**Tipo:** Requerimiento no funcional
**Categoría:** Compatibilidad
**Fuente:** RFP-AGROIA-003 §7 (Requerimientos no funcionales)

## Descripción
Las migraciones Alembic deben ser reversibles; las lecturas históricas se reclasifican con un proceso por lotes, sin borrar nada.

## Criterio medible / restricción concreta
Reclasificación histórica sin pérdida de registros.

## Impacto en la arquitectura
Principio 1 del RFP: el valor crudo se conserva siempre.

## Notas del analista
No aplican — el RFP define el requisito de forma concreta.
