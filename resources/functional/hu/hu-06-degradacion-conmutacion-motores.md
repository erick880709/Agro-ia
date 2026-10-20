---
id: HU-06
type: Historia de Usuario
epic: 011
priority: Alta
points: 5
---

# HU-06: Degradación y conmutación de motores

## Como
Productor o técnico de campo

## Quiero
Que, si el motor de voz falla o agota su cuota, la respuesta se lea con otro motor o se muestre en texto con un aviso

## Para
No quedarme sin respuesta

## Criterios de Aceptación
- [ ] CA1: Si el motor principal falla o agota su cuota, se conmuta al respaldo.
- [ ] CA2: Si no hay motor disponible, se muestra la respuesta de texto y se informa brevemente.
- [ ] CA3: La respuesta escrita y el chat permanecen sin cambios.
