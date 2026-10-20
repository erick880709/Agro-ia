# RF-056: Métricas de uso de la lectura sin guardar audio

**Tipo:** Requerimiento funcional
**Fuente:** RFP-AGROIA-002 — Secciones 7 (RF-19) y 10
**Prioridad:** Deseable (D)

## Descripción
La plataforma debe registrar métricas de uso de la función de lectura — activaciones, voz elegida, errores y caracteres leídos — sin guardar el contenido del audio de las respuestas.

## Actores involucrados
- Administrador (consulta las métricas)
- Productor / agricultor y técnico (generan los eventos)

## Criterios de aceptación
- Se registran activaciones, voz elegida, errores y caracteres leídos.
- No se guarda contenido de audio de las respuestas.

## Dependencias / relacionados
- RT-022: Control de cuota
- RNF-030: Costos

## Notas del analista
"Caracteres leídos" es la métrica base para el control de cuota de los motores en la nube (las capas gratuitas se miden en caracteres). El RFP no especifica retención ni agregación.
