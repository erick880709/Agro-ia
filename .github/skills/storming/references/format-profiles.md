# Perfiles de formato EventStorming

Seleccionar el formato más pequeño que permita alcanzar el objetivo. Encadenar formatos únicamente
cuando el siguiente necesite explícitamente el resultado del anterior.

## Matriz de decisión

| Señal principal | Formato recomendado |
|---|---|
| Línea de negocio completa, silos, perspectivas contradictorias, modernización amplia | `big-picture` |
| Proceso end-to-end específico, variantes, experiencia de stakeholders, rediseño operativo | `process-modelling` |
| Comportamiento de software crítico, agregados, invariantes, read models y límites | `software-design` |
| No se conoce todavía qué proceso merece profundización | `big-picture → process-modelling` |
| El proceso está comprendido pero falta diseño conductual | `process-modelling → software-design` |

No exigir Big Picture como prerrequisito universal. Un proceso bien delimitado puede iniciar
directamente en Process Modelling o Software Design.

## Big Picture

**Objetivo:** construir aprendizaje sistémico y una narrativa compartida de una línea de negocio.

**Participantes:** amplia diversidad; personas con preguntas y personas con respuestas.

**Mecánica mínima:**

1. Exploración caótica de eventos.
2. Orden temporal.
3. Eventos pivote y swimlanes cuando ayuden.
4. Personas y sistemas.
5. Hotspots.
6. Walkthrough narrado y corregido en vivo.

**Extensiones opcionales:** valor, problemas/oportunidades, ownership, votación, bounded contexts o
candidatos a historias.

**Cierre:** narrativa validada o claramente marcada como borrador, hotspots y siguiente área de
profundización. No agregar comandos/agregados solo para completar documentación.

## Process Modelling

**Objetivo:** descubrir o diseñar un proceso específico y todas sus variantes relevantes.

**Participantes:** equipo interdisciplinario pequeño con representación de los stakeholders afectados.

**Reglas de cierre:**

1. Cada camino termina en un estado estable.
2. La gramática evento/comando/política/read model se respeta.
3. Cada stakeholder queda razonablemente satisfecho.
4. Cada hotspot se resuelve o queda aceptado con responsable y consecuencia.

**Mecánica:** construir primero el camino base; aplazar objeciones como hotspots; después tensionar el
modelo con alternativas, excepciones, cantidades, vencimientos y casos límite.

**Extensiones opcionales:** valor/emociones, wireframes, pruebas de aceptación y oportunidades TO-BE.

## Software Design

**Objetivo:** diseñar comportamiento de software coherente para procesos críticos.

**Participantes:** expertos de dominio y equipo técnico capaces de discutir comportamiento sin
desplazar el lenguaje del negocio.

**Reglas adicionales:**

1. Visualizar y permitir mover límites.
2. Exigir comportamiento consistente dentro de cada componente/agregado.

**Mecánica:** eventos, comandos, políticas y read models; agregados por invariantes/ciclo de vida;
lenguaje ubicuo; bounded contexts; escenarios reales y casos límite.

**Extensiones opcionales:** wireframes cuando la interfaz cambia decisiones, pruebas de aceptación y
prototipo/código para obtener feedback.

## Cadena de formatos

Declarar siempre:

```text
Formato actual: <formato>
Entrada heredada: <artefacto o ninguno>
Pregunta que este formato debe resolver: <pregunta>
Criterio de cierre: <resultado observable>
Siguiente formato: <formato o ninguno>
```

Cerrar y validar cada formato antes de iniciar el siguiente. No reutilizar automáticamente el mismo
grupo de participantes: ajustar perspectivas y tamaño al objetivo de cada receta.
