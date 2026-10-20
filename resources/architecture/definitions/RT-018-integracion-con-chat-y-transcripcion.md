# RT-018: Integración con el chat y el servicio de transcripción

**Tipo:** Requisito técnico
**Categoría:** Integración
**Fuente:** RFP-AGROIA-001 — Secciones 9.2 y 10

## Descripción
La consulta transcrita debe reutilizar el endpoint de chat existente y llegar como texto, indistinguible de una consulta escrita. No se debe modificar el agente ni las reglas UPRA/Cenicafé/AGROSAVIA. Si se crea un endpoint de transcripción, debe exigir autenticación, limitar tamaño y duración del audio y aplicar tasa de peticiones.

## Criterio medible / restricción concreta
Reutilización del endpoint de chat; autenticación y límites de tamaño, duración y frecuencia obligatorios para cualquier nuevo endpoint de transcripción.

## Impacto en la arquitectura
El backend debe recibir cambios mínimos o nulos según la alternativa seleccionada. Un endpoint nuevo añade obligaciones de autenticación, protección frente a abuso y manejo transitorio de audio.

## Notas del analista
No se define el contrato del endpoint de transcripción, porque su creación depende de la alternativa técnica que se elija.
