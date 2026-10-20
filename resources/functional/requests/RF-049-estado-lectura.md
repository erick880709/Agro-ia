# RF-049: Informar el estado de la lectura

**Tipo:** Requerimiento funcional
**Fuente:** RFP-AGROIA-002 — Secciones 7 (RF-12) y 4.1
**Prioridad:** Mandatoria (M)

## Descripción
La interfaz debe informar el estado de la lectura: preparando audio, reproduciendo y error.

## Actores involucrados
- Productor / agricultor
- Técnico / extensionista

## Criterios de aceptación
- Se indica visualmente cuándo se está preparando el audio, reproduciendo o hay un error.

## Dependencias / relacionados
- RF-041: Lectura automática
- RF-043: Controles de reproducción
- RNF-025: Accesibilidad de controles

## Notas del analista
El estado debe cumplir los criterios de accesibilidad (no depender solo del color) y ser visible mientras dura la síntesis (la preparación puede tardar si se usa un motor en la nube).
