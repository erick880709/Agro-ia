# RF-032: Continuidad del chat escrito y consultas rápidas

**Tipo:** Requerimiento funcional
**Fuente:** RFP-AGROIA-001 — Secciones 4.1, 6, 7 (RF-10) y 11
**Prioridad:** Mandatoria (M)

## Descripción
La incorporación de voz debe mantener sin cambios el flujo de escritura y las consultas rápidas existentes. Los fallos de permiso, conectividad o transcripción no deben impedir que el usuario envíe una consulta escrita.

## Actores involucrados
- Productor / agricultor
- Técnico / extensionista

## Criterios de aceptación
- El chat conserva intactos su funcionamiento de escritura y sus consultas rápidas.
- Ante fallos de la función de voz, el usuario puede seguir escribiendo.

## Dependencias / relacionados
- RF-025: Solicitud y orientación del permiso de micrófono
- RF-033: Compatibilidad de captura en navegador
- RNF-014: Aislamiento de fallos del servicio de voz
- RNF-016: Conectividad y degradación de la función

## Notas del analista
No se especifica un mecanismo de trabajo sin conexión; el requisito pide comunicar el problema y conservar el flujo escrito cuando sea posible.
