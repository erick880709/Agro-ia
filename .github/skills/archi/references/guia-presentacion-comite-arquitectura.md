# Guía: Presentación para Comité de Arquitectura

Esta guía define cómo generar `25.1-Presentacion-Comite-Arquitectura_<Proyecto>.html` a partir de los artefactos revisados. La presentación es una vista navegable y trazable; no es una nueva fuente de verdad ni reemplaza los documentos `01`-`25`.

## Contenido

1. [Momento y gate de generación](#momento-y-gate-de-generación)
2. [Artefactos y comandos](#artefactos-y-comandos)
3. [Principios de contenido](#principios-de-contenido)
4. [Vistas por audiencia](#vistas-por-audiencia)
5. [Secciones obligatorias](#secciones-obligatorias)
6. [Mapeo de fuentes](#mapeo-de-fuentes)
7. [Diagramas y operación sin conexión](#diagramas-y-operación-sin-conexión)
8. [Conflictos y evidencia faltante](#conflictos-y-evidencia-faltante)
9. [Criterios de cierre](#criterios-de-cierre)

## Momento y gate de generación

Genera `25.1` después de contar con una ronda de `25-Revision-Tecnica-Arquitectura.md` y antes de abrir `26-Validacion-y-Aprobacion.md`.

- **Apta para aprobación:** todos los artefactos aplicables están en `Cumple` o `Cumple con observaciones`, no hay hallazgos bloqueantes abiertos ni conflictos canónicos sin resolver y la selección humana de `10` está registrada en Casos A/C.
- **Borrador:** puede generarse para revisión temprana, pero debe mostrar de forma persistente `BORRADOR — NO APTO PARA APROBACIÓN`, los bloqueos y la evidencia faltante.
- **Aprobación:** solo se registra en `26`. La presentación nunca se autoaprueba ni convierte una recomendación en decisión humana.

Si cambia cualquier artefacto fuente después de generar la presentación, regenera el manifiesto/HTML y vuelve a ejecutar la validación. Los hashes permiten detectar una presentación obsoleta.

## Artefactos y comandos

Genera en el mismo directorio de arquitectura:

- `25.1.1-Manifiesto-Presentacion_<Proyecto>.json`: contenido estructurado, referencias y estado del gate.
- `25.1-Presentacion-Comite-Arquitectura_<Proyecto>.html`: presentación autocontenida, salvo imágenes locales exportadas.
- `25.1.2-*`, `25.1.3-*`, etc.: SVG/PNG locales derivados de diagramas canónicos cuando el navegador no pueda renderizarlos directamente.

Usa como contrato `references/esquema-presentacion-arquitectura.json`, copia y completa `assets/plantilla-manifiesto-presentacion.json`, y renderiza con `assets/plantilla-presentacion-arquitectura.html`. Elimina del manifiesto las fuentes/colecciones condicionales que no apliquen solo cuando el esquema lo permita y registra `No aplica — motivo` en la sección dueña.

```powershell
python .claude/skills/archi/scripts/generate_architecture_presentation.py `
  --manifest resources/architecture/25.1.1-Manifiesto-Presentacion_MiProyecto.json `
  --project-root . `
  --output resources/architecture/25.1-Presentacion-Comite-Arquitectura_MiProyecto.html

python .claude/skills/archi/scripts/validate_architecture_presentation.py `
  --presentation resources/architecture/25.1-Presentacion-Comite-Arquitectura_MiProyecto.html `
  --project-root .
```

Agrega `--strict` al generador cuando el resultado se vaya a presentar para aprobación. El modo estricto falla en lugar de producir una presentación aprobable con bloqueos.

## Principios de contenido

1. **Resultado primero:** abre con la decisión solicitada, recomendación, valor, costo/rango, plazo, riesgos y condiciones.
2. **Evidencia del trabajo:** muestra qué se analizó, qué se descartó, qué se decidió y cómo se validó; no presentes solo el diagrama final.
3. **Divulgación progresiva:** la vista ejecutiva explica el porqué; la de arquitectura añade el cómo y la evidencia; la completa conserva todo el detalle disponible.
4. **Trazabilidad:** cada afirmación material incluye `source.path`, `source.section` y, al generar, SHA-256 del archivo fuente.
5. **Propiedad:** `25.1` resume. `05` posee atributos, `09` alternativas, `10` selección, `10.1` arquetipo/baseline, `14` diseño, `17` despliegue, `18` tácticas, `20` decisiones y `25` la revisión.
6. **No invención:** si falta el dato, muestra `Missing evidence` y su consecuencia; no completes tecnologías, métricas, costos, fechas, responsables o estados por intuición.
7. **Lenguaje de decisión:** separa hechos, inferencias, recomendaciones, decisiones confirmadas y pendientes.

## Vistas por audiencia

El HTML incluye un selector visible y conserva las tres vistas:

| Vista | Audiencia | Pregunta que responde | Profundidad |
|---|---|---|---|
| `Ejecutiva` | Sponsor, CEO, CIO | ¿Qué se solicita, por qué ahora, cuánto cuesta y qué riesgo se acepta? | 8-12 bloques breves |
| `Arquitectura` | Comité, CTO, arquitectos, seguridad, datos, operaciones | ¿Cómo se sustenta y valida la decisión? | Matrices, diagramas y trazabilidad |
| `Completa` | Revisor técnico | ¿Cuál es toda la evidencia disponible? | Unión de las anteriores y anexos |

No generes archivos diferentes por audiencia. Un único HTML usa `?view=executive`, `?view=architecture` o `?view=complete` y permite cambiar durante la sesión.

## Secciones obligatorias

El manifiesto y la presentación cubren, en este orden:

1. **Portada y estado:** proyecto, escenario, versión, fecha, autores, estado de `25`, etiqueta de borrador y decisión solicitada.
2. **Resumen ejecutivo:** problema/oportunidad, recomendación, beneficios medibles o por validar, inversión/rango, plazo/rango y riesgos principales.
3. **Decisión requerida:** opciones concretas (`Aprobar`, `Aprobar con condiciones`, `Solicitar ajustes`), autoridad y condiciones.
4. **Trabajo realizado:** matriz de artefactos aplicables `01`-`25`, estado, evidencia y hallazgos; hitos/gates `07`, `10`, `11`-`13` y `25`.
5. **Drivers:** `OBJ-xx`, `QA-xx` priorizados, `FAS-xxx`, restricciones, QAW y trade-offs.
6. **Alternativas:** alcance común, configuración por capacidad, criterios/pesos/puntajes normalizados, descartes y sensibilidad. Explica soluciones mixtas por scope.
7. **Selección y arquetipo:** alternativa confirmada, mapa de scope, `ARQ-xxx`, baseline tecnológico y desviaciones.
8. **Incertidumbres y PoC:** hipótesis, umbrales, resultados, evidencia y riesgos aceptados.
9. **Arquitectura diseñada:** contexto C4, contenedores, componentes de cada contenedor significativo, gobierno/catálogo de APIs y contratos, secuencias críticas y dependencias. Resume `API-xxx`/operaciones críticas, exposición, owner, consumidores, seguridad y compatibilidad cuando sean materiales para la decisión; no copies especificaciones completas. Si aplica Microfrontends, muestra driver, alternativa SPA comparada, shell/composición, unidades/owners, compatibilidad, experiencia, rendimiento y despliegue/rollback sin saturar la vista ejecutiva.
10. **Datos:** ownership, modelo por contenedor significativo, clasificación, residencia, retención, integraciones y CQRS localizado cuando aplique.
11. **Cloud y despliegue:** proveedor/región, cuentas/suscripciones, red, identidad, servicios administrados, HA/DR, observabilidad, capacidades de entrega, IaC y costos; enlaza Vulcano si ya existe sin duplicar su estrategia.
12. **Tácticas, patrones y calidad interna:** trazabilidad `QA → TP → CT → DA → prueba`, patrones aplicados y controles `CC-xxx` relevantes.
13. **Seguridad arquitectónica:** cuando `19.1` aplique, muestra activos/datos críticos, trust boundaries, 3-5 amenazas materiales `THR-xxx`, requisitos `SEC-xxx`, riesgo residual y estado del handoff a Vulcano. No presenta scanners, stages o inventario DevSecOps salvo como evidencia enlazada.
14. **Decisiones:** ADR/`DA-xxx` principales, estado, trade-off y consecuencias.
15. **Validación y coherencia:** resultados de PoC/pruebas, ATAM por escenario, Well-Architected, cobertura de criterios de cierre, resumen `prometido → diseñado → evidencia`, elementos huérfanos/contradicciones y dictamen de `25`.
16. **Riesgos, deuda y condiciones:** severidad, impacto, mitigación, owner, fecha/condición y riesgo residual.
17. **Economía y roadmap:** costo/rango y supuestos, fases, dependencias, puntos de decisión, rollback y métricas de salida.
18. **Cierre:** decisión solicitada, condiciones propuestas y enlaces a fuentes.

Una sección no aplicable permanece visible como `No aplica — <motivo>`. Una sección aplicable sin evidencia permanece visible como `Missing evidence` y bloquea la aptitud cuando es material para la decisión.

## Mapeo de fuentes

| Contenido de presentación | Dueño canónico mínimo |
|---|---|
| Estado y decisión solicitada | `25`, autoridad de `01`, selección de `10` |
| Problema, alcance, interesados, objetivos | `02` |
| Restricciones y supuestos | `03`, `04` |
| Drivers/QAW/Well-Architected | `05`-`08` |
| Alternativas y sensibilidad | `09` |
| Selección y mapa de scope | `10` |
| Arquetipo y tecnologías | `10.1` |
| Tecnologías emergentes, incertidumbres y PoC | `11`-`13` |
| C4, gobierno de APIs y diseño detallado | `14`, `14.00` y todos los `14.xx` aplicables |
| Flujos críticos | `15` |
| Datos | `16`, todos los `16.xx` aplicables |
| Cloud, despliegue y costos | `17`, `17.1`-`17.5` aplicables |
| Tácticas, patrones y Clean Code | `18`, `19` |
| Amenazas y requisitos de seguridad | `19.1` cuando aplique; decisiones/riesgos en `20`, `21` |
| Decisiones, riesgos y deuda | `20`, `21` |
| Brechas y roadmap TO-BE | `23`, `24` |
| Cobertura, ATAM y hallazgos | `25` |

Cada elemento de `sources` usa ruta relativa al `project-root`. No enlaces archivos externos ni rutas absolutas personales.

## Diagramas y operación sin conexión

Cuando existan, enlaza `15.1-Flujos-Interactivos_<Proyecto>.html` con enlaces profundos
(`#modo=TO-BE&flujo=<id>&paso=<n>`) al paso que sustenta cada argumento, y los `.excalidraw`
explicativos exportados (PNG/SVG con escena embebida). La presentación resume y enlaza; los
diagramas siguen siendo dueños de su artefacto (`references/guia-diseno-diagramas.md` §11).

- El HTML no depende de CDN, fuentes remotas ni JavaScript externo.
- Exporta Mermaid/draw.io canónicos a SVG o PNG local sin convertir la exportación en nuevo dueño del diagrama.
- Cada diagrama indica tipo/nivel, alcance, versión/hash del dueño y leyenda suficiente.
- Incluye al menos: contexto o C4 L2, detalle L3 de contenedores significativos, despliegue cloud y uno o más flujos críticos cuando apliquen.
- No uses diagramas decorativos ni combines AS-IS y TO-BE sin una leyenda inequívoca.
- Las imágenes deben ser legibles en 16:9, tener texto alternativo y abrirse en tamaño completo.

## Conflictos y evidencia faltante

Antes de generar, contrasta al menos:

- proveedor, región, identidad y servicios cloud entre `10.1`, `14`, `17` y `20`;
- estilo/configuración y asignación de capacidades entre `09`, `10` y `14`;
- tecnologías/versiones entre `10.1`, diseño, despliegue e IaC;
- nombres/IDs `CT-xx`, `API-xxx`, `API-xxx-OP-xxx`, contratos y ownership entre `14`, `14.00`, `14.xx`, `15`-`17`;
- estado de decisiones/riesgos entre `20`, `21` y `25`;
- costos y supuestos entre `17.4`, `17.5` y el resumen ejecutivo.

Registra cada discrepancia en `conflicts` con fuentes, severidad, owner y disposición. Un conflicto material sin resolver impide `approvalEligible=true`. No elijas silenciosamente una de dos fuentes incompatibles.

## Criterios de cierre

`25.1` cumple solo cuando:

- [ ] El manifiesto satisface el esquema y contiene las tres vistas.
- [ ] La portada muestra versión, fecha, escenario, estado de revisión y decisión solicitada.
- [ ] El resumen ejecutivo explicita valor, costo/plazo o `Missing evidence`, riesgos y condiciones.
- [ ] La matriz de trabajo evidencia todos los artefactos aplicables y sus gates.
- [ ] La presentación resume la cobertura de compromisos, la trazabilidad inversa del diseño y las contradicciones de `25` sin recalcular ni ocultar hallazgos.
- [ ] Alternativas, selección, diseño, datos, cloud, tácticas, decisiones, validación y riesgos están resumidos y enlazados.
- [ ] Cada contenedor significativo aparece con su `14.xx` y, cuando aplica, `16.xx`.
- [ ] Cuando existen interfaces programáticas, resume `14.00` y enlaza las APIs/operaciones críticas y sus contratos sin duplicarlos.
- [ ] Cada afirmación material tiene fuente relativa y hash vigente.
- [ ] Los diagramas son locales, legibles, trazables y no contradicen sus dueños.
- [ ] Los faltantes y conflictos están visibles; ninguno material está oculto.
- [ ] Si `approvalEligible=false`, aparece el watermark de borrador en todas las vistas.
- [ ] El HTML funciona sin red y pasa `validate_architecture_presentation.py` sin errores.
- [ ] `25` registra los hashes del manifiesto/HTML y el resultado de validación.

Estado de cierre permitido: `Cumple`, `Cumple con observaciones` o `No cumple`. `Cumple con observaciones` no admite errores del validador ni observaciones que cambien la decisión solicitada.
