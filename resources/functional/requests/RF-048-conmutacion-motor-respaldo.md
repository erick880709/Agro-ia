# RF-048: Conmutación a motor de respaldo de voz

**Tipo:** Requerimiento funcional
**Fuente:** RFP-AGROIA-002 — Secciones 4.1, 6.1, 7 (RF-11), 9.3 y 12
**Prioridad:** Mandatoria (M)

## Descripción
Si el motor de voz principal falla o agota su cuota, el sistema debe conmutar automáticamente a un motor de respaldo. Si ninguno está disponible, se muestra la respuesta de texto con un aviso breve, sin afectar el chat.

## Actores involucrados
- Productor / agricultor
- Técnico / extensionista
- Administrador (configura la cadena de motores)

## Criterios de aceptación
- Ante fallo o cuota agotada del motor principal, se conmuta al respaldo.
- Si no hay motor disponible, se muestra la respuesta de texto y se informa el problema brevemente.

## Dependencias / relacionados
- RT-021: Cadena de respaldo de motores
- RF-049: Informar estado de la lectura
- RF-047: Chat escrito sin cambios

## Notas del analista
La cadena recomendada por el solicitante es: navegador (A) → nube con capa gratuita (B/C) → Piper autoalojado (E) como contingencia.
