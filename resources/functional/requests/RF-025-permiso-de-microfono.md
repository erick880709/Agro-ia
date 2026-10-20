# RF-025: Solicitud y orientación del permiso de micrófono

**Tipo:** Requerimiento funcional
**Fuente:** RFP-AGROIA-001 — Secciones 4.1, 6, 7 (RF-03) y 11
**Prioridad:** Mandatoria (M)

## Descripción
La aplicación debe solicitar el permiso de micrófono únicamente cuando el usuario active la función de voz. Si el permiso se deniega, debe explicar cómo habilitarlo y mantener disponible la entrada escrita.

## Actores involucrados
- Productor / agricultor
- Técnico / extensionista

## Criterios de aceptación
- La aplicación solicita el permiso al activar la captura.
- Si se deniega, orienta al usuario para habilitarlo y permite continuar escribiendo.

## Dependencias / relacionados
- RF-023: Botón de captura de voz
- RF-032: Continuidad del flujo de escritura
- RNF-016: Conectividad y degradación de la función

## Notas del analista
El RFP no especifica el texto de ayuda ni diferencias de presentación entre navegadores.
