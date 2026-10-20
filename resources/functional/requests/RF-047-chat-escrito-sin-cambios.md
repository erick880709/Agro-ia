# RF-047: Mantener sin cambios la respuesta escrita y el chat

**Tipo:** Requerimiento funcional
**Fuente:** RFP-AGROIA-002 — Secciones 4.1, 7 (RF-10) y 12
**Prioridad:** Mandatoria (M)

## Descripción
La incorporación de la lectura en voz alta no debe alterar la respuesta escrita ni el flujo actual del chat: el texto sigue mostrándose como hoy y el agente no cambia.

## Actores involucrados
- Productor / agricultor
- Técnico / extensionista

## Criterios de aceptación
- La respuesta escrita y el funcionamiento actual del chat permanecen sin cambios.

## Dependencias / relacionados
- RF-041: Lectura automática
- RF-048: Conmutación a motor de respaldo

## Notas del analista
Requisito de no regresión explícito; aplica tanto al contenido como al comportamiento del endpoint de chat existente (RFP-AGROIA-001).
