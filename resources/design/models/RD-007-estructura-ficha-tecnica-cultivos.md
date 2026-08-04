# RD-007: Estructura de Ficha Técnica de Cultivos

**Tipo:** Información de diseño
**Fuente:** RFP-AgroInteligente-Colombia.md — Sección 5.7; Anexo-Datasets-Fuentes-Datos.md — Secciones 3, 4, 6

## Descripción
Cada cultivo en el catálogo debe tener una ficha técnica estructurada con los siguientes campos y fuentes recomendadas:

### Identificación del cultivo
- **Nombre común:** ej. "Café Arábica"
- **Nombre científico:** ej. *Coffea arabica*
- **Familia botánica:** ej. Rubiaceae

### Requerimientos edafoclimáticos (con umbrales numéricos)
- **Temperatura ideal:** rango en °C → Fuente: Cenicafé (café: 18–24°C)
- **Humedad del suelo ideal:** rango en % → Fuente: Cenicafé (café: 60–80% capacidad de campo)
- **pH ideal:** rango → Fuente: Cenicafé (café: 5.5–6.5)
- **Altitud recomendada:** rango en msnm
- **Tipo de suelo recomendado:** clasificación
- **Requerimientos de N-P-K:** valores de referencia en kg/ha
- **Requerimiento de Calcio:** valor de referencia

### Información agronómica
- **Tiempo de cosecha:** días/meses desde la siembra
- **Producción esperada:** ton/ha → Fuente: DANE-EVA (históricos municipales)
- **Enfermedades y plagas frecuentes:** lista con condiciones que las favorecen → Fuente: Cenicafé, AGROSAVIA
- **Compatibilidad y rotación:** cultivos compatibles para rotación/asociación

### Información económica
- **Mercados objetivo:** nacional / exportación
- **Precio de referencia:** COP/ton → Fuente: DANE-SIPSA
- **Costo de producción estimado:** COP/ha
- **Rentabilidad estimada:** margen

### Fuentes de datos recomendadas por cultivo
| Cultivo | Fuente primaria | Fuente secundaria |
|---|---|---|
| Café | Cenicafé (biblioteca técnica) | FAO GAEZ (rendimiento potencial) |
| Otros cultivos colombianos | UPRA (zonificaciones) | AGROSAVIA, FAO GAEZ |
| Cultivos sin ficha colombiana | FAO GAEZ v4/v5 | SoilGrids + literatura internacional |

## Elementos de referencia
- Esta estructura debe modelarse en la base de datos PostgreSQL como una tabla `cultivos` con columnas para cada campo, más una tabla relacionada `cultivo_umbrales` para los rangos (mínimo, óptimo, máximo).
- La ficha técnica es la base contra la cual se comparan las mediciones de sensores para determinar la aptitud del suelo (RF-013).

## Notas del analista
- Para el MVP con piloto en café, la ficha técnica de café debe ser la más completa y validada por Cenicafé. Las demás fichas pueden poblarse progresivamente.
- Los umbrales deben tener un identificador de fuente verificable (ej. "Cenicafé, 2007, Guía de fertilidad del suelo") para trazabilidad.
- La estructura debe ser extensible: permitir agregar nuevos campos sin migraciones destructivas (usar JSONB para campos específicos por cultivo).
