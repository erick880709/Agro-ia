# RF-052: Consentimiento explícito y verificación de voz propia

**Tipo:** Requerimiento funcional
**Fuente:** RFP-AGROIA-002 — Secciones 4.1, 6.2, 7 (RF-15) y 11
**Prioridad:** Plus (P — Fase 2)

## Descripción
Antes de grabar, la aplicación debe explicar qué se grabará, para qué se usará y por cuánto tiempo se conservará, y solicitar consentimiento explícito. Debe verificar que la voz grabada pertenece al propio usuario (frase de verificación leída en el momento), prohibiendo cargar audios de terceros.

## Actores involucrados
- Productor / agricultor
- Técnico / extensionista

## Criterios de aceptación
- La grabación exige consentimiento explícito e informado.
- Se verifica que la voz es la del propio usuario (frase de verificación).

## Dependencias / relacionados
- RF-051: Flujo de grabación
- RT-029: Privacidad y cumplimiento normativo
- RT-030: Prevención de suplantación

## Notas del analista
La verificación de identidad con una frase leída en vivo es una mitigación anti-suplantación; el RFP no especifica si hay verificación biométrica adicional. Requiere asesoría jurídica (dato biométrico).
