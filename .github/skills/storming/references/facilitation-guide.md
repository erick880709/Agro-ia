# Guía de facilitación y validación

Leer esta guía únicamente al conducir un taller o validar un modelo documental con expertos de dominio.

## Contenido

- Preparación y selección de formato.
- Big Picture.
- Process Modelling.
- Software Design.
- Pruebas de aceptación.
- Desacuerdos y validación documental.
- Cierre.

## Preparación

Confirmar antes de iniciar:

- Propósito, resultado esperado y formato seleccionado.
- Para Process Modelling/Software Design: proceso, punto inicial y punto final.
- Para Big Picture: línea de negocio y perspectivas necesarias.
- Big Picture: diversidad amplia de personas con preguntas y respuestas.
- Process Modelling/Software Design: equipo interdisciplinario pequeño que represente ejecución,
  decisión, soporte e integración.
- Experto de dominio con autoridad para confirmar reglas.
- Facilitador y responsable de registrar hotspots.
- Modo AS-IS o TO-BE.

Evitar iniciar con una presentación extensa de DDD. Explicar solo la notación necesaria para la fase
actual.

Aplicar únicamente las secciones correspondientes al formato seleccionado; no convertir esta guía en
una secuencia obligatoria de los tres formatos.

## Big Picture

### 1. Eventos caóticos

Pedir a cada participante hechos relevantes que ya ocurrieron, en pasado:

- “¿Qué tuvo que ocurrir para que el proceso avanzara?”
- “¿Qué hecho le importa al negocio?”
- “¿Qué hecho inicia o termina el proceso?”
- “¿Qué resultado confirma una decisión o rechazo?”

Aceptar duplicados y conflictos inicialmente. No discutir soluciones ni ordenar todavía.

### 2. Línea de tiempo

Ordenar eventos de izquierda a derecha. Preguntar:

- “¿Qué tuvo que ocurrir justo antes?”
- “¿Puede ocurrir esto más de una vez?”
- “¿Qué caminos alternativos existen?”
- “¿Dónde termina el proceso sin éxito?”
- “¿Qué ocurre si este paso falla o vence?”

Marcar pivotes, ramas, ciclos, esperas y compensaciones.

Cerrar Big Picture con un walkthrough: una persona narra el flujo en voz alta y otra actualiza el
modelo con correcciones. Continuar con otro formato solo si el objetivo lo requiere.

## Process Modelling

### 3. Comandos y actores

Para cada evento relevante preguntar:

- “¿Quién quiso que esto ocurriera?”
- “¿Qué decisión o acción lo provocó?”
- “¿Qué información necesitó para decidir?”
- “¿Puede un sistema externo producirlo?”

No forzar un comando cuando el evento es temporal, externo o espontáneo; registrarlo explícitamente.

### 4. Políticas y reglas

Buscar automatismos y reacciones:

```text
Cuando [evento]
si [condición]
entonces [comando]
```

Distinguir:

- Política: reacción o decisión que conecta eventos y comandos.
- Regla: restricción que siempre debe cumplirse.
- Excepción: camino válido diferente del flujo normal.
- Hotspot: pregunta o conflicto aún sin respuesta.

Construir primero un camino base hasta un estado estable. Usar hotspots para aplazar alternativas sin
perderlas; después volver sobre ellas y tensionar el modelo con excepciones y casos límite.

Comprobar antes de cerrar:

- Cada camino termina en estado estable.
- La gramática se respeta.
- Cada stakeholder queda razonablemente satisfecho.
- Cada hotspot se resuelve o queda aceptado con responsable y consecuencia.

## Software Design

### 5. Límites y comportamiento

Agrupar por cambios de:

- Lenguaje.
- Reglas/invariantes.
- Responsable u ownership.
- Ritmo de cambio.
- Necesidad de autonomía.

Usar estos cortes como hipótesis de bounded contexts. No discutir microservicios ni repositorios en
esta fase.

Modelar agregados por comportamiento, invariantes y ciclo de vida. Modelar read models como la
información necesaria para tomar decisiones. Derivar entidades internas solo cuando aclaren el
comportamiento.

## Extraer pruebas de aceptación

Ejecutar opcionalmente después de Process Modelling o Software Design cuando el flujo principal y los
casos límite sean suficientemente robustos.

Seleccionar escenarios que:

- Representen el camino base.
- Cubran reglas o políticas importantes.
- Tensionen el modelo con vencimientos, cantidades, rechazos o compensaciones.
- Resuelvan o hagan verificable un hotspot.

Redactar cada escenario con equivalencia bilingüe:

```text
DADO / GIVEN [estado o contexto verificable]
CUANDO / WHEN [acción, comando o evento disparador]
ENTONCES / THEN [evento, estado o resultado observable]
```

Usar una sola expectativa observable por escenario. Agregar ejemplos concretos cuando reduzcan
ambigüedad y mantener trazabilidad hacia los IDs reales del modelo. Persistir opcionalmente en
`ES-016-Escenarios-de-Aceptacion.md`.

## Manejo de desacuerdos

No resolver por votación una regla de negocio que requiere autoridad. Registrar:

1. Versiones en conflicto.
2. Fuente o experiencia que sostiene cada versión.
3. Impacto de no resolver.
4. Persona responsable.
5. Fecha o evento de resolución.

Convertir el desacuerdo en hotspot y continuar si no bloquea la fase actual.

## Validación de modelos documentales

Al validar un modelo inferido desde documentos:

1. Presentar primero alcance y línea de tiempo, no los agregados.
2. Pedir correcciones concretas sobre eventos omitidos, orden y excepciones.
3. Confirmar reglas y términos ambiguos.
4. Revisar bounded contexts al final.
5. Registrar participante, rol, fecha y elementos confirmados.

No convertir una reunión sin expertos de dominio en `validado-dominio`. Usar `validacion-parcial`.

## Rondas de preguntas documentales

En modo documental o conversación asíncrona, formular máximo 5 preguntas por ronda:

1. Bloqueos legales, regulatorios o de seguridad.
2. Reglas que cambian límites o invariantes.
3. Excepciones que alteran la línea de tiempo.
4. Fuentes de verdad e integraciones.
5. Definiciones de lenguaje.

No preguntar por decisiones técnicas que correspondan a `archi`.

En un taller en vivo no limitar artificialmente la cantidad total de preguntas: facilitar su aparición,
usar hotspots para diferir discusiones y proteger el foco de la actividad actual.

## Cierre del taller

Mostrar:

- Flujo confirmado.
- Cambios realizados durante la sesión.
- Hotspots resueltos y pendientes.
- Personas responsables y próximos hitos.
- Estado del modelo.
- Formato ejecutado y criterio de cierre alcanzado.
- Perfil mínimo cosechado y extensiones opcionales creadas.
- Siguiente handoff: aclaración con `epicureo`, arquitectura con `archi` o desglose con `specter`.

No considerar el número de documentos como criterio de éxito.
