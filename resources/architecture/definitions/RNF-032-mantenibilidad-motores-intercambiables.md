# RNF-032: Mantenibilidad — motores de voz intercambiables

**Tipo:** Requerimiento no funcional
**Categoría:** Mantenibilidad
**Fuente:** RFP-AGROIA-002 — Secciones 8 y 10

## Descripción
Los motores de voz deben ser intercambiables detrás de una interfaz común y sus parámetros deben ser administrables (no fijos en código).

## Criterio medible / restricción concreta
Interfaz común de síntesis ("texto → audio") y parámetros administrables. El RFP no define métricas de modularidad.

## Impacto en la arquitectura
Servicio de voz con una operación única de síntesis; los motores (navegador, nube, autoalojados) implementan la misma interfaz para poder conmutarlos sin tocar el chat.

## Notas del analista
Equivalente a RT-019 (parámetros administrables de voz) de RFP-AGROIA-001; ambos módulos comparten el principio de intercambiabilidad.
