# Referencia generica — Formato de acta de reunion (respaldo)

Esquema generico de acta, agnostico de cliente. **Usa esta referencia solo cuando el proyecto actual
no tenga una plantilla oficial de acta propia** en `resources/procesos/templates/` (ver `SKILL.md`,
Paso 1.0a) — si el proyecto SI tiene plantilla propia, esa manda sobre esta guia.

Esta referencia aplica a **generar** una acta (redactar una nueva a partir de notas/transcripcion que
te de el usuario), no a **leer** las que ya existen en `Meetings/` — para eso ver el Paso 0 de
`SKILL.md`, que procesa cualquier formato de archivo tal como venga, sin forzarlo a esta estructura.

## Encabezado

- **Numero de acta**: consecutivo — ver "Numeracion y anti-colision" en `SKILL.md`.
- **Fecha** / **Hora** / **Lugar**: de la reunion.
- **Elaborado por**: quien redacta el acta (puede ser distinto de quien lidero la reunion).
- **Objetivo de la reunion**: en una frase, para que se convoco.
- **Asistentes**: nombre y rol/cargo de cada participante.

## Agenda

Tabla `Item | Tema` — los puntos previstos a tratar, en el orden en que se trataron.

## Compromisos del acta anterior

Tabla `Item | Compromiso | Responsable | Fecha de entrega` — solo si esta reunion es continuacion de
una anterior con compromisos pendientes. Si es la primera reunion de la serie, omite esta seccion o
dejala vacia con una nota.

## Desarrollo tematico

Narrativa de lo discutido, organizada por punto de agenda. Aqui es donde tipicamente aparece
informacion de procesos (decisiones, responsables, actividades, sistemas) — recuerda que si esta
acta se esta generando como parte del levantamiento de un proceso, esa informacion tambien debe
reflejarse en el `.md` del proceso correspondiente (seccion "Notas de reuniones"), no solo en el acta.

## Documentos anexos

Tabla `Item | Tema` — documentos que se adjuntaron o se mencionaron como soporte de la reunion.

## Acuerdos o compromisos

Tabla `Item | Compromiso | Responsable | Fecha de entrega` — lo que quedo pendiente de esta reunion,
para dar seguimiento en la proxima.

## Proxima reunion

Fecha (si se acordo una). Si no se acordo, indicarlo explicitamente en vez de dejarlo vacio sin
explicacion.

## Control de cambios / aprobacion

Igual estructura que los demas documentos: tabla `Version | Fecha | Descripcion de la actualizacion`
y fila `Elaboro | Reviso | Aprobo`.
