# Guía: Gate DR-01 de preparación del dominio

Usa este gate en los casos A (greenfield) y C (TO-BE) antes de generar la línea base de arquitectura. Su propósito es evitar que `archi` seleccione una solución técnica sin comprender el comportamiento del negocio. El requisito es contar con evidencia suficiente del dominio; Event Storming es la evidencia obligatoria por defecto cuando el dominio es complejo, pero no una ceremonia universal.

## 1. Evaluar aplicabilidad

Clasifica el dominio antes de generar artefactos de arquitectura:

| Clasificación | Señales | Decisión sobre Event Storming |
|---|---|---|
| Complejo | Proceso end-to-end o transversal; múltiples actores, equipos o estados; reglas y excepciones relevantes; compensaciones; integraciones; consistencia distribuida; arquitectura orientada a eventos; límites de dominio u ownership inciertos | Obligatorio |
| Simple | Cambio aislado, comportamiento acotado, reglas conocidas, un owner claro y sin transiciones o integraciones relevantes | No obligatorio si existe evidencia equivalente validada |
| Técnico | Librería, plataforma o capacidad puramente técnica sin proceso de negocio relevante | No aplica, con justificación |

No uses la arquitectura pretendida como evidencia para declarar simple el dominio. La clasificación se basa en comportamiento, lenguaje, ownership y riesgo de negocio.

En Caso B (AS-IS) no bloquees la observación del sistema por ausencia de Event Storming. Si la solicitud incorpora un TO-BE, reclasifícala como Caso C y aplica DR-01 antes de diseñar el estado objetivo.

## 2. Evidencia mínima

Para declarar el gate `Listo`, debe existir evidencia verificable de:

1. Propósito, alcance incluido/excluido y resultados esperados.
2. Actores, stakeholders, owners y autoridad de decisión.
3. Procesos o capacidades críticas, con inicio, final y estados estables cuando apliquen.
4. Eventos, comandos, reglas, políticas, excepciones y compensaciones relevantes.
5. Sistemas externos, integraciones y dependencias del dominio.
6. Lenguaje ubicuo y términos conflictivos.
7. Límites de dominio o bounded contexts candidatos, sin convertirlos en servicios desplegables.
8. Hotspots con prioridad, responsable, impacto y estado.
9. Fuente y nivel de validación del modelo.

Cuando Event Storming sea obligatorio, usa los artefactos existentes en `resources/functional/eventstorming/` y trata como paquete mínimo, cuando correspondan al formato ejecutado, `ES-002`, `ES-004`, `ES-010`, `ES-012`, `ES-013` y `ES-015`. No exijas documentos ajenos al formato elegido. Acepta:

- `validado-dominio`; o
- `validacion-parcial` únicamente si no existen hotspots que bloqueen arquitectura y cada riesgo restante tiene owner y condición de cierre.

No aceptes `borrador-documental` como validación del dominio ni `bloqueado-por-hotspots` para continuar con el diseño objetivo.

La evidencia equivalente puede ser un modelo DDD validado, BPMN, capability map, especificación operacional u otra fuente que cubra los nueve puntos anteriores, identifique a quienes la validaron y conserve trazabilidad. Una lista de requisitos o entidades, por sí sola, no es equivalente.

## 3. Resultados permitidos

| Estado DR-01 | Significado | Acción |
|---|---|---|
| `Listo` | Evidencia suficiente y cero hotspots arquitectónicos bloqueantes | Continuar con el Paso 1 |
| `Listo con riesgos` | Event Storming en `validacion-parcial`, sin bloqueantes; riesgos no críticos con owner y condición de cierre | Continuar, registrar riesgos y exigir su cierre antes de `25` |
| `Requiere clarificación de negocio` | Falta propósito, alcance, métricas, prioridad o decisión de stakeholders | Detener el flujo y devolver al orquestador para `epicureo` |
| `Requiere Event Storming` | El dominio es complejo y falta un modelo aceptable | Detener el flujo y devolver al orquestador para `storming` |
| `Bloqueado` | Existen hotspots que bloquean decisiones arquitectónicas | No generar la arquitectura objetivo; informar IDs, owner y condición de reanudación |

`archi` no ejecuta Event Storming dentro de su sesión ni sustituye la validación de expertos del dominio con inferencias propias.

## 4. Contrato que debe registrar `01`

Cuando DR-01 permita continuar, agrega a `01-Linea-Base_<Proyecto>.md` una sección `## Preparación del dominio` con esta tabla:

```markdown
| Campo | Valor |
|---|---|
| Escenario | A o C |
| Complejidad del dominio | Complejo / Simple / Técnico |
| Event Storming | Obligatorio / Evidencia equivalente / No aplica |
| Estado del modelo | validado-dominio / validacion-parcial / evidencia-equivalente / no-aplica |
| Estado DR-01 | Listo / Listo con riesgos |
| Evidencia | Rutas e IDs verificables |
| Hotspots arquitectónicos bloqueantes | Ninguno |
| Handoff pendiente | Ninguno |
| Riesgos no bloqueantes | Ninguno / ID, owner y condición de cierre |
| Justificación | Razón de aplicabilidad y suficiencia |
```

No uses valores vacíos, “por definir” o una afirmación sin fuente. `Listo` exige `Riesgos no bloqueantes: Ninguno`; `Listo con riesgos` exige al menos un riesgo identificable con owner y condición de cierre, y obliga a actualizar DR-01 a `Listo` antes de declarar `25` apto. Si el gate no permite continuar, no crees `01` para aparentar avance: devuelve un handoff con estado, faltantes concretos, destino y condición de reanudación.

## 5. Handoffs y reanudación

- Falta de propósito, alcance, métricas o decisión de stakeholders: `orquestador → epicureo`.
- Falta de eventos, reglas, estados, excepciones, lenguaje o límites del dominio: `orquestador → storming`.
- Hotspot resuelto por `epicureo`: reconciliar Event Storming conservando IDs antes de volver a `archi`.
- Modelo de dominio suficiente: `storming → archi`, entregando estado, fuentes, participantes, artefactos e IDs de hotspots.

Al reanudar, vuelve a ejecutar DR-01. No des por cerrado el gate solo porque existe la carpeta `eventstorming/`.

## 6. Límites

- Event Storming descubre el dominio; no selecciona nube, framework, persistencia ni topología.
- `archi` decide la materialización técnica; no reescribe hechos del negocio para ajustarlos a una solución.
- Un bounded context no equivale automáticamente a un microservicio, módulo o repositorio.
- La aprobación arquitectónica no sustituye la validación del dominio, y la validación del dominio no aprueba la arquitectura.
