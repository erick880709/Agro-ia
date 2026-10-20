# RF-044: Control de velocidad de lectura

**Tipo:** Requerimiento funcional
**Fuente:** RFP-AGROIA-002 — Secciones 3, 4.1 y 7 (RF-07)
**Prioridad:** Deseable (D)

## Descripción
El usuario debe poder ajustar la velocidad de la lectura. El RFP sugiere valores como 0,75x, 1x, 1,25x y 1,5x.

## Actores involucrados
- Productor / agricultor
- Técnico / extensionista

## Criterios de aceptación
- Se ofrece un control de velocidad con al menos los valores sugeridos (0,75x, 1x, 1,25x, 1,5x).

## Dependencias / relacionados
- RF-043: Controles de reproducción
- RT-020: Interfaz común de síntesis

## Notas del analista
No todos los motores de voz permiten controlar la velocidad de forma nativa; puede requerirse re-síntesis o `speechSynthesis.rate` en el navegador. El RFP lo marca deseable.
