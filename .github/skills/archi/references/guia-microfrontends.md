# Guía: Evaluación y diseño de Microfrontends

Usa esta guía cuando exista una experiencia web compleja, varios equipos de producto, necesidad de despliegue independiente por capacidad o evidencia AS-IS de composición de interfaces. Microfrontends es un patrón arquitectónico candidato, no una recomendación por defecto ni un sinónimo de componentes UI.

## Contenido

1. [Decidir si aplica](#1-decidir-si-aplica)
2. [Comparar alternativas en 09](#2-comparar-alternativas-en-09)
3. [Seleccionar y registrar el arquetipo](#3-seleccionar-y-registrar-el-arquetipo)
4. [Modelar en C4](#4-modelar-en-c4)
5. [Diseñar shell y microfrontends](#5-diseñar-shell-y-microfrontends)
6. [Flujos, estado y APIs](#6-flujos-estado-y-apis)
7. [Despliegue y operación](#7-despliegue-y-operación)
8. [Tácticas, decisión y validación](#8-tácticas-decisión-y-validación)
9. [Criterios de cierre](#9-criterios-de-cierre)

## 1. Decidir si aplica

Evalúa Microfrontends solo cuando uno o más drivers verificables no puedan resolverse suficientemente con una SPA modular o módulos publicados juntos:

- dos o más equipos autónomos necesitan ownership y cadencias de entrega diferentes;
- existen capacidades de negocio con fronteras de UI estables y evolución independiente;
- una parte de la experiencia requiere migración incremental, aislamiento de fallos o rollback propio;
- diferentes ciclos regulatorios, de seguridad o disponibilidad justifican despliegues separados;
- el AS-IS ya contiene aplicaciones independientes que deben componerse durante una transición.

Evita o descarta el patrón cuando:

- un solo equipo controla la experiencia y puede coordinar una única entrega;
- las fronteras de dominio/UI son inestables o cambian en cada iteración;
- navegación, estado y componentes están fuertemente acoplados;
- el costo de plataforma, pruebas, observabilidad y soporte supera el beneficio de autonomía;
- se busca únicamente usar varios frameworks, repositorios o nombres de equipo;
- una SPA modular, librerías internas y lazy loading satisfacen los mismos `QA-xx`.

No uses cantidad de pantallas, tamaño del repositorio ni presencia de microservicios como justificación suficiente. No generes un microfrontend por microservicio ni por bounded context de forma automática.

Registra los drivers en `05`/`06` y formula preguntas sobre equipos, frecuencia de release, ownership, fallos, UX y migración. Si falta evidencia, conserva Microfrontends como candidato y escribe `Missing evidence`; no lo selecciones.

## 2. Comparar alternativas en 09

Si la composición frontend cambia materialmente topología, entrega, operación o costo, compara en `09` al menos la recomendada y una alternativa razonable:

| Alternativa | Unidad de entrega | Uso típico |
|---|---|---|
| SPA modular | Una aplicación desplegable con módulos internos | Un equipo o release coordinado; menor complejidad operativa |
| Aplicaciones por ruta | Aplicaciones independientes separadas por URL/ruta | Capacidades con navegación y ciclos de vida suficientemente independientes |
| Microfrontends runtime | Shell/host compone remotes en navegador | Experiencia integrada con releases independientes y contratos runtime |
| Composición server-side/edge | Servidor o edge compone fragmentos | Primera carga/SEO o control central de composición con ownership distribuido |
| Híbrida | Combina SPA modular y microfrontends solo en scopes justificados | Transición o autonomía localizada |

Module Federation, import maps, Web Components, single-spa u otra herramienta son mecanismos posibles después de elegir el modo de composición; no son alternativas de negocio por sí solos.

Agrega a cada alternativa una matriz frontend:

```markdown
| Canal / capacidad UI | Owner/equipo | Unidad de build | Unidad de despliegue | Composición | Estado compartido | API/BFF | Driver | Condición de consolidación/extracción |
|---|---|---|---|---|---|---|---|---|
| Web / Nómina | Equipo Nómina | Remote Nómina | Independiente | Runtime en Shell RR. HH. | Solo sesión/tema | BFF Web compartido | Release regulatorio propio | Consolidar si desaparece autonomía |
```

Evalúa bajo los mismos criterios y evidencia:

- autonomía real y capacidad de los equipos;
- independencia de build, despliegue, rollback y operación;
- estabilidad de fronteras y ownership funcional;
- consistencia UX, accesibilidad, i18n y design system;
- rendimiento: carga inicial, bundles duplicados, caché y navegación;
- contratos, compatibilidad entre versiones y estado compartido;
- autenticación, autorización, CSP, supply chain y aislamiento de fallos;
- observabilidad, pruebas integradas, soporte y costo de plataforma.

Una alternativa Microfrontends queda incompleta si no identifica shell/compositor, scopes, owners, modo de composición, unidades desplegables, contratos y estrategia de rollback.

## 3. Seleccionar y registrar el arquetipo

En `10` conserva la decisión humana y la matriz frontend aprobada. Registra alcance exacto: Microfrontends puede aplicar solo al portal web o a capacidades concretas, mientras otros canales permanecen consolidados.

En `10.1` registra:

- subarquetipo frontend: SPA modular, aplicaciones por ruta, Microfrontends runtime, composición server-side/edge o híbrida;
- shell/host/compositor y cada unidad desplegable prevista u observada;
- framework/runtime y baseline de compatibilidad sin inventar versiones;
- mecanismo de composición y resolución de versiones;
- design system, identidad/sesión, telemetría y librerías compartidas;
- unidad de repositorio/build/despliegue, capacidad de entrega independiente, hosting/CDN, owner y estado de adopción; enlaza pipeline AS-IS/Vulcano cuando exista;
- `TP-xxx`, `DA-xxx`, incertidumbres y PoC cuando apliquen.

No declares diversidad tecnológica como beneficio automático. Toda excepción de framework agrega costo de seguridad, experiencia, soporte, observabilidad y dependencias, y requiere driver/decisión explícitos.

## 4. Modelar en C4

Aplica estas reglas de clasificación:

- **Contenedor `CT-xx`:** shell o microfrontend construido, versionado y desplegado independientemente, con boundary runtime y owner claros.
- **Componente de `14.xx`:** módulo, feature library o paquete compilado y publicado junto con otro frontend, aunque el equipo lo llame microfrontend.
- **Sistema externo `EXT-xx`:** aplicación fuera del ownership del sistema, aunque se incruste o enlace desde el shell.

En C4 Nivel 2 muestra shell/compositor, microfrontends `CT-xx`, APIs/BFF y sistemas externos cuando sean contenedores reales. Etiqueta el modo de composición y no dibujes cada componente visual.

El shell normalmente es significativo si posee routing, autenticación/sesión, descubrimiento/carga de remotes, layout, error boundaries, telemetría o compatibilidad. Cada microfrontend significativo obtiene su `14.xx`; uno trivial puede quedar clasificado como no significativo con motivo, pero conserva su fila `CT-xx` si es desplegable.

## 5. Diseñar shell y microfrontends

Además del contenido general de `14.xx`, documenta para el shell:

- routing, navegación y deep links;
- descubrimiento, carga, versionado y fallback de remotes;
- sesión, permisos, feature flags, configuración y consentimiento;
- layout, design tokens, accesibilidad, i18n y manejo de errores;
- telemetría correlacionada, degradación y compatibilidad.

Para cada microfrontend documenta:

- capacidad UI y límites incluidos/excluidos;
- owner, repositorio, build, despliegue y rollback;
- rutas, elementos públicos y contratos con el shell;
- APIs/BFF consumidos y política de autorización;
- eventos/UI contracts permitidos y dependencias prohibidas;
- estado local, caché, persistencia/offline y sincronización;
- dependencias compartidas, compatibilidad y presupuesto de bundle;
- pruebas unitarias, de contrato, integración y journeys críticos;
- fallos de carga/runtime, aislamiento, fallback y observabilidad.

Evita imports directos entre remotes, acceso al estado interno de otro microfrontend y eventos globales sin esquema/owner. Prefiere contratos pequeños, versionados y observables.

## 6. Flujos, estado y APIs

En `15` documenta los flujos críticos que atraviesen shell, microfrontends y APIs, incluyendo:

- bootstrap, autenticación y carga autorizada;
- navegación entre capacidades y preservación de contexto;
- comunicación por URL, eventos o contratos explícitos;
- remote incompatible, no disponible o con error runtime;
- despliegue/rollback cuando produce coexistencia de versiones.

En `16`/`16.xx`, un frontend no es fuente de verdad de datos de negocio salvo decisión explícita. Documenta estado de sesión/UI, caché, offline, sincronización, clasificación de datos y borrado. Evita un store global que acople los ciclos de entrega; si existe, registra contrato, owner y compatibilidad.

Un BFF no se crea automáticamente por microfrontend. Evalúa BFF por canal o capacidad solo cuando adaptación, seguridad, agregación o autonomía lo justifiquen; evita duplicación de lógica de negocio y proliferación uno-a-uno sin driver.

## 7. Despliegue y operación

En `17` registra por shell y microfrontend:

- hosting, CDN/edge, dominios/rutas y ambientes;
- capacidad de entrega/promoción independiente y requisitos de integridad, firma o SBOM cuando apliquen; enlaza la estrategia Vulcano si ya existe;
- estrategia de caché e invalidación;
- despliegue independiente, canary/feature flag y rollback;
- compatibilidad shell-remote y ventana de versiones soportadas;
- CSP, CORS, SRI, secretos inexistentes en cliente y supply chain;
- logs/eventos, errores frontend, Web Vitals, trazas y correlación con backend;
- SLO/alerta, runbook, soporte y costo por unidad/equipo.

`archi` define la autonomía requerida, la unidad desplegable, compatibilidad, rollback y
propiedades de seguridad. Vulcano define repositorios/pipelines, stages, scanners, generación
de SBOM, firma/provenance, umbrales y evidencia operativa. En AS-IS, `archi` puede citar el
pipeline observado como evidencia de independencia sin convertirlo en especificación DevSecOps.

Si todos los microfrontends deben desplegarse siempre juntos, registra la contradicción con el driver de independencia y reevalúa una SPA modular.

## 8. Tácticas, decisión y validación

Registra Microfrontends como patrón arquitectónico `TP-xxx` en `18` solo cuando esté seleccionado, observado o sea arquitectónicamente significativo. La ficha enlaza `09`, `10`, `10.1`, todos los `CT-xx`, despliegue y una `DA-xxx` con alternativas/consecuencias.

Valida al menos:

| Área | Evidencia/medida esperada |
|---|---|
| Autonomía | A/C: ownership, capacidad de entrega independiente y rollback por unidad con criterio de aceptación; B/implementado: releases/rollbacks independientes observables sin coordinación obligatoria no declarada |
| Compatibilidad | Contract tests o matriz shell-remote y comportamiento ante versión incompatible |
| Rendimiento | Presupuesto acordado de JS/CSS, carga inicial, navegación y Web Vitals medidos |
| Resiliencia | Remote ausente/fallido queda aislado y ofrece fallback verificable |
| Seguridad | `SEC-xxx` aplicables, autorización, CSP/SRI o control equivalente y requisitos de supply chain; Vulcano operacionaliza pruebas y gates |
| UX | Design system, accesibilidad, navegación, foco e i18n consistentes |
| Operación | Telemetría identifica versión, owner y correlación de cada unidad; existe rollback/runbook |
| Entrega | Arquitectura: independencia/promoción/rollback requeridos; AS-IS o Vulcano: pipeline y evidencia de despliegue por unidad |

No inventes presupuestos ni umbrales. Derívalos de `QA-xx`, estándares corporativos o QAW. Una PoC es obligatoria cuando la composición, compatibilidad, rendimiento, seguridad o experiencia del equipo tenga incertidumbre crítica.

En A/C preimplementación, `Seleccionado` exige diseño completo, responsables y criterios de aceptación, pero no evidencia de producción inexistente. Reserva `Implementado` para código/configuración/pipelines observables y `Validado` para pruebas con umbrales. En B exige evidencia del repositorio, despliegue o telemetría para toda afirmación material.

## 9. Criterios de cierre

Microfrontends puede quedar `Seleccionado`/`Cumple` únicamente cuando:

- [ ] Existe un driver verificable que una SPA modular no satisface suficientemente.
- [ ] `09` compara al menos una alternativa más simple bajo los mismos criterios.
- [ ] `10` delimita canales/capacidades y registra selección humana.
- [ ] `10.1` registra subarquetipo, mecanismo, baseline, owners, capacidad de entrega y hosting; enlaza pipeline Vulcano/AS-IS cuando exista.
- [ ] Cada unidad independiente está clasificada como `CT-xx`; los módulos no desplegables permanecen como componentes.
- [ ] Shell y microfrontends significativos tienen `14.xx` con contratos, estado, seguridad, UX, fallos y pruebas.
- [ ] `15` cubre journeys y rutas de error de composición; `16` gobierna estado/caché aplicable.
- [ ] `17` demuestra despliegue, compatibilidad, caché, observabilidad y rollback por unidad.
- [ ] `18`/`20` registran patrón, decisión, trade-offs y validación; `21` conserva riesgos residuales.
- [ ] Las incertidumbres críticas tienen PoC o aceptación explícita de riesgo.
- [ ] `25` verifica evidencia y ausencia de contradicciones entre autonomía declarada y entrega real.

Si falta un criterio aplicable, conserva el patrón en `Propuesta` o el artefacto en `No cumple`; no uses `Cumple con observaciones` para encubrir una frontera, owner, contrato o estrategia de despliegue ausente.
