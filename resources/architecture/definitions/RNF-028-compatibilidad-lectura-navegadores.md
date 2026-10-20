# RNF-028: Compatibilidad de navegadores y dispositivos

**Tipo:** Requerimiento no funcional
**Categoría:** Compatibilidad
**Fuente:** RFP-AGROIA-002 — Secciones 8, 12 y 15

## Descripción
La función de lectura debe validarse en los navegadores y dispositivos soportados por AgroIA, con matriz de pruebas obligatoria.

## Criterio medible / restricción concreta
Matriz de pruebas por dispositivo y navegador con resultados. El RFP no enumera navegadores ni versiones (se heredan del soporte de AgroIA).

## Impacto en la arquitectura
La síntesis en el navegador (`speechSynthesis`) varía por dispositivo y sistema operativo; la matriz debe cubrir estas variaciones y el respaldo en servidor.

## Notas del analista
La lista de navegadores soportados por AgroIA (Chrome, Edge, Safari, Firefox — últimas 2 versiones) debe confirmarse, como en RNF-015.
