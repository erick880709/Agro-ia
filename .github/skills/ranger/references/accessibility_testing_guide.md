# Guía de Accessibility Testing (WCAG)

Criterios comunes para planear pruebas de accesibilidad automatizadas y manuales, priorizar hallazgos y conservar evidencia. Cada especialista mantiene la instalación y los ejemplos de su herramienta.

---

## Índice

- [Qué Cubre y Qué No Cubre el Testing Automatizado](#qué-cubre-y-qué-no-cubre-el-testing-automatizado)
- [Nivel de Conformidad Objetivo](#nivel-de-conformidad-objetivo)
- [Automatizado: axe en Playwright](#automatizado-axe-en-playwright)
- [Automatizado: axe en Componentes (jest-axe)](#automatizado-axe-en-componentes-jest-axe)
- [Manual: Navegación por Teclado](#manual-navegación-por-teclado)
- [Manual: Checklist con Lector de Pantalla](#manual-checklist-con-lector-de-pantalla)
- [Priorización de Hallazgos](#priorización-de-hallazgos)
- [Convención de Id de Caso](#convención-de-id-de-caso)

---

## Qué Cubre y Qué No Cubre el Testing Automatizado

**Importante para no generar falsa confianza:** las herramientas
automatizadas (axe) detectan de forma confiable aproximadamente el
**30-40%** de los problemas de accesibilidad reales — los que son
mecánicamente verificables (contraste, atributos ARIA faltantes/inválidos,
labels ausentes, orden de headings). No detectan:

- Si el orden de foco tiene sentido para un usuario real.
- Si un mensaje de error es comprensible leído por un lector de pantalla.
- Si un flujo completo (no un componente aislado) es operable solo con
  teclado de principio a fin.

Por eso este playbook combina automatizado (para regresiones, en cada PR)
con manual dirigido (para flujos críticos, antes de un release).

## Nivel de Conformidad Objetivo

Por defecto, `WCAG 2.1 nivel AA` salvo que el proyecto documente otro
nivel explícitamente (algunos contextos regulados, como banca, pueden
requerir AA o superior con criterios adicionales — confirmar con el
usuario en vez de asumir).

## Automatizado: axe en Playwright

Consulta la [implementación Playwright](../../qa-ranger-playwright/references/18-accesibilidad-axe.md). Ejecuta los casos en los flujos críticos del plan, no solo en una página dedicada.

## Automatizado: axe en Componentes (jest-axe)

Consulta la [implementación unitaria](../../qa-ranger-unitarias/references/07-accesibilidad-componentes.md). Un componente accesible en aislamiento no acredita la accesibilidad de la página completa.

## Manual: Navegación por Teclado

Checklist a ejecutar sobre cada flujo crítico (documentar como caso
`A11Y-xxx` con pasos manuales, igual que cualquier caso del runbook):

- [ ] Todo el flujo es completable usando solo `Tab`/`Shift+Tab`/`Enter`/`Espacio`/flechas, sin mouse.
- [ ] El orden de foco sigue el orden visual/lógico de la página.
- [ ] El foco es siempre visible (outline no removido con `outline: none` sin reemplazo).
- [ ] Modales/dropdowns atrapan el foco mientras están abiertos y lo devuelven al cerrarse.
- [ ] No hay "trampas de teclado" (un elemento del que no se puede salir con Tab).
- [ ] Elementos interactivos custom (divs con `onClick`) responden también a teclado o son `button`/`a` reales.

## Manual: Checklist con Lector de Pantalla

Con VoiceOver (macOS), NVDA (Windows) o similar, sobre el flujo crítico:

- [ ] Cada input tiene un label anunciado (no solo un placeholder).
- [ ] Los mensajes de error se anuncian automáticamente (`aria-live` o foco movido al error).
- [ ] Las imágenes informativas tienen `alt` descriptivo; las decorativas, `alt=""`.
- [ ] Los estados dinámicos (carga, éxito, error) se anuncian, no solo se muestran visualmente.
- [ ] La jerarquía de headings (`h1`→`h2`→`h3`) es lógica, sin saltos.

## Priorización de Hallazgos

| Severidad | Criterio |
|---|---|
| Critical | Bloquea completamente el flujo para un usuario de tecnología asistiva (no puede completar login, checkout, etc.) |
| Serious | Dificulta severamente pero no bloquea (contraste insuficiente en texto principal, foco perdido tras una acción) |
| Moderate | Afecta la experiencia sin bloquear (labels imprecisos, heading fuera de orden) |
| Minor | Cosmético, sin impacto funcional real |

Un hallazgo `Critical` en un flujo etiquetado `[critical]` en el plan de
pruebas fuerza `NO-GO` igual que cualquier otro defecto crítico.

## Convención de Id de Caso

Usar el prefijo `A11Y-` (ej. `A11Y-01 [high]`), reconocido al leer el CTRF
(`../../../contracts/output/validators/qa/ctrf.mjs`). Los casos automatizados conservan la evidencia del nivel browser o unit según la [política común](evidence_guide.md); los casos
manuales de teclado/lector de pantalla se documentan en el runbook con su
resultado y, cuando sea posible, una grabación de pantalla de la sesión
manual guardada en la misma carpeta `resources/qa/test-results/<runId>/A11Y-xxx/`.
