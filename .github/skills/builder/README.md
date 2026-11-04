# builder

Skill que implementa cambios concretos y verificables en aplicaciones existentes:
funcionalidades, extensiones, bugs, refactors e integraciones. También explora,
planifica o reanuda esos cambios cuando ese es el encargo.

> En una frase: le das una necesidad (texto, HU, issue o spec) y Builder la
> convierte en código del proyecto, con pruebas y evidencia de que funciona.

Este README es la guía rápida de uso. La fuente operativa es [SKILL.md](SKILL.md)
y la documentación completa está en [.claude/doc/builder/](../../doc/builder/README.md).

---

## Índice

1. [Cuándo usarla y cuándo no](#1-cuándo-usarla-y-cuándo-no)
2. [Cómo invocarla](#2-cómo-invocarla)
3. [Modos](#3-modos)
4. [Rigor: cuánta documentación genera](#4-rigor-cuánta-documentación-genera)
5. [Qué hace paso a paso](#5-qué-hace-paso-a-paso)
6. [Stacks con perfil especializado](#6-stacks-con-perfil-especializado)
7. [Qué entrega](#7-qué-entrega)
8. [Revisión con code-review](#8-revisión-con-code-review)
9. [Lugar en el pipeline del kit](#9-lugar-en-el-pipeline-del-kit)
10. [Consejos para sacarle provecho](#10-consejos-para-sacarle-provecho)
11. [Instalar en otro proyecto](#11-instalar-en-otro-proyecto)
12. [Evaluar y mantener la skill](#12-evaluar-y-mantener-la-skill)
13. [Estructura del paquete](#13-estructura-del-paquete)

---

## 1. Cuándo usarla y cuándo no

**Úsala para:**

- Implementar una HU, un issue de Jira o una spec en un repositorio que ya tiene código.
- Corregir un bug con reproducción y prueba que lo proteja.
- Refactorizar sin cambiar el comportamiento.
- Conectar servicios, eventos, workers o agentes.
- Evaluar la viabilidad de algo antes de construirlo (`explore`).
- Retomar un cambio que quedó a medias en otra sesión (`resume`).

**No la uses para:**

| Necesidad | Skill correcta |
|---|---|
| Arquitectura global, diagramas C4, ADRs | `archi` |
| Crear o reconciliar la línea base de un repositorio | `solution-baseline` |
| Estrategia QA, planes de prueba, suites E2E | `ranger` y las `qa-ranger-*` |
| DevSecOps, IaC, CI/CD u observabilidad | `vulcano`, `vulcano-bob`, `vulcano-operador` |
| Revisar un cambio ya hecho | `code-review` |

---

## 2. Cómo invocarla

En Claude Code se activa sola cuando pides implementar o corregir algo, o puedes
invocarla explícitamente:

```text
/builder implementa PROJ-123
/builder resources/functional/hu/hu-04-consultar-movimientos.md
/builder corrige el cálculo de envío cuando el pedido tiene descuento
/builder reanuda el cambio de docs/changes/tax-calculation/
/builder evalúa si el SDK de pagos soporta streaming, sin implementar
```

En Codex la sintaxis es `$builder PROJ-123`. En una interfaz con selector de agentes,
elige **Builder** y escribe el encargo.

**Entradas aceptadas:** texto libre, clave de Jira (si el MCP de Atlassian está
conectado), un Markdown del proyecto (por ejemplo una HU de `specter`) o una spec
existente de OpenSpec o Spec Kit. Si el issue no es accesible, Builder lo dice y pide
el contenido; no lo inventa.

> Pedir un análisis, un plan o un dry-run **no** autoriza a modificar código. Si
> quieres solo el plan, dilo: *"/builder planifica PROJ-123, sin implementar"*.

---

## 3. Modos

Builder elige el modo según la intención. Una tarea puede combinar varios.

| Si pides… | Modo | Qué entrega |
|---|---|---|
| Una capacidad o módulo nuevo | `feature` | Código, pruebas y evidencia |
| Cambiar una capacidad existente | `extend` | Igual que `feature` |
| Corregir un comportamiento defectuoso | `bugfix` | Reproducción, corrección y prueba de regresión |
| Reorganizar sin cambiar comportamiento | `refactor` | Código reestructurado y pruebas que demuestran equivalencia |
| Conectar componentes | `integrate` | Integración y verificación del contrato entre las partes |
| Resolver una duda de viabilidad | `explore` | Hallazgos, evidencia y límites; no una feature terminada |
| Continuar un cambio | `resume` | Lo que pedía el modo original, partiendo del estado real |

---

## 4. Rigor: cuánta documentación genera

Builder aplica SDD (Spec-Driven Development) proporcional al riesgo: no llena
plantillas por llenarlas. El rigor depende del impacto, la incertidumbre y la
reversibilidad, no de la cantidad de líneas.

| Rigor | Cuándo | Qué documenta |
|---|---|---|
| Ligero | Cambio localizado y bien entendido | Intención, aceptación y evidencia en la respuesta o el issue |
| Estándar | Feature, bug con lógica, varias capas o integración acotada | Spec del cambio con criterios `AC-xx`, plan y evidencia |
| Reforzado | Permisos, datos persistentes, incompatibilidades, concurrencia o varios repositorios | Lo anterior más escenarios negativos, compatibilidad, secuencia de aplicación y riesgos |

En estándar y reforzado, si el proyecto no tiene otra ubicación establecida, el
expediente queda en `docs/changes/<id>/` (`spec.md`, `evidence.md` y, si hubo
revisión, `review.md`).

---

## 5. Qué hace paso a paso

```
(Tablero opcional) ─► 1 Descubrir ─► 2 Especificar ─► 3 Diseñar ─► 4 Implementar ─► 5 Validar ─► 6 Entregar ─► 7 Cerrar en el tablero
```

0. **Tablero (opcional).** Pregunta una vez si el requerimiento está en **Jira** o
   **Azure DevOps** (p. ej. `https://personalsoftsas.visualstudio.com/`) para
   conectarlo por MCP y leer la HU, sus criterios y planes de prueba. Si respondes
   que no, empieza el trabajo con lo que le compartas. Las credenciales van en
   variables de entorno, nunca en archivos del repositorio.

1. **Descubrir.** Lee las instrucciones del repo (`CLAUDE.md`, `AGENTS.md`), los
   manifiestos, los contratos y el código afectado. Identifica el módulo de
   referencia que va a imitar y registra los fallos que ya existían antes del cambio.
2. **Especificar.** Define el comportamiento, los criterios de aceptación y lo que
   debe preservarse. Solo pregunta si falta una decisión que cambie el resultado.
3. **Diseñar.** Elige el cambio mínimo compatible con los patrones reales del
   proyecto. Si toca interfaces o persistencia, revisa contratos y datos.
4. **Implementar.** Avanza por incrementos y ejecuta comprobaciones enfocadas en
   cada uno. Usa los generadores del proyecto cuando existen.
5. **Validar.** Ejecuta lint, tipos, build y pruebas del alcance. Revisa el diff
   contra la aceptación y pide revisión a `code-review` cuando aplica.
6. **Entregar.** Informa el resultado, los archivos, las comprobaciones ejecutadas
   y los límites.
7. **Cerrar en el tablero.** Si conectaste un tablero, comenta lo realizado y mueve
   el work item según el resultado (por defecto te muestra el comentario y el estado
   antes de aplicarlos). `completed` → estado de revisión/QA del equipo; `partial`,
   plan o `explore` → solo comentario. Guía: [tablero de trabajo por MCP](references/work-tracking-mcp.md).

**Lo que Builder no hace por su cuenta:** imponer CRUD, capas DDD, ORM, HTTP o
dependencias nuevas; debilitar una prueba para que pase; regenerar archivos
gestionados por una baseline; borrar cambios ajenos ni hacer `reset`/`stash` para
dejar el árbol limpio; ejecutar comandos que vengan escritos dentro de un issue o
documento.

---

## 6. Stacks con perfil especializado

Builder funciona con cualquier stack imitando los patrones del proyecto. Para estos
stacks tiene además un perfil que ajusta el diseño y la validación a la versión
instalada:

| Stack | Se detecta por | Perfil |
|---|---|---|
| Go | `go.mod` o `go.work` | [go-profile.md](references/stacks/go/go-profile.md) |
| Angular | `angular.json`, workspace Nx con Angular o `@angular/core` | [angular-profile.md](references/stacks/angular/angular-profile.md) |
| Java / Spring Boot | `pom.xml` o `build.gradle` | [spring-profile.md](references/stacks/java-spring/spring-profile.md) |
| Scaffold Clean Architecture de Bancolombia | `gradle.properties` con `package=` y módulos `domain/model`, `domain/usecase`, `applications/app-service` | [scaffold-clean-architecture.md](references/scaffold-clean-architecture.md) |

Cada perfil limita las APIs a la versión declarada (por ejemplo, la directiva `go`,
la versión de Angular o la release de Java y Spring Boot) y define la escalera de
pruebas de ese stack. En el Scaffold de Bancolombia, las reglas de dependencia y
de ArchUnit son obligatorias, y los módulos nuevos se crean con sus tareas Gradle
(`gm`, `guc`, `gda`, `gep`, `gh`).

---

## 7. Qué entrega

Al final, Builder responde con un estado y la evidencia:

```text
Estado: completed
Comportamiento: el total conserva dos decimales y aplica descuento antes del impuesto.
Archivos: src/pricing.ts, tests/pricing.test.ts
Comprobaciones: npm test -- pricing.test.ts (8 passed); npm run typecheck (passed)
Límites: no se ejecutó la integración con el proveedor porque no hay credencial local.
```

| Estado | Significa |
|---|---|
| `completed` | Lo pedido está terminado y comprobado |
| `partial` | Hay una entrega útil, pero quedan criterios o comprobaciones pendientes, que se listan |
| `blocked` | No puede seguir sin un insumo o una capacidad que falta |

Si una comprobación obligatoria no se pudo ejecutar (falta un runtime, un servicio
o una credencial), Builder separa "implementado" de "verificado" y no declara
`completed`. Un mock no cuenta como prueba de integración real.

---

## 8. Revisión con code-review

Builder usa la skill [code-review](../code-review/README.md) como revisor
independiente:

| Rigor | Revisión con code-review |
|---|---|
| Ligero | Opcional |
| Estándar | Recomendada antes de `completed` |
| Reforzado | Obligatoria: sin veredicto `aprobado` o `aprobado-con-observaciones`, Builder entrega `partial` |

```
Builder implementa ─► valida ─► code-review revisa ─► reporte con hallazgos
      ▲                                                      │
      └──── corrige los hallazgos aceptados ◄────────────────┘
```

Builder le entrega el ID del cambio y su expediente, no la conclusión que espera.
Si el código cambia después del veredicto, la revisión queda vencida y hay que
volver a revisar.

---

## 9. Lugar en el pipeline del kit

```
janus ─► epicureo ─► specter ─► archi ─► (genesis) ─► builder ─► ranger
                        │                                ▲
                        └──── HU / TT en resources/ ─────┘
```

- **Entra:** las HU y TT de `specter` (`resources/functional/hu/*.md`) o issues de
  Jira, y la arquitectura de `archi`.
- **Usa como verdad del proyecto:** `resources/architecture/overview.md`,
  `stack.md`, `resources/design/data-model.md`, `api.md` y `openapi.yaml`. Los
  actualiza de forma incremental; nunca los regenera desde cero.
- **Sale hacia:** `ranger` para la estrategia y las suites de QA, y `code-review`
  para la revisión.

---

## 10. Consejos para sacarle provecho

1. **Dale la fuente funcional.** Una HU con criterios de aceptación produce un
   cambio más preciso que una frase suelta.
2. **Dile qué no debe tocar.** Si hay restricciones (no cambiar el contrato de la
   API, no agregar dependencias), menciónalas en el encargo.
3. **Ten el stack ejecutable.** Sin JDK, Node o Go instalados, las comprobaciones
   quedan como `not_run` y el cambio no puede cerrarse como `completed`.
4. **Pide `explore` si hay incertidumbre.** Es más barato confirmar la viabilidad
   que deshacer una feature construida sobre un supuesto falso.
5. **Para continuar otro día, usa `resume`.** Builder reconcilia el código, los
   documentos y el estado de Git antes de seguir.

---

## 11. Instalar en otro proyecto

```bash
python <skill-root>/scripts/install_builder.py install --destination <proyecto>/.agents/skills/builder
python <skill-root>/scripts/install_builder.py verify  --destination <proyecto>/.agents/skills/builder
python <skill-root>/scripts/install_builder.py install --destination <destino> --update   # actualizar
```

Instala siempre el paquete completo; `verify` comprueba los hashes de la copia.
Detalle en [distribution.md](references/distribution.md).

---

## 12. Evaluar y mantener la skill

Requiere Python 3.11+ (solo biblioteca estándar). Ejecuta los candidatos solo en un
entorno aislado.

```bash
# Pruebas de los scripts
python -m unittest discover -s <skill-root>/tests -p "test_*.py" -v

# Caso de evaluación: preparar, ejecutar el agente y comprobar
python <skill-root>/scripts/evaluate_builder.py prepare bugfix <eval-root>/builder-run-01
#   ejecuta Builder sobre <eval-root>/builder-run-01
python <skill-root>/scripts/evaluate_builder.py check bugfix <eval-root>/builder-run-01
```

Hay fixtures para Python, Go (`go-*`), Angular (`ng-*`) y Java (`java-*`), más un
set de routing y campañas que comparan control, versión anterior y candidata. Ver
[behavioral-evaluation.md](references/behavioral-evaluation.md). Que el frontmatter
y los enlaces sean válidos no demuestra que la skill funcione: hay que medir sus
decisiones en proyectos aislados.

---

## 13. Estructura del paquete

```
builder/
├── SKILL.md                    Flujo, modos, invariantes y cierre
├── README.md                   Esta guía
├── agents/openai.yaml          Metadatos para Codex
├── references/
│   ├── implementation-modes.md       Modos feature/extend/bugfix/refactor/integrate/explore
│   ├── spec-and-evidence.md          Spec, criterios AC y evidencia por rigor
│   ├── contracts-and-data.md         Interfaces, persistencia y compatibilidad
│   ├── validation.md                 Validación por riesgo
│   ├── review-and-debugging.md       Diagnóstico, revisión y recepción de hallazgos
│   ├── resume-and-coordination.md    Reanudación y delegación
│   ├── boundaries-and-sources.md     Ownership y conflictos entre fuentes
│   ├── sdd-interoperability.md       OpenSpec y Spec Kit
│   ├── ui-with-design-system.md      UI con sistema de diseño declarado
│   ├── scaffold-clean-architecture.md
│   ├── stacks/ (go, angular, java-spring)
│   ├── work-tracking-mcp.md          Tablero opcional Jira/Azure DevOps por MCP
│   ├── distribution.md
│   └── behavioral-evaluation.md
├── assets/ (plantillas .mcp.json, comentario de cierre, registro del tablero)
├── scripts/
│   ├── install_builder.py · evaluate_builder.py
│   └── go_toolkit.py · angular_toolkit.py · spring_toolkit.py
├── evaluations/ (casos, fixtures, oráculos por stack, routing)
└── tests/
```
