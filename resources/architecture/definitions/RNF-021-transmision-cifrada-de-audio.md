# RNF-021: Transmisión cifrada de audio

**Tipo:** Requerimiento no funcional
**Categoría:** Seguridad
**Fuente:** RFP-AGROIA-001 — Secciones 9.2 y 10

## Descripción
Cualquier audio que se transmita para su procesamiento debe enviarse por un canal cifrado HTTPS.

## Criterio medible / restricción concreta
HTTPS es obligatorio para la transmisión de audio. No se especifican versiones de TLS ni una política criptográfica.

## Impacto en la arquitectura
Si se elige procesamiento en servidor, el endpoint y las comunicaciones con el servicio de transcripción deben usar HTTPS.

## Notas del analista
La alternativa de reconocimiento del navegador también debe evaluarse según el tratamiento del audio por el proveedor del navegador.
