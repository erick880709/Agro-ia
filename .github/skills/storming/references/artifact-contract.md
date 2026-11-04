# Contrato de artefactos de Event Storming

Usar esta estructura para hacer harvesting, reconciliar y validar outputs bajo
`resources/functional/eventstorming/`. No interpretar el catálogo como una lista obligatoria: producir
solo el perfil mínimo del formato seleccionado y cualquier extensión que el usuario haya pedido.

El board, las conversaciones y las decisiones son el resultado principal. Los archivos son una captura
posterior para preservar aprendizaje y habilitar handoffs. No crear archivos vacíos.

## Contenido

- Perfiles mínimos de harvesting.
- Catálogo e identificadores.
- Tablas mínimas por tipo de elemento.
- Trazabilidad.
- Checklist de cierre por perfil.

## Perfiles mínimos de harvesting

| Formato | Archivos mínimos | Extensiones cuando aporten valor |
|---|---|---|
| `big-picture` | `ES-001`, `ES-002`, `ES-003`, `ES-004`, `ES-013` | `ES-005` para narrativa detallada; `ES-012` si se trabajaron límites |
| `process-modelling` | `ES-001`, `ES-002`, `ES-005`, `ES-006`, `ES-007`, `ES-008`, `ES-013` | `ES-014/015` para TO-BE; `ES-016` para aceptación |
| `software-design` | `ES-001`, `ES-002`, `ES-006`, `ES-007`, `ES-008`, `ES-010`, `ES-011`, `ES-012`, `ES-013` | `ES-009` si las entidades aclaran comportamiento; `ES-016` para aceptación |
| `cadena` | Unión sin duplicados de los perfiles ejecutados | Solo extensiones solicitadas |

Permitir un harvesting todavía más liviano —por ejemplo, export/fotografía del board más un resumen de
hotspots— si preserva suficiente contexto para el objetivo de la sesión. Generar el catálogo completo
solo por solicitud explícita o necesidad comprobada de un consumidor posterior.

## Catálogo

| Archivo | Nivel | Contenido mínimo |
|---|---|---|
| `ES-001-Resumen-Ejecutivo-y-Alcance.md` | Sesión | Modo, estado, proceso, propósito, inicio/fin, IN/OUT, fuentes, participantes, hallazgos y enlaces |
| `ES-002-Eventos-de-Dominio.md` | Big Picture | Catálogo de eventos, línea temporal, proceso, descripción, datos mínimos y fuente |
| `ES-003-Actores.md` | Big Picture | Actores, tipo, responsabilidad, comandos y consultas |
| `ES-004-Sistemas-Externos.md` | Big Picture | Sistemas, rol, dirección, mecanismo conocido, fuente de verdad y estado AS-IS/TO-BE |
| `ES-005-Flujos-del-Proceso.md` | Process | Flujo principal, pivotes, rutas alternativas, excepciones y compensaciones |
| `ES-006-Comandos.md` | Process | Comando, actor, precondiciones, validaciones, evento resultante y errores |
| `ES-007-Consultas.md` | Process | Read models/consultas, consumidor, datos y comandos que soportan |
| `ES-008-Politicas-y-Reglas-de-Negocio.md` | Process | Políticas reactivas, condiciones, reglas, excepciones y fuente |
| `ES-009-Entidades.md` | Design | Identidad, ciclo de vida, atributos sustentados, reglas y relaciones |
| `ES-010-Agregados.md` | Design | Raíz, miembros, invariantes, comandos, eventos y límite de consistencia |
| `ES-011-Lenguaje-Ubicuo.md` | Design | Término, definición, contexto, fuente, sinónimos y estado de discusión |
| `ES-012-Clasificacion-Dominio-y-Contextos.md` | Domain | Subdominios, bounded contexts, ownership, lenguaje, relaciones y context map |
| `ES-013-Hotspots-Consolidados.md` | Transversal | Hotspot, evidencia, impacto, prioridad, bloqueo, responsable y estado |
| `ES-014-Analisis-de-Mejoras.md` | TO-BE | Problema/hotspot, oportunidad, valor, contexto, dependencias y prioridad |
| `ES-015-Definicion-TO-BE.md` | TO-BE | Diferencias AS-IS/TO-BE, eventos/comandos, integraciones, transición y criterios de éxito |
| `ES-016-Escenarios-de-Aceptacion.md` | Extensión | Escenarios Dado/Cuando/Entonces con ejemplos, resultado observable y trazabilidad |

## Identificadores

