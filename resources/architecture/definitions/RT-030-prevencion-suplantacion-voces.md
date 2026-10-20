# RT-030: Prevención de suplantación y aislamiento de voces

**Tipo:** Requisito técnico
**Categoría:** Seguridad
**Fuente:** RFP-AGROIA-002 — Secciones 11, 12 y 14

## Descripción
Prevenir la suplantación: verificación de voz propia en el momento de la grabación (frase leída en vivo), prohibir audios de terceros, no compartir voces entre usuarios, no exponer la voz personalizada por API pública y aplicar marcas de agua cuando el modelo lo soporte.

## Criterio medible / restricción concreta
Verificación de voz propia, aislamiento por usuario y ausencia de API pública para la voz personalizada. El RFP no define el método biométrico de verificación.

## Impacto en la arquitectura
Aislamiento estricto por usuario de muestras y voces; control de acceso a los artefactos; marca de agua de audio si el motor lo soporta.

## Notas del analista
Mitiga el riesgo "suplantación o uso indebido de voces" (alto, sección 14). La marca de agua está disponible en Chatterbox (G) y debe validarse en el motor elegido.
