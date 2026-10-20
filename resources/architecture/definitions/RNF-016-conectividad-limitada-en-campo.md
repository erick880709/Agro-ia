# RNF-016: Degradación ante conectividad limitada

**Tipo:** Requerimiento no funcional
**Categoría:** Disponibilidad
**Fuente:** RFP-AGROIA-001 — Secciones 6, 8, 11, 12 y 13

## Descripción
Ante conectividad baja o nula, la aplicación debe informar claramente el problema y conservar, cuando sea posible, el uso del chat escrito.

## Criterio medible / restricción concreta
No se especifican condiciones de red ni un modo offline obligatorio. Se requiere un mensaje claro y tolerancia a fallos sin impedir la escritura.

## Impacto en la arquitectura
El flujo de voz debe detectar y comunicar errores de conexión sin introducir dependencias que bloqueen la interacción escrita.

## Notas del analista
El RFP no establece si las consultas dictadas deben recuperarse o conservarse tras una interrupción de red.
