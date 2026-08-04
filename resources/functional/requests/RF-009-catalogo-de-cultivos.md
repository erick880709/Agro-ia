# RF-009: Catálogo de Cultivos

**Tipo:** Requerimiento funcional
**Fuente:** RFP-AgroInteligente-Colombia.md — Sección 5.7
**Prioridad:** Alta

## Descripción
El sistema debe mantener un catálogo de cultivos con fichas técnicas detalladas. Cada ficha técnica de cultivo debe contener como mínimo:

- Nombre común y nombre científico
- Familia botánica
- Temperatura ideal (rango)
- Humedad ideal del suelo y ambiental (rango)
- pH ideal del suelo (rango)
- Requerimientos de N-P-K y Calcio (valores de referencia)
- Altitud recomendada (msnm)
- Tipo de suelo recomendado
- Tiempo de cosecha (días/meses)
- Enfermedades y plagas frecuentes
- Producción esperada (ton/ha)
- Mercados objetivo
- Rentabilidad estimada

El catálogo debe ser administrable (crear, editar, desactivar cultivos) por el Administrador y debe servir como base de referencia para los modelos de IA, especialmente el Modelo 2 (predicción del cultivo ideal) y el sistema de recomendaciones.

## Actores involucrados
- Administrador — gestiona el catálogo de cultivos
- Técnico Agrónomo — valida y revisa las fichas técnicas
- Cliente — consulta fichas técnicas desde el dashboard y reportes

## Criterios de aceptación
- Se puede crear, editar, consultar y desactivar una ficha técnica de cultivo.
- Cada ficha contiene todos los campos mínimos especificados.
- Los valores de referencia provienen de fuentes oficiales verificables (Cenicafé, UPRA, FAO GAEZ, AGROSAVIA).
- No especificados en el RFP — definir: ¿quién valida la veracidad de las fichas técnicas?, ¿proceso de aprobación antes de publicar una ficha nueva?, ¿cultivos iniciales precargados?

## Dependencias / relacionados
- RF-010: Motor de conocimiento agronómico
- RF-012: Motor predictivo (Modelo 2)
- RD-007: Estructura de ficha técnica
- Anexo-Datasets-Fuentes-Datos.md: fuentes de umbrales agronómicos

## Notas del analista
- Para el piloto inicial en café del Quindío, Cenicafé es la fuente primaria de verdad agronómica. Su biblioteca digital contiene guías de fertilidad y nutrición del café con umbrales validados.
- Para cultivos sin ficha oficial colombiana, se puede usar FAO/IIASA GAEZ como baseline internacional.
- La UPRA ya tiene zonificaciones de aptitud publicadas para varios cultivos (café incluido). Se recomienda adoptar sus criterios de clasificación como estándar.
