# Guía de modelo de amenazas y requisitos de seguridad

## Índice

1. [Propósito y frontera con DevSecOps](#1-propósito-y-frontera-con-devsecops)
2. [Cuándo generar `19.1`](#2-cuándo-generar-191)
3. [Fuentes mínimas](#3-fuentes-mínimas)
4. [Método de análisis](#4-método-de-análisis)
5. [Baseline OWASP para aplicaciones agentic](#5-baseline-owasp-para-aplicaciones-agentic)
6. [Estructura obligatoria del artefacto](#6-estructura-obligatoria-del-artefacto)
7. [Catálogo de amenazas `THR-xxx`](#7-catálogo-de-amenazas-thr-xxx)
8. [Catálogo de requisitos `SEC-xxx`](#8-catálogo-de-requisitos-sec-xxx)
9. [Trazabilidad con el diseño](#9-trazabilidad-con-el-diseño)
10. [Contrato de entrega a Vulcano](#10-contrato-de-entrega-a-vulcano)
11. [Reglas por escenario](#11-reglas-por-escenario)
12. [Diagramas](#12-diagramas)
13. [Criterios de cierre](#13-criterios-de-cierre)

## 1. Propósito y frontera con DevSecOps

`19.1-Modelo-de-Amenazas-y-Requisitos-de-Seguridad_<Proyecto>.md` posee el análisis de
seguridad **arquitectónica** del sistema. Convierte exposición, activos, flujos y amenazas en
requisitos verificables que condicionan contenedores, APIs, datos, despliegue y decisiones.

`archi` es responsable de:

- activos, clasificación de datos y objetivos de protección;
- actores, superficies de ataque y fronteras de confianza;
- amenazas, escenarios de abuso y riesgo inherente/residual;
- controles requeridos por diseño y criterios arquitectónicos de aceptación;
- trazabilidad `THR-xxx → SEC-xxx → CT/API/OP/DA/TP/QA → validación`;
- condiciones que se entregan a seguridad, desarrollo, plataforma y Vulcano.

Vulcano es responsable de **operacionalizar** los `SEC-xxx` aplicables mediante DevSecOps:
herramientas, etapas de pipeline, SAST/DAST/SCA/IAST, secret e image scanning, umbrales de
bloqueo, SLA de remediación, SBOM, firma/provenance, policy as code, configuración de runners,
gestión operativa de secretos y evidencia continua. `19.1` no selecciona ni duplica esos
mecanismos. Puede indicar la clase de evidencia esperada, pero la implementación pertenece a
`resources/devops-strategy/08-security.md` y sus documentos dependientes.

## 2. Cuándo generar `19.1`

Genera `19.1` cuando exista al menos una de estas condiciones:

- APIs, webhooks, eventos, archivos o interfaces expuestas a terceros;
- datos personales, sensibles, financieros, de salud, credenciales o información regulada;
- identidad, pagos, administración privilegiada o autorización compleja;
- multi-tenancy, aislamiento entre clientes o separación fuerte entre dominios;
- una o más fronteras de confianza entre zonas, redes, nubes, organizaciones o runtimes;
- integraciones externas no controladas, plugins, carga de archivos o contenido activo;
- servicios Internet-facing, aplicaciones móviles o frontend con riesgo relevante de cliente;
- IA generativa, agentes, herramientas, recuperación de conocimiento o datos no confiables;
- `QA-xx`, restricción, hallazgo AS-IS, PoC o riesgo material de seguridad;
- requerimiento normativo, contractual o explícito de InfoSec.

Si ninguna condición aplica, no generes un archivo vacío. En la subsección Seguridad de `19`
registra `No aplica`, el análisis que sustenta la decisión y quién debe revisarla si cambia la
exposición.

La presencia de comportamiento **agentic** hace `19.1` obligatorio. Usa la clasificación canónica de `10.1`: un sistema es agentic cuando al menos un componente planifica o itera para alcanzar una meta, selecciona/invoca herramientas, conserva memoria que influye decisiones, ejecuta acciones con efecto externo o delega/se comunica con otros agentes. Una inferencia puntual o workflow determinístico que solo llama a un modelo no activa por sí solo esta regla.

## 3. Fuentes mínimas

Lee y enlaza, cuando existan:

- `02` alcance, actores, objetivos y sistemas externos;
- `03` restricciones regulatorias, corporativas y de datos;
- `05` escenarios de Seguridad y atributos que puedan degradarse por un ataque;
- `06` funcionalidades arquitectónicamente significativas;
- `10`/`10.1` configuración y baseline seleccionados;
- `14`, `14.00` y `14.xx` contenedores, interfaces, operaciones y contratos;
- `15` flujos críticos y rutas de error;
- `16`/`16.xx` ownership, clasificación, retención y flujo de datos;
- `17` topología, identidades, zonas y servicios cloud;
- `18` tácticas/patrones y `20` decisiones;
- evidencia reproducible de código, configuración, IAM, IaC o pruebas en Caso B.

No inventes controles por una tecnología presumida. Registra la falta de evidencia en `04` o
como hallazgo de `21` según corresponda.

## 4. Método de análisis

Usa un método explícito y proporcional. STRIDE es el punto de partida recomendado para
software general; complementa con abuso de negocio, OWASP ASVS/API Security, privacidad o
amenazas de IA cuando el alcance lo exija. La referencia orienta categorías, no sustituye el
razonamiento contextual.

1. Delimita sistema, ambientes y alcance excluido.
2. Identifica activos y objetivos de confidencialidad, integridad, disponibilidad, privacidad
   y accountability.
3. Modela actores, entradas, salidas, almacenes y fronteras de confianza.
4. Recorre cada flujo crítico y frontera; formula amenazas concretas con precondición y activo.
5. Estima probabilidad e impacto con una escala declarada; no uses números sin definición.
6. Relaciona cada amenaza material con uno o más `SEC-xxx`.
7. Aplica los requisitos a `CT-xx`, `API-xxx`, `API-xxx-OP-xxx`, datos o zonas específicas.
8. Registra verificación, owner, riesgo residual y decisión/aceptación cuando corresponda.

Para soluciones agentic ejecuta además la evaluación completa de la sección 5. STRIDE y OWASP Agentic se complementan: STRIDE recorre elementos y fronteras del sistema; `ASI01`-`ASI10` obliga a revisar riesgos propios de autonomía, herramientas, memoria, identidad, comunicación y confianza humana.

## 5. Baseline OWASP para aplicaciones agentic

Cuando `10.1` declare `Aplicabilidad agentic: Sí`, adopta explícitamente como baseline **OWASP Top 10 for Agentic Applications 2026** y registra nombre, versión, URL oficial y fecha de consulta. Fuente oficial: <https://genai.owasp.org/resource/owasp-top-10-for-agentic-applications-for-2026/>.

Este baseline es un marco priorizado para threat modeling y diseño, no una certificación. Escribe `Baseline adoptado` o `Evaluado contra`; nunca declares `Certificado`, `Cumple OWASP` ni cobertura global sin evidencia por categoría.

Evalúa exactamente una vez cada categoría oficial:

| ID | Categoría | Enfoque arquitectónico mínimo |
|---|---|---|
| `ASI01` | Agent Goal Hijack | Manipulación del objetivo, instrucciones y prioridades que desvía el comportamiento autorizado. |
| `ASI02` | Tool Misuse and Exploitation | Uso indebido, encadenamiento o explotación de herramientas y de sus efectos. |
| `ASI03` | Identity and Privilege Abuse | Identidades excesivas, confusión de principal, delegación insegura o abuso de privilegios. |
| `ASI04` | Agentic Supply Chain Vulnerabilities | Procedencia, integridad y confianza de modelos, prompts, skills, plugins, herramientas/MCP, datos y dependencias. |
| `ASI05` | Unexpected Code Execution (RCE) | Generación, interpretación o ejecución no prevista de código, comandos, plantillas o contenido activo. |
| `ASI06` | Memory and Context Poisoning | Contaminación persistente o transitoria de memoria, contexto, RAG, instrucciones o estado compartido. |
| `ASI07` | Insecure Inter-Agent Communication | Suplantación, manipulación, replay, autorización débil o fuga en mensajes y delegaciones entre agentes. |
| `ASI08` | Cascading Failures | Propagación, loops, amplificación de costo/carga y fallos correlacionados entre agentes, herramientas y sistemas. |
| `ASI09` | Human-Agent Trust Exploitation | Sobreconfianza, persuasión, interfaz engañosa o aprobación humana sin contexto/autoridad suficiente. |
| `ASI10` | Rogue Agents | Desalineación, evasión de controles, persistencia o acciones fuera del propósito y límites autorizados. |

Incluye la sección canónica `## Evaluación OWASP Top 10 for Agentic Applications 2026` y esta matriz:

```markdown
| ASI | Estado | Escenario y justificación | Alcance agentic | `THR-xxx` | `SEC-xxx` | `TP/DA` | Validación/evidencia | Riesgo residual | Owner/disposición |
|---|---|---|---|---|---|---|---|---|---|
| ASI01 | Aplicable | [...] | Agente/herramienta/memoria/frontera | THR-001 | SEC-001 | TP-001 / DA-001 | [criterio o evidencia] | [nivel y enlace a 21] | [owner] |
```

Estados permitidos:

- `Aplicable`: formula al menos un escenario contextual `THR-xxx`, uno o más controles verificables `SEC-xxx`, alcance concreto, `TP/DA`, validación, riesgo residual y owner.
- `Considerado y descartado`: explica qué parte del diseño se revisó, por qué el escenario no es plausible y qué cambio obligaría a reevaluarlo.
- `No aplica`: aporta motivo estructural verificable; no uses ausencia de evidencia o controles como motivo.

Las diez filas son obligatorias. No copies descripciones genéricas como amenazas del proyecto: conviértelas en escenarios con actor, precondición, objetivo, herramienta/memoria/identidad afectada, efecto y trust boundary. Una misma amenaza puede cubrir varias categorías y una categoría puede producir varias amenazas, pero la matriz conserva la disposición de cada `ASI`.

Aplica mínima agencia: evita autonomía que no responda a un driver, restringe herramientas y privilegios por tarea, limita tiempo/iteraciones/costo, separa identidades, hace observables objetivo/pasos/invocaciones/resultados, exige aprobación humana por riesgo y provee revocación, pausa, fallback y kill switch. No registres razonamiento interno sensible; conserva eventos y decisiones auditables suficientes.

Si `Topología agentic: Multiagente`, complementa el análisis con **OWASP Multi-Agentic System Threat Modeling Guide v1.0** (<https://genai.owasp.org/resource/multi-agentic-system-threat-modeling-guide-v1-0/>), modela cada identidad/delegación/canal/frontera A2A y marca `ASI07` como `Aplicable`. Para profundizar escenarios y controles usa **OWASP Agentic AI – Threats and Mitigations** (<https://genai.owasp.org/resource/agentic-ai-threats-and-mitigations/>). Usa OWASP LLM Top 10 para riesgos generales del componente LLM sin duplicar amenazas ya trazadas.

## 6. Estructura obligatoria del artefacto

El documento contiene:

1. propósito, estado, versión, owner y fecha;
2. alcance incluido/excluido y fuentes revisadas;
3. método, escala de riesgo y supuestos;
4. activos y clasificación de datos;
5. actores, superficies de ataque y fronteras de confianza;
6. diagrama de amenazas o flujo de datos cuando aporte claridad;
7. catálogo `THR-xxx`;
8. escenarios de abuso prioritarios;
9. catálogo `SEC-xxx` y criterios de aceptación;
10. matriz de trazabilidad con diseño, decisiones, pruebas y riesgos;
11. riesgos residuales, excepciones y aceptaciones;
12. contrato de entrega a Vulcano;
13. criterios de cierre.

Cuando la solución sea agentic, agrega después del método y antes del catálogo `THR-xxx`:

- declaración del baseline OWASP, versión, fuente y fecha;
- inventario de runtime de agentes, modelos, prompts/policies, herramientas/MCP, identidades, memoria/contexto, sistemas destino, supervisores humanos y canales A2A;
- diagrama agentic de trust boundaries;
- matriz completa `ASI01`-`ASI10`;
- declaración de mínima agencia, autorizaciones humanas, contención y kill switch.

## 7. Catálogo de amenazas `THR-xxx`

Usa IDs estables y agrega nuevas amenazas al final; no renumeres las cerradas.

| Campo | Contenido requerido |
|---|---|
| ID y nombre | `THR-001` + formulación breve y específica |
| Categoría | STRIDE, abuso de negocio, privacidad, IA u otra taxonomía declarada |
| Actor y precondición | Quién puede producirla y qué necesita |
| Activo/flujo | Dato, operación, componente o capacidad afectada |
| Superficie/frontera | Punto de entrada y trust boundary cruzada |
| Escenario | Secuencia plausible; evita etiquetas genéricas como “hackeo” |
| Impacto/probabilidad | Valor según la escala definida y justificación |
| Riesgo inherente | Resultado antes de controles |
| Requisitos asociados | Uno o más `SEC-xxx` o aceptación explícita |
| Riesgo residual | Resultado esperado después del diseño; enlaza `21` si sigue material |
| Estado y owner | Abierta, mitigada, aceptada o descartada con responsable/evidencia |

## 8. Catálogo de requisitos `SEC-xxx`

Un `SEC-xxx` expresa una propiedad o comportamiento verificable del sistema. No es el nombre
de una herramienta ni una frase como “cumplir OWASP”.

```markdown
### SEC-001: Autorización por tenant en operaciones administrativas

- **Drivers:** THR-003, QA-04, RN-D02
- **Alcance:** CT-03; API-006-OP-014; datos de Tenant
- **Requisito:** Toda operación administrativa debe resolver el tenant desde una identidad
  autenticada y rechazar un tenant aportado solo por el payload cuando no coincida.
- **Criterio de aceptación:** intentos cross-tenant con identidad válida reciben denegación y
  no producen lectura, escritura ni evento de dominio.
- **Clase de evidencia:** prueba de autorización negativa + registro de auditoría correlacionado
- **Owner de diseño:** Arquitectura/Seguridad de aplicación
- **Destino operativo:** Vulcano — testing/security; no define herramienta
- **Estado:** Definido / Implementado / Validado / Excepción aceptada
```

Cada requisito incluye: ID, drivers, alcance, redacción normativa, criterio observable, clase
de evidencia, owner, destino y estado. Distingue:

- **Definido:** diseño y aceptación completos, todavía sin implementación;
- **Implementado:** existe evidencia técnica reproducible;
- **Validado:** evidencia satisface el criterio;
- **Excepción aceptada:** autoridad, motivo, compensación y fecha de revisión explícitos.

## 9. Trazabilidad con el diseño

Incluye esta matriz sin duplicar el detalle de los documentos dueños:

| `THR-xxx` | `SEC-xxx` | `QA/FAS/RN/RT` | `CT/API/OP/Dato/Zona` | `DA/TP` | Validación arquitectónica | Riesgo residual |
|---|---|---|---|---|---|---|

Propaga los requisitos:

- `14.00` registra seguridad aplicable a cada API/operación;
- `14.xx` explica cómo el contenedor satisface los `SEC-xxx` de su alcance;
- `15` muestra rutas de denegación, expiración o fallo relevantes;
- `16.xx` aplica clasificación, minimización, cifrado, retención y aislamiento;
- `17` materializa trust boundaries, identidad, red y protección de servicios;
- `18` enlaza tácticas/patrones que implementan el requisito;
- `20` conserva decisiones con alternativas y trade-offs;
- `21` posee riesgos residuales y deuda.

Para agentic propaga además:

- `10.1` define runtime, herramientas, identidad, memoria, autonomía, supervisión, observabilidad y contención esperadas en el arquetipo;
- `14`/`14.xx` materializan agentes, tool adapters, policy/guardrail enforcement, memoria y sistemas destino con IDs y trust boundaries;
- `14.00` cataloga herramientas o interfaces invocables con identidad, autorización, schema, efectos e idempotencia;
- `15` muestra aprobación/denegación, timeout, revocación, fallback, kill switch y fallos agentic críticos;
- `18` explica mínima agencia, guardrails, controles de herramientas/memoria/identidad, HITL y aislamiento de fallos como `TP-xxx`;
- `20` registra elecciones de autonomía, herramientas, memoria, modelos, multiagente y riesgo aceptado;
- `25` audita las diez disposiciones `ASI`, su trazabilidad y ausencia de categorías materiales huérfanas.

## 10. Contrato de entrega a Vulcano

Termina con una tabla consumible por Vulcano:

| `SEC-xxx` | Scope | Criterio de aceptación | Clase de evidencia esperada | Aplicabilidad DevSecOps | Documento destino | Estado de handoff |
|---|---|---|---|---|---|---|
| SEC-001 | CT-03 / API-006-OP-014 | Prueba cross-tenant denegada | Prueba negativa + auditoría | Sí | `08-security.md` / `07-continuous-testing.md` | Listo |

Valores de aplicabilidad: `Sí`, `Parcial` o `No requiere automatización`, siempre con motivo.
Vulcano conserva el ID y el criterio; puede dividir su operacionalización en varios controles,
pero no cambia ni renumera el requisito. Si detecta contradicciones, devuelve el hallazgo a
`19.1`/`20` en vez de crear una segunda verdad.

La aprobación de arquitectura exige un handoff completo, no evidencia de un pipeline que aún
no existe. La evidencia operacional se evalúa después en Vulcano/Bob. En AS-IS sí se enlaza la
evidencia observable disponible y se separan faltantes como deuda o riesgo.

### Retroalimentación desde código (`aegis`)

Si la skill `aegis` verificó el código o la IaC contra este artefacto, recibe de ella:

- el estado observado de cada `SEC-xxx` (`implementado-con-evidencia`, `ausente`,
  `ineficaz`, `desconocido`) con `archivo:línea`; úsalo como evidencia para pasar a
  `Implementado`/`Validado`, nunca como cambio automático de estado;
- amenazas observadas no modeladas como `THR-propuesta-NN`; si se aceptan, recibe un
  `THR-xxx` definitivo al final del catálogo y se aplica la reapertura incremental;
- contradicciones diseño ↔ código, que se resuelven en `19.1`/`20` (decisión) o como
  defecto de implementación devuelto a builder.

`aegis` no edita `19.1` ni renumera IDs; archi conserva el ownership.

## 11. Reglas por escenario

- **Caso A:** modela amenazas contra el TO-BE; permite `SEC-xxx: Definido`; no afirma controles
  implementados. Handoff `Listo` significa listo para operacionalizar.
- **Caso B:** cada amenaza/control observado enlaza código, configuración, IAM, IaC, contrato o
  prueba. Distingue control ausente, desconocido e ineficaz.
- **Caso C:** conserva trazabilidad `AS-IS → TO-BE`; explica qué amenaza disminuye, aparece o
  cambia y qué requisito se incorpora, reemplaza o mantiene.

En los tres escenarios, si la solución es agentic las diez categorías se evalúan. En B cada `Aplicable` distingue control observado, ausente o desconocido con evidencia reproducible. En C la matriz explica cambios de aplicabilidad o riesgo `AS-IS → TO-BE`.

## 12. Diagramas

Genera Mermaid cuando existan tres o más fronteras relevantes, flujos de datos sensibles,
identidades delegadas o una cadena de abuso difícil de entender en tabla. Usa `flowchart` para
flujo de datos/trust boundaries, `sequenceDiagram` para abuso y rechazo, y `stateDiagram-v2`
para ciclos de credenciales o autorización. Marca las fronteras y datos sensibles; no generes
un diagrama decorativo ni dupliques `14`, `15` o `17`.

Para soluciones agentic genera obligatoriamente al menos un Mermaid que muestre runtime del agente, modelo, herramientas, identidades efectivas, memoria/contexto, sistemas destino, supervisión humana y fronteras de confianza aplicables. Si hay multiagente, representa agentes y canales/delegaciones A2A. El diagrama puede enlazar una vista propietaria de `14`/`15` cuando ya contenga exactamente esta información; en ese caso no lo dupliques y registra el enlace y la justificación.

## 13. Criterios de cierre

El artefacto solo cumple cuando:

- alcance, fuentes, método y escala de riesgo están explícitos;
- activos, datos, superficies y fronteras cubren el diseño material;
- cada amenaza prioritaria tiene actor, escenario, impacto, probabilidad y disposición;
- cada amenaza material se relaciona con `SEC-xxx` o aceptación de riesgo autorizada;
- cada `SEC-xxx` tiene alcance, criterio verificable, evidencia esperada, owner y estado;
- la trazabilidad coincide con `14`-`21` y no hay IDs huérfanos;
- los riesgos residuales están en `21` y las decisiones/excepciones en `20`;
- el handoff a Vulcano cubre todos los `SEC-xxx` aplicables sin prescribir herramientas;
- en B/C la evidencia y transición son reproducibles y no se presenta intención como hecho.
- declara `Aplicabilidad agentic` consistente con `10.1`; si es `Sí`, registra baseline, versión, fuente y fecha de OWASP Top 10 for Agentic Applications 2026;
- si es agentic, `ASI01`-`ASI10` aparecen exactamente una vez en la matriz con estado válido y justificación; todo `Aplicable` enlaza alcance, `THR`, `SEC`, `TP/DA`, validación, riesgo residual y owner;
- si es agentic, mínima agencia, identidad, herramientas, memoria, límites, supervisión, observabilidad, contención y kill switch están diseñados o tienen disposición explícita;
- si es multiagente, se aplica la guía multiagente, `ASI07` queda `Aplicable` y cada canal/delegación A2A tiene identidad, autenticidad, autorización, límites y aislamiento;
- no declara certificación o cumplimiento OWASP global; demuestra cobertura por categoría y riesgo.
