# RF-033: Degradación cuando el navegador no soporte captura de voz

**Tipo:** Requerimiento funcional
**Fuente:** RFP-AGROIA-001 — Secciones 4.1, 7 (RF-11) y 11
**Prioridad:** Mandatoria (M)

## Descripción
Si el navegador no soporta la captura de voz, el sistema debe ocultar o deshabilitar el botón de micrófono e informar al usuario de la limitación, sin afectar el chat escrito.

## Actores involucrados
- Productor / agricultor
- Técnico / extensionista

## Criterios de aceptación
- En un navegador sin soporte, el botón se oculta o deshabilita y se muestra un mensaje.
- El flujo escrito permanece disponible.

## Dependencias / relacionados
- RF-032: Continuidad del chat escrito y consultas rápidas
- RNF-015: Compatibilidad de navegadores y dispositivos

## Notas del analista
El RFP permite ocultar o deshabilitar el botón, dejando la elección visual a diseño e implementación.
