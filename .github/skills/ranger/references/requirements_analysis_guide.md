# Guía de Análisis de Requisitos Antes del Diseño de Pruebas

Fase previa a `./testing_strategies.md` y `../../qa-ranger-plan-pruebas/templates/test_plan_template.md`: antes
de definir estrategia o escribir la matriz funcional, analizar la fuente
del requisito (historia de Jira, HU, documento funcional, hallazgo de un
incidente) para detectar ambigüedad, conflictos y huecos de trazabilidad
que, si pasan desapercibidos, se convierten en casos de prueba mal
diseñados o en huecos de cobertura invisibles.

---

## Índice

- [Cuándo Aplicar Esta Fase](#cuándo-aplicar-esta-fase)
- [Detección de Ambigüedad](#detección-de-ambigüedad)
- [Detección de Conflictos entre Requisitos](#detección-de-conflictos-entre-requisitos)
- [Trazabilidad](#trazabilidad)
- [Extracción de Reglas de Negocio Implícitas](#extracción-de-reglas-de-negocio-implícitas)
- [Salida Esperada](#salida-esperada)

---

## Cuándo Aplicar Esta Fase

- Siempre que exista una fuente de requisito identificable (historia de
  Jira/HU, spec funcional, documento de negocio) antes de generar el plan
  de pruebas — ver Paso "0.2" en `../SKILL.md`.
- Si el usuario solo pide "ejecutar este runbook ya escrito" sin una fuente
  de requisito nueva detrás, esta fase no aplica — el runbook ya es el
  contrato a ejecutar (ver `./markdown_test_runbook.md`).
- Si el requisito es trivial y sin ambigüedad real (ej. "cambiar el color
  de un botón"), no forzar esta fase — aplica el juicio proporcional al
  riesgo, no un checklist obligatorio para todo.

## Detección de Ambigüedad

Revisar el requisito buscando estas categorías de ambigüedad — cada una
encontrada se marca `[SUPUESTO]` en el plan de pruebas (ver
`../../qa-ranger-plan-pruebas/templates/test_plan_template.md`) hasta confirmarse con el usuario/stakeholder:

| Categoría | Pregunta a hacerse | Ejemplo |
|---|---|---|
| Actores | ¿Quién exactamente puede hacer esto? ¿Todos los roles o solo algunos? | "El usuario puede cancelar la orden" — ¿cualquier usuario o solo el dueño? |
| Condiciones | ¿Bajo qué condición aplica la regla? | "Se aplica un descuento" — ¿siempre, o solo en ciertas condiciones no explicitadas? |
| Cantidades | ¿Hay un límite? ¿Qué pasa en el límite exacto? | "Puede subir varios archivos" — ¿cuántos es "varios"? |
| Temporalidad | ¿Cuándo empieza/termina de aplicar? | "La promoción es válida por unos días" — ¿desde cuándo, hasta cuándo? |
| Estados | ¿Qué pasa si el recurso ya está en otro estado? | "Se puede editar el pedido" — ¿en cualquier estado, incluso ya enviado? |
| Lenguaje de aceptación | ¿El criterio de aceptación es verificable objetivamente? | "La página debe cargar rápido" — no es un criterio verificable sin un número |

## Detección de Conflictos entre Requisitos

Al comparar el requisito nuevo contra requisitos/comportamiento existentes
documentados (otras historias, el propio código, otro documento):

- ¿Este requisito contradice una regla ya implementada en otra parte del
  sistema? (ej. una historia dice "el límite diario es $5.000.000" y otra
  parte del sistema ya documentaba $10.000.000).
- ¿Dos criterios de aceptación de la misma historia son mutuamente
  excluyentes en algún escenario borde?
- Si se detecta un conflicto real, **no decidir cuál es el correcto** — es
  una decisión de negocio. Documentarlo y preguntarle al usuario antes de
  diseñar casos sobre una interpretación asumida.

## Trazabilidad

Cada fila de la Matriz Funcional (`../../qa-ranger-plan-pruebas/templates/test_plan_template.md`, sección 4)
debe poder trazarse a:

1. Un criterio de aceptación explícito de la historia/requisito, **o**
2. Una regla de negocio implícita documentada explícitamente como tal (ver
   siguiente sección), **o**
3. Un caso marcado `[SUPUESTO]` pendiente de confirmación.

Ningún caso debería existir "porque sí" sin que se pueda señalar de dónde
sale. Esto es lo que después permite responder, ante un defecto en
producción, si el comportamiento estaba cubierto por un requisito
conocido o era un hueco de análisis.

## Extracción de Reglas de Negocio Implícitas

Muchos invariantes de negocio nunca se escriben explícitamente porque se
consideran obvios para quien escribió el requisito, pero no lo son para
quien diseña las pruebas. Antes de cerrar el análisis, preguntarse
explícitamente:

- ¿Qué no puede pasar dos veces? (aplicar un cupón, confirmar un pago)
- ¿Qué recurso no puede quedar en un estado inconsistente? (una orden sin
  stock reservado, una transferencia sin ambos lados registrados)
- ¿Qué operación debería ser reversible y cuál no?
- ¿Qué pasa si dos usuarios interactúan con el mismo recurso a la vez?

Estas preguntas son la misma base que usa
`./adversarial_fraud_testing.md#como-derivar-casos-desde-las-reglas-de-negocio`
para generar casos adversariales — el análisis de requisitos alimenta
directamente ese playbook cuando el dominio lo amerita (transaccional,
financiero, multi-usuario).

## Salida Esperada

Esta fase no produce un documento nuevo separado por defecto — sus
resultados se integran directamente en:

- La sección "Encabezado Obligatorio" y "Matriz Funcional" del plan de
  pruebas, con los supuestos marcados `[SUPUESTO]`.
- Una lista corta y explícita de preguntas abiertas para el usuario,
  presentada **antes** de generar el plan completo si las ambigüedades
  encontradas son de alto impacto (afectan flujos `critical`/`high`) — no
  seguir adelante generando un plan entero sobre supuestos no confirmados
  cuando el riesgo lo amerita.
