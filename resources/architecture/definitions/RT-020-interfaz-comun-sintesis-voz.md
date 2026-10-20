# RT-020: Interfaz común de síntesis de voz

**Tipo:** Requisito técnico
**Categoría:** Integración
**Fuente:** RFP-AGROIA-002 — Secciones 8, 10 y 15

## Descripción
Definir un servicio de voz con una operación única "texto → audio" (interfaz común de síntesis) para intercambiar motores sin modificar el chat.

## Criterio medible / restricción concreta
Una interfaz común con operación de síntesis; los motores (navegador, nube, autoalojados) la implementan de forma intercambiable.

## Impacto en la arquitectura
Permite la cadena de respaldo (RT-021) y la conmutación en caliente de motores sin tocar el chat ni el agente.

## Notas del analista
El RFP sugiere la operación "texto → audio"; el contrato debe definir entrada (texto limpio, voz, velocidad) y salida (audio streaming o fragmentos).
