# RF-024: Iniciar y detener la grabación

**Tipo:** Requerimiento funcional
**Fuente:** RFP-AGROIA-001 — Secciones 4.1, 6 y 7 (RF-02)
**Prioridad:** Mandatoria (M)

## Descripción
El usuario debe poder iniciar y detener la captura de voz desde el chat. La captura finaliza también al detectarse silencio, según el flujo esperado descrito en el RFP.

## Actores involucrados
- Productor / agricultor
- Técnico / extensionista

## Criterios de aceptación
- El usuario puede iniciar y detener la grabación.
- Tras detenerse la captura o finalizar por silencio, la interfaz pasa a procesar la transcripción.

## Dependencias / relacionados
- RF-023: Botón de captura de voz
- RF-031: Estados de captura y procesamiento
- RNF-013: Tiempo de transcripción

## Notas del analista
El umbral de silencio y el comportamiento exacto de detección automática no están definidos.
