---
id: HU-06
type: Historia de Usuario
epic: 010
priority: Alta
points: 5
---

# HU-06: Degradación elegante ante falta de soporte, errores y conectividad limitada

## Como
Productor o técnico de campo

## Quiero
Que, si el navegador no soporta voz, no hay conexión o falla la transcripción, el sistema me informe y me permita seguir escribiendo

## Para
No quedarme bloqueado en campo

## Criterios de Aceptación
- [ ] CA1: En un navegador sin soporte de captura, el botón se oculta o deshabilita con un mensaje claro.
- [ ] CA2: Ante conectividad baja o nula, se informa el problema y el chat escrito permanece disponible.
- [ ] CA3: El flujo de escritura y las consultas rápidas existentes se mantienen intactos.
- [ ] CA4: Un fallo del servicio de voz nunca afecta el envío de texto al chat.
