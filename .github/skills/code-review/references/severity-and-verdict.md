# Severidad, confianza y veredicto

## Severidad (impacto, no gusto)

| Severidad | ID | Significa | Ejemplos |
|---|---|---|---|
| `bloqueante` | `B-NN` | No se fusiona así | Comportamiento roto o AC visible ausente; vulnerabilidad explotable; pérdida/corrupción de datos; exposición de PII o secretos; build/test rojo; ruptura de contrato público sin mandato; violación de regla de arquitectura obligatoria (scaffold) |
| `mayor` | `M-NN` | Debe corregirse antes de fusionar | Error no manejado en ruta de usuario; regresión de rendimiento probable; test que no puede fallar para lógica nueva; acoplamiento que rompe límites del repo; AC parcial; edición de archivo `managed` |
| `menor` | `m-NN` | Corregir cuando convenga, no bloquea | Nombre confuso, duplicación pequeña, tipo laxo, log mejorable |
| `nit` | `N-NN` | Opcional | Preferencia de estilo compatible, micro-optimización |

Anotaciones sin severidad (no cuentan para el veredicto):

| Tipo | ID | Uso |
|---|---|---|
| `pregunta` | `Q-NN` | Algo que no pudiste verificar o depende de contexto que no tienes. Formúlalo como pregunta concreta ("¿qué pasa si `items` llega vacío desde el batch?") |
| `preexistente` | `P-NN` | Defecto en código tocado que el cambio no introdujo. Informativo salvo que el cambio lo agrave |
| `fyi` | `F-NN` | Contexto útil para el autor, sin acción |

Escala `mayor` → `bloqueante` cuando el impacto alcanza usuarios, dinero, datos
personales o seguridad. Baja `mayor` → `menor` cuando hay una defensa real en
otra capa que verificaste.

## Confianza

Asigna confianza a cada hallazgo después de la pasada de verificación:

- **alta:** leíste el código actual, construiste el escenario y no hay defensa;
  idealmente lo demostraste (test, comando, mutación).
- **media:** el escenario es plausible y no encontraste defensa, pero no lo
  ejecutaste o depende de configuración que no viste.
- **baja:** sospecha. No se reporta como defecto: conviértela en `pregunta` o
  descártala.

Un `bloqueante` exige confianza alta, o media con impacto crítico (seguridad,
datos) y entonces explica qué falta para confirmarlo.

## Filtro de falsos positivos

Descarta un candidato si:

- el código actual ya no contiene el problema (lo viste en el diff pero un hunk
  posterior lo corrige);
- existe validación/guarda en otra capa por la que siempre pasa el flujo;
- el tipo, el framework o la configuración lo impiden (p. ej. Bean Validation
  activo en el controller, constraint de BD, `@Transactional` presente);
- es una regla que el linter/CI del proyecto ya hace cumplir;
- contradice una convención explícita del proyecto (`CLAUDE.md`, ADR);
- es una preferencia sin impacto observable.

## Veredicto

| Veredicto | Condición |
|---|---|
| `aprobado` | 0 bloqueantes, 0 mayores, gate verde, todos los AC del alcance ✅ |
| `aprobado-con-observaciones` | Como arriba pero con menores/nits/preguntas no críticas abiertos |
| `cambios-requeridos` | ≥ 1 bloqueante o mayor verificado, o algún AC ❌/⚠️ en alcance |
| `no-concluyente` | No se puede juzgar: spec inaccesible, diff incompleto, gate imposible de ejecutar sin evidencia alternativa. Indica exactamente qué falta |

Una `pregunta` puede impedir `aprobado` si su respuesta podría convertirla en
bloqueante (p. ej. "¿este endpoint es público?"). En ese caso el veredicto es
`cambios-requeridos` con la pregunta como acción.

## Orden de presentación

Bloqueantes → mayores → menores → nits → preguntas → preexistentes. Dentro de
cada grupo, por impacto. Si hay un problema estructural y diez nits, el
problema estructural *es* la revisión: considera omitir los nits.