| Concepto | Prefijo | Ejemplo |
|---|---|---|
| Evento | `EV` | `EV01` |
| Actor | `AC` | `AC03` |
| Sistema externo | `SX` | `SX02` |
| Comando | `CM` | `CM07` |
| Consulta/read model | `QR` | `QR04` |
| Política | `PL` | `PL02` |
| Regla de negocio | `RN` | `RN05` |
| Entidad | `EN` | `EN03` |
| Agregado | `AG` | `AG02` |
| Subdominio | `SD` | `SD01` |
| Bounded context | `BC` | `BC04` |
| Hotspot | `HS` | `HS08` |
| Oportunidad | `OP` | `OP06` |
| Escenario de aceptación | `AT` | `AT03` |

Conservar los IDs existentes aunque cambie el nombre. Marcar elementos retirados como `retirado`; no
renumerar los siguientes. Asignar IDs durante el harvesting, no durante la exploración caótica.

## Tablas mínimas

### Eventos

| ID | Evento en pasado | Descripción de negocio | Proceso | Datos mínimos | Origen/Fuente | Estado |
|---|---|---|---|---|---|---|

Estados sugeridos: `confirmado`, `inferido`, `en-discusion`, `nuevo-to-be`, `modificado-to-be`,
`retirado-to-be`.

### Comandos

| ID | Comando | Actor | Precondiciones | Validaciones | Evento(s) resultante(s) | Fuente |
|---|---|---|---|---|---|---|

### Políticas

| ID | Cuando ocurre | Si se cumple | Entonces ejecutar | Datos/consulta | Excepciones | Fuente |
|---|---|---|---|---|---|---|

### Agregados

| ID | Agregado/Raíz | Entidades | Invariantes protegidas | Comandos | Eventos | Estado |
|---|---|---|---|---|---|---|

### Bounded contexts

| ID | Contexto | Subdominio | Responsabilidad | Lenguaje/ownership | Publica | Consume | Estado |
|---|---|---|---|---|---|---|---|

### Hotspots

| ID | Pregunta/Conflicto | Evidencia | Impacto | Prioridad | Bloquea | Responsable | Estado |
|---|---|---|---|---|---|---|---|

Valores para `Bloquea`: `dominio`, `arquitectura`, `backlog`, `implementacion`, `no-bloqueante`.

### Escenarios de aceptación

| ID | Nombre | Dado/Given | Cuando/When | Entonces/Then | Ejemplos | Trazabilidad | Estado |
|---|---|---|---|---|---|---|---|

Reglas:

- Expresar una expectativa observable por escenario.
- Mantener `Dado` como estado/contexto, `Cuando` como disparador y `Entonces` como resultado.
- Referenciar únicamente IDs existentes `CM`, `EV`, `PL`, `RN`, `AG`, `BC` y `HS`.
- Incluir camino base y casos límite que tensionaron el modelo.
- No convertir escenarios en historias, tareas ni casos automatizados dentro de esta skill.

## Trazabilidad mínima

Mantener relaciones verificables:

```text
Fuente CTX/RF/RNF/RT/RD
  → Evento/Regla/Hotspot
  → Comando/Política/Agregado
  → Bounded Context
  → Oportunidad TO-BE
  → Escenario AT (cuando se extraiga)
  → HU/TT generada posteriormente por specter
```

No exigir una relación ficticia cuando un elemento fue descubierto directamente en taller. En ese
caso registrar `Fuente: taller YYYY-MM-DD — participante/rol`.

## Checklist de cierre por perfil

- [ ] Alcance y estado de validación explícitos en `ES-001`.
- [ ] AS-IS y TO-BE distinguibles sin depender del contexto de conversación.
- [ ] Eventos expresados en pasado y ordenados.
- [ ] En Big Picture: personas/sistemas, pivotes y narrativa recorrida.
- [ ] En Process Modelling: comandos, políticas, read models, caminos estables y stakeholders satisfechos.
- [ ] En Software Design: agregados por comportamiento, límites visibles y lenguaje ubicuo.
- [ ] Excepciones relevantes con salida, compensación o hotspot.
- [ ] Hotspots consolidados con responsable y bloqueo.
- [ ] IDs estables y enlaces internos válidos.
- [ ] Fuentes documentales o participantes trazables.
- [ ] Si se extrajeron pruebas: escenarios observables Dado/Cuando/Entonces y trazabilidad válida.
- [ ] Siguiente handoff identificado.
- [ ] No se generaron archivos ajenos al perfil solo para completar el catálogo.
