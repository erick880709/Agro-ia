# Diagnóstico y revisión

## Diagnóstico dirigido por evidencia

Antes de corregir un defecto, expresa el síntoma observable, el comportamiento
esperado y el límite donde aparece. Sigue datos y control por el entrypoint real.
Formula una hipótesis que prediga una observación discriminante; ejecuta el
experimento más pequeño capaz de refutarla y registra resultado, no solo la acción.

No acumules cambios para probar varias causas a la vez. Tras un intento fallido,
revierte únicamente el experimento propio si es seguro, conserva la evidencia y
actualiza la hipótesis. Si dos intentos consecutivos no cambian la evidencia o el
mismo supuesto vuelve a fallar, deja de parchear: amplía instrumentación, revisa el
límite anterior o identifica el dato faltante. El número orienta la revisión, no
autoriza descartar una pista nueva ni convierte automáticamente la tarea en bloqueo.

Detén el diagnóstico cuando una causa explique el síntoma y una comprobación pueda
distinguir la versión defectuosa de la corregida. Si no hay reproducción, entrega
las hipótesis descartadas, evidencia obtenida y condición necesaria para continuar;
no presentes correlación, silencio de logs o un test incapaz de fallar como causa.

## Revisión en dos perspectivas

Revisa primero **cumplimiento** usando la fuente funcional y los criterios, sin
dejar que la forma del código redefina el resultado:

- comportamiento requerido, errores y escenarios negativos pertinentes;
- preservación, compatibilidad, ownership y ausencia de cambios fuera de alcance;
- cableado y entrypoints que demuestren que la implementación se usa;
- evidencia ejecutada contra la revisión actual.

Resuelve los incumplimientos antes de aceptar la entrega. Después revisa **calidad**:
claridad, consistencia con el repositorio, complejidad accidental, seguridad,
operabilidad y mantenibilidad proporcionales al cambio. Clasifica hallazgos por
impacto observable; una preferencia estilística compatible no bloquea cumplimiento.

En componentes Go, concreta la revisión de calidad y el diagnóstico con
[revisión y diagnóstico Go](stacks/go/go-review-and-debugging.md); en Angular, con
[revisión y diagnóstico Angular](stacks/angular/angular-review-and-debugging.md); en Java/Spring, con
[revisión y diagnóstico Java/Spring](stacks/java-spring/spring-review-and-debugging.md).

Un cambio ligero permite ambas perspectivas en la misma inspección. Usa revisor
independiente solo cuando el riesgo, la incertidumbre o la separación de ownership
lo justifiquen y exista capacidad; entrégale criterios y diff, no la conclusión
deseada. El autor reconcilia sus hallazgos con evidencia y vuelve a ejecutar las
comprobaciones afectadas. No marques calidad aprobada porque los tests estén verdes,
ni cumplimiento aprobado porque el diseño parezca limpio.

## Revisión independiente con code-review

Cuando uses la skill `code-review` (modo `gate`), entrega en el expediente
`docs/changes/<id>/`: spec con criterios `AC-xx` y comportamiento preservado, base y
revisión exacta (SHA o hashes si hay cambios sin commit), evidencia vigente y rigor
elegido. Haz commit o registra hashes antes de pedirla: una revisión sin
identificador de revisión no sirve para saber si sigue vigente.

El reporte `review.md` pertenece al revisor. Builder solo actualiza el estado y la
nota del autor de cada hallazgo; no reescribe hallazgos ni el veredicto.

Al recibir hallazgos:

- Lee todos antes de tocar código; si alguno no es claro, pregunta por todos los
  poco claros antes de implementar cualquiera.
- Verifica cada uno contra el código actual. Acepta los que se sostienen; rechaza
  con razón técnica comprobable (consumidor real, contrato, decisión aprobada,
  YAGNI demostrado con búsqueda de usos). Un hallazgo no es un mandato del usuario.
- Corrige en orden bloqueante → mayor → menor, uno por vez, re-ejecutando las
  comprobaciones afectadas. No debilites tests ni criterios para cerrar un hallazgo.
- Marca `corregido` con una línea de qué cambió y actualiza la evidencia; si el
  arreglo rompe otro check, déjalo `reabierto` con la regresión.
- Pide `re-review`: el revisor verifica los corregidos y el diff incremental.

Si tras dos rondas un hallazgo vuelve a reabrirse o aparecen hallazgos nuevos del
mismo tipo, deja de parchear: es probable que el problema sea de diseño o de spec.
Entrega el gap al responsable según [fronteras y fuentes](boundaries-and-sources.md).
