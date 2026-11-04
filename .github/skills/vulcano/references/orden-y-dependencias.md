# Orden recomendado de generación y dependencias

## Índice

- [Orden sugerido](#orden-sugerido-numerado)
- [Justificación](#por-qué-este-orden-y-no-otro)
- [Progresión por madurez](#progresión-por-madurez)
- [Estados mixtos](#manejo-de-estados-mixtos)

Este orden minimiza cuánto hay que re-preguntar: cada archivo se genera después de los que le
sirven de insumo. No es obligatorio seguirlo al pie de la letra — el arquitecto puede elegir
cualquier archivo en cualquier momento (Fase 1 del `SKILL.md`) — pero si no expresa preferencia,
usa este orden por defecto.

Cada carpeta tiene una numeración propia y estable: `devops-strategy/` usa `01-` a `11-`,
`infrastructure-as-code/` usa `01-` a `08-`, `observability/` usa `01-` a `07-`, y la raíz de
`resources_root` usa `01-` y `02-` para los artefactos de cierre. El prefijo no cambia si el
arquitecto decide generar los archivos en otra secuencia; representa el orden relativo dentro
de su carpeta.

## Orden sugerido (numerado)

**Nota sobre dependencias "de baseline" vs. "de archivo generado por vulcano":** varias entradas
de abajo distinguen explícitamente si dependen de algo que **ya se conocía antes de empezar**
(`resources/architecture/`, producido por `archi`/`janus` en la Fase 0.1) o de un archivo que
**esta misma skill genera** durante la sesión. Solo el segundo tipo obliga a un orden — lo
primero está disponible desde el archivo 1, sin importar la posición.

```
1.  devops-strategy/01-devops-overview.md            [sin dependencias de archivos de vulcano — solo filosofía/roles/criterios, no nombra herramientas finales]
2.  devops-strategy/02-repository-management.md      [sin dependencias]
3.  devops-strategy/03-task-management.md            [sin dependencias]
4.  devops-strategy/04-branching-strategy.md         [depende de: 03-task-management.md (convención de nombre de rama suele incluir el ID del ítem)]
5.  devops-strategy/05-environments.md               [depende solo del baseline; NO depende de infrastructure-as-code/01-architecture.md]
6.  infrastructure-as-code/01-architecture.md        [depende solo del baseline — decide la herramienta de IaC]
7.  infrastructure-as-code/02-environments.md        [depende de: devops-strategy/05-environments.md e infrastructure-as-code/01-architecture.md]
8.  infrastructure-as-code/03-naming-conventions.md  [depende de: devops-strategy/05-environments.md]
9.  infrastructure-as-code/04-terraform-structure.md [depende de: infrastructure-as-code/01-architecture.md, 03-naming-conventions.md]
10. infrastructure-as-code/05-state-management.md    [depende de: 04-terraform-structure.md, infrastructure-as-code/02-environments.md]
11. infrastructure-as-code/06-modules.md             [depende de: 04-terraform-structure.md]
12. infrastructure-as-code/07-networking.md          [depende de: infrastructure-as-code/02-environments.md, baseline]
13. infrastructure-as-code/08-secrets-management.md  [depende de: infrastructure-as-code/02-environments.md]
14. devops-strategy/06-ci-cd.md                      [depende de: 04-branching-strategy.md, devops-strategy/05-environments.md]
15. devops-strategy/07-continuous-testing.md         [depende de: 06-ci-cd.md y resources/qa/ si existe; al terminar reconcilia gates y enlaces de 06-ci-cd.md]
16. devops-strategy/08-security.md                   [depende de: 06-ci-cd.md, infrastructure-as-code/08-secrets-management.md y requisitos Archi `SEC-xxx`/fuentes de seguridad si existen]
17. devops-strategy/09-release-management.md         [depende de: 06-ci-cd.md, devops-strategy/05-environments.md]
18. devops-strategy/10-incident-management.md        [depende de: devops-strategy/05-environments.md]
19. devops-strategy/11-disaster-recovery.md          [depende de: baseline, devops-strategy/05-environments.md]
20. observability/01-monitoring.md                   [depende de: baseline, 06-ci-cd.md y 09-release-management.md]
21. observability/02-logging.md                      [depende de: baseline, puede generarse junto con 01-monitoring.md]
22. observability/03-tracing.md                      [condicional según arquitectura distribuida]
23. observability/04-slis-slos.md                    [depende de: 01-monitoring.md y baseline]
24. observability/05-dashboards.md                   [depende de: 01-monitoring.md, 04-slis-slos.md]
25. observability/06-alerting.md                     [depende de: 04-slis-slos.md, 01-monitoring.md]
26. observability/07-runbooks.md                     [depende de: 06-alerting.md; enlaza con 10-incident-management.md]
```

## Por qué este orden y no otro

- **`01-devops-overview.md` va primero, no segundo.** Es el único archivo que no necesita que se
  haya decidido ninguna herramienta todavía — cubre filosofía, roles y el *criterio* de
  selección, no el nombre final de cada herramienta (eso se repetiría después en
  `01-architecture.md`/`06-ci-cd.md`/`01-monitoring.md`, generando inconsistencias si cambia algo en el
  camino). Por eso su plantilla no tiene una tabla de "herramientas centrales" a rellenar de
  entrada.
- **`04-branching-strategy.md` va justo después de `03-task-management.md`**, sin esperar a
  ambientes ni IaC — su única dependencia real es la convención de ID del tablero, no el
  proveedor de nube.
- **`devops-strategy/05-environments.md` no depende de `infrastructure-as-code/01-architecture.md`.**
  El proveedor de nube ya se conoce desde la Fase 0.1 (viene de `resources/architecture/`,
  generado por `archi`/`janus` antes de que `vulcano` empiece) — no hace falta esperar a que
  `vulcano` decida la *herramienta* de IaC para poder nombrar los ambientes y su propósito de
  negocio. Por eso puede ir en la posición 5, antes de `infrastructure-as-code/01-architecture.md`.
- **IaC antes que CI/CD**: el pipeline de CI/CD normalmente despliega la infraestructura que
  ya está definida (o al menos decidida en `infrastructure-as-code/01-architecture.md`); preguntar
  sobre el pipeline sin saber qué herramienta de IaC se usa lleva a respuestas contradictorias.
- **`08-security.md` operacionaliza, no redefine, la seguridad de Archi**: antes de generarlo
  consume `19.1`/`SEC-xxx`, `14.00`, `14.xx`, `17`, `20` y `21` aplicables siguiendo
  `contrato-handoff-archi.md`; después decide herramientas, stages, evidencia y gobierno.
- **`environments.md` se genera dos veces a propósito** (`05-` en DevOps y `02-` en IaC) pero la segunda vez no
  se vuelve a preguntar nada — solo se traduce la misma decisión (nombres, propósito, orden de
  promoción) al lenguaje de infraestructura (workspaces, carpetas, variables por ambiente).
- **Dentro de `infrastructure-as-code/`, `03-naming-conventions.md` va antes que
  `04-terraform-structure.md`, `05-state-management.md` y `06-modules.md`** — estos tres reutilizan la
  convención de nombres en sus ejemplos, así que generarlos antes obligaría a corregirlos
  después.
- **Observabilidad va al final** porque sus tres archivos más importantes (`04-slis-slos.md`,
  `06-alerting.md`, `07-runbooks.md`) dependen de que ya exista una lista real de servicios
  desplegados y ambientes — que se resuelve en los pasos de IaC.
- **Dentro de `observability/`, `04-slis-slos.md` va antes que `05-dashboards.md` y `06-alerting.md`** —
  ambos muestran/disparan sobre SLOs ya definidos; generarlos antes dejaría paneles y alertas
  sin un SLO real del cual derivarse.
- **`03-tracing.md` es condicional**: si el sistema documentado en `resources/architecture/` es un
  monolito sin comunicación distribuida relevante, pregúntale al arquitecto si quiere
  igualmente el archivo (puede ser útil a futuro) o si prefiere omitirlo — no lo generes con
  contenido de relleno si no aporta valor real todavía.

## Progresión por madurez

Referenciado desde la Fase 0.4 del `SKILL.md`. El nivel de madurez DevOps que declare el
arquitecto (Básico / Intermedio / Avanzado) no cambia el orden de generación, pero sí **cuánto**
proponer dentro de cada archivo — proponer de entrada el techo de sofisticación a un equipo que
recién está saliendo de procesos manuales genera un documento que nadie va a implementar.

| Archivo | Equipo Básico | Equipo Intermedio | Equipo Avanzado |
|---|---|---|---|
| `06-ci-cd.md` | Un solo pipeline, sin ambientes paralelos, aprobación manual a todo | Pipeline con ambientes, algunos gates automáticos | Pipeline completo con gates automáticos, promoción sin intervención manual salvo prod |
| `06-ci-cd.md` (inspección/deuda) | Lint y baseline visible; hallazgos informativos | Gates sobre código nuevo + backlog de deuda con owner | Ratchet, métricas completas, excepciones con vencimiento y mejora basada en tendencia |
| `devops-strategy/08-security.md` | SCA y secret scanning sobre el flujo crítico | SAST + SCA con gates por riesgo; DAST informativo | Controles completos de supply chain y seguridad, bloqueantes solo cuando la señal es confiable y el riesgo lo exige |
| `07-continuous-testing.md` | Empezar por pruebas unitarias en el flujo crítico, sin exigir % de cobertura todavía | Cobertura mínima por capa, E2E en flujos críticos | Pirámide completa con targets por capa y pruebas de carga/seguridad integradas al pipeline |
| `observability/01-monitoring.md` (DORA) | Instrumentar una baseline de las cinco métricas; si no hay datos, declararlo | Metas a 6 meses con fuente y calidad de dato | Metas a 6/12 meses, análisis de tendencias y mejora basada en evidencia |
| `11-disaster-recovery.md` | Tabletop y restore test mínimo proporcional al riesgo | Simulacro anual y restores periódicos | Simulacros periódicos con RTO/RPO medidos y acciones rastreadas |

Para un equipo Básico, el archivo que más vale la pena reforzar primero no es el más avanzado
técnicamente — es `01-devops-overview.md` y `06-ci-cd.md` con lo mínimo operable. Para un equipo
Avanzado, evita explicaciones de qué es cada práctica y ve directo a las decisiones específicas
del proyecto.

## Manejo de estados mixtos

Es normal que un proyecto tenga, por ejemplo, IaC ya implementada en código pero cero
observabilidad. En ese caso:

1. Los archivos cuyo pilar está en estado **"Implementado sin documentar"** (ver `SKILL.md`
   Fase 0.2) se generan primero como borrador AS-IS a partir del código real, y se confirman
   con el arquitecto — no se preguntan de cero.
2. Los archivos cuyo pilar está en estado **"Sin evidencia"** siguen el flujo normal de
   preguntas de `preguntas-por-archivo.md`.
3. El orden numerado de arriba sigue aplicando dentro de cada pilar, pero el arquitecto puede
   priorizar el pilar con menos madurez si lo prefiere (p. ej. "documentemos primero
   observabilidad porque es lo que no tenemos nada armado").
