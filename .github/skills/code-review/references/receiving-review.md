# Recepción de hallazgos (modo `receive`)

Para quien recibe una revisión —Builder, otro agente o tú mismo— y debe
decidir y aplicar. El principio: verifica antes de implementar; corrección
técnica sobre comodidad social.

## Secuencia

1. **Leer** todo el reporte (y notas del autor) antes de tocar código.
2. **Entender:** reformula cada hallazgo como requisito técnico. Si alguno no
   está claro, detente y pregunta por **todos** los poco claros antes de
   implementar cualquiera: los hallazgos suelen estar relacionados.
3. **Verificar** contra el código actual: ¿el escenario ocurre en *este*
   repositorio, versión y configuración?
4. **Evaluar:** ¿rompe funcionalidad existente? ¿hay una razón para el diseño
   actual (compatibilidad, decisión registrada)? ¿el revisor tenía todo el
   contexto?
5. **Responder:** aceptar, o rechazar con razón técnica verificable, o pedir
   información.
6. **Implementar** uno por vez: bloqueantes → arreglos simples → arreglos
   complejos; ejecuta las comprobaciones afectadas tras cada uno.

## Cuándo rechazar

- La sugerencia rompe comportamiento o contrato existente.
- El revisor no tenía contexto (consumidor real, restricción de plataforma).
- YAGNI: piden "implementarlo bien" algo que nadie usa. Busca usos
  (`grep -rn`); si no hay, propone eliminarlo en vez de ampliarlo.
- Es incorrecto para este stack o contradice una decisión aprobada (ADR,
  usuario). Si choca con una decisión del usuario, consúltale antes.

Rechaza con hechos: "El endpoint lo consume `pagos-batch` (ver
`clients/pagos.yaml:12`); renombrar el campo lo rompe. Propongo deprecarlo".

## Cuándo no puedes verificar

Dilo: "No puedo verificar esto sin acceso a la configuración de producción;
¿lo investigo, lo pregunto o procedo con la suposición X?". No implementes a
ciegas ni lo descartes en silencio.

## Respuestas

- Correcto: "Corregido: el gateway ahora filtra por titular
  (`AccountAdapter.java:58`); test `otherAccount` → 403".
- Sin acuerdo performativo ("¡Tienes toda la razón!", "¡Excelente punto!"),
  sin agradecimientos de relleno: el código corregido muestra que escuchaste.
- Si rechazaste y estabas equivocado: "Verifiqué X y hace Y; tenías razón.
  Corrigiendo." Sin disculpas largas.

## Reglas para Builder al recibir

- No debilites tests ni requisitos para cerrar un hallazgo.
- No amplíes alcance para atender "fuera de alcance"; regístralo como deuda.
- Actualiza el estado en el reporte (`corregido`, con una línea de qué cambió)
  y la evidencia; luego pide `re-review`.
- Un arreglo que pone rojo otro check deja el hallazgo `reabierto` con la
  regresión anotada; no lo marques corregido.
- "Lo limpio después" no cierra un hallazgo aceptado: corrígelo o difiérelo
  explícitamente con ticket y responsable.
- En hilos de GitHub, responde en el hilo del comentario, no como comentario
  general del PR, y solo si el usuario autorizó acciones remotas.
