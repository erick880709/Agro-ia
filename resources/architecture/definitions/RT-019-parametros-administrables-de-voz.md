# RT-019: Parámetros administrables de voz

**Tipo:** Requisito técnico
**Categoría:** Configuración
**Fuente:** RFP-AGROIA-001 — Secciones 7 (RF-12, RF-15) y 9.2

## Descripción
Los parámetros de duración máxima, activación e idioma deben poder administrarse y no quedar fijos en el código. La activación desde Administración → Parámetros se plantea como función deseable.

## Criterio medible / restricción concreta
Duración máxima, activación e idioma se identifican como parámetros administrables. No se especifica mecanismo de configuración ni si todos deben ser editables por el administrador.

## Impacto en la arquitectura
La configuración debe poder cambiarse sin modificar el código; su mecanismo debe alinearse con la administración existente de AgroIA.

## Notas del analista
La inclusión del control administrativo de activación en Fase 1 está abierta y debe confirmarse. La exigencia de no fijar parámetros en el código sí aparece en los lineamientos técnicos.
