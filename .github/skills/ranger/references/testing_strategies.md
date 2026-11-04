# Estrategia QA: niveles, alcance y cierre

Guía común para elegir niveles de prueba, priorizar riesgos y definir criterios de salida. La configuración de runners y sus ejemplos viven en cada especialista.

## Índice

- [La Pirámide de Testing](#la-pirámide-de-testing)
- [Tipos de pruebas y responsables](#tipos-de-pruebas-y-responsables)
- [Objetivos y Umbrales de Cobertura](#objetivos-y-umbrales-de-cobertura)
- [Patrones de Organización de Tests](#patrones-de-organización-de-tests)
- [Estrategias de Integración con CI/CD](#estrategias-de-integración-con-cicd)
- [Marco de Decisión para Testing](#marco-de-decisión-para-testing)

## La Pirámide de Testing

La pirámide orienta cómo distribuir el esfuerzo entre niveles. Los porcentajes siguientes ilustran una distribución; no son metas de cobertura ni criterios de aceptación del encargo.

### Estructura Clásica de la Pirámide

```
        /\
       /  \      Pruebas E2E (5-10%)
      /----\     - Validación de recorridos de usuario
     /      \    - Cobertura de rutas críticas
    /--------\   Pruebas de Integración (20-30%)
   /          \  - Interacciones entre componentes
  /            \ - Integración de API
 /--------------\ Pruebas Unitarias (60-70%)
/                \ - Funciones individuales
------------------  - Componentes aislados
```

### Pirámide Adaptada a React/Next.js

Para aplicaciones frontend, la pirámide se ajusta levemente:

| Nivel | Porcentaje | Herramientas | Enfoque |
|-------|------------|-------|-------|
| Unitario | 50-60% | Jest o Vitest, RTL | Funciones puras, hooks, componentes aislados |
| Integración | 25-35% | RTL, MSW | Árboles de componentes, llamadas a API, contexto |
| E2E | 10-15% | Playwright | Flujos críticos de usuario, navegación entre páginas |

Conserva el runner instalado. El especialista unitario mantiene los ejemplos y comandos de Jest/Vitest.

### ¿Por Qué Esta Distribución?

**Las pruebas unitarias son rápidas y económicas:**
- Se ejecutan en milisegundos
- Permiten identificar fallas con precisión
- Son fáciles de mantener
- Se ejecutan en cada commit

**Las pruebas de integración equilibran cobertura y costo:**
- Prueban escenarios realistas
- Detectan errores de interacción entre componentes
- Tiempo de ejecución moderado
- Se ejecutan en cada PR

**Las pruebas E2E son costosas pero esenciales:**
- Validan la experiencia real del usuario
- Detectan problemas de despliegue
- Son lentas y frágiles (flaky)
- Se ejecutan en staging/producción

---

## Tipos de pruebas y responsables

| Nivel | Alcance | Implementación |
|---|---|---|
| Unitario | Lógica aislada y componentes en memoria | [Unitarias](../../qa-ranger-unitarias/SKILL.md) |
| Integración | Interacción entre componentes, API o servicios | El especialista del stack elegido; distingue dobles en memoria de servicios reales |
| E2E | Flujos de usuario en navegador | [Playwright](../../qa-ranger-playwright/SKILL.md), [Selenium](../../qa-ranger-selenium/SKILL.md) o [Robot Framework](../../qa-ranger-robotframework/SKILL.md), según el proyecto |
| Visual y accesibilidad | Cambios de UI, teclado y tecnologías de apoyo | [Playwright](../../qa-ranger-playwright/references/07-visual-y-accesibilidad.md) y [criterios comunes](accessibility_testing_guide.md) |
| API | Contratos y comportamiento de endpoints | [Karate](../../qa-ranger-karate/SKILL.md), [Robot Framework](../../qa-ranger-robotframework/resources/06-api-requests.md) o herramienta instalada |
| Aceptación de base de datos | Esquema, integridad y datos de referencia tras el despliegue | [Robot Framework](../../qa-ranger-robotframework/resources/07-base-de-datos.md) |
| Carga | SLA y comportamiento bajo carga | [JMeter](../../qa-ranger-jmeter/SKILL.md) o [k6](performance_testing_guide.md) |

## Objetivos y Umbrales de Cobertura

La [política QA](../../../contracts/output/validators/qa/qa-policy.json) establece 95% de cobertura unitaria por métrica soportada. Una meta diferente requiere instrucción explícita y `targetOverride`. Define el alcance de archivos y exclusiones por requisito, conserva el reporte nativo y distingue cobertura de código de cobertura de requisitos. Prioriza rutas críticas sin reducir la meta predeterminada de las demás.

La configuración de Jest y los ejemplos React se encuentran en [ejemplos y organización unitarios](../../qa-ranger-unitarias/references/06-ejemplos-y-organizacion.md). Para flujos E2E y visuales consulta [ejemplos Playwright](../../qa-ranger-playwright/references/16-ejemplos-y-ci.md).

## Patrones de Organización de Tests

Conserva las convenciones del repositorio: pruebas cerca del módulo o carpetas separadas según el stack. Cada caso mantiene un ID y prioridad estables; separa código versionado de reportes y evidencia por ejecución. La estructura concreta de fixtures, POM y configuración corresponde al especialista.

## Estrategias de Integración con CI/CD

Define qué suites se ejecutan por commit, PR y release según riesgos y criterios de salida del encargo. Ejecuta primero las verificaciones rápidas y luego los flujos críticos; conserva los artefactos incluso si falla una etapa. No conviertas una suite completa fallida en una alerta por defecto.

El reporte compartido consume CTRF y el alcance previsto. Usa `--fail-on-no-go` cuando el gate acordado bloquee NO-GO. Consulta la [guía de evidencia](evidence_guide.md) y configura el pipeline en el especialista: [Playwright](../../qa-ranger-playwright/references/09-ci-cd-y-reportes.md), [Selenium](../../qa-ranger-selenium/resources/08-ci-cd-y-reportes.md) o el runner del proyecto.

## Marco de Decisión para Testing

### Cuándo Escribir Cada Tipo de Prueba

```
¿Es una función pura sin efectos secundarios?
├── Sí → Prueba unitaria
└── No
    ├── ¿Realiza llamadas a API o usa contexto?
    │   ├── Sí → Prueba de integración con mocking
    │   └── No
    │       ├── ¿Es un flujo crítico de usuario?
    │       │   ├── Sí → Prueba E2E
    │       │   └── No → Prueba de integración
    └── ¿Está enfocado en la UI con muchos estados visuales?
        ├── Sí → Storybook + Prueba visual
        └── No → Prueba unitaria de componente
```

### Matriz de ROI de Testing

| Tipo de Prueba | Tiempo de Escritura | Tiempo de Ejecución | Mantenimiento | Confianza |
|-----------|------------|----------|-------------|------------|
| Unitaria | Bajo | Muy rápido | Bajo | Media |
| Integración | Medio | Rápido | Medio | Alta |
| E2E | Alto | Lento | Alto | Muy alta |
| Visual | Bajo | Medio | Medio | Alta (UI) |

### Cuándo NO Testear

- Código generado (tipos de GraphQL, cliente de Prisma)
- Elementos internos de librerías de terceros
- Detalles de implementación (estado interno, métodos privados)
- Wrappers simples de paso directo (pass-through)
- Definiciones de tipos

### Señales de Alerta en la Estrategia de Testing

| Señal de Alerta | Problema | Solución |
|----------|---------|----------|
| Pruebas E2E > 30% | CI lento, tests flaky | Trasladar lógica hacia pruebas de integración |
| Solo pruebas unitarias | Faltan errores de interacción | Agregar pruebas de integración |
| Testear mocks | No se prueba el comportamiento real | Probar comportamiento, no implementación |
| Meta de cobertura del 100% | Rendimientos decrecientes | Enfocarse en las rutas críticas |
| Sin pruebas E2E | Faltan problemas de despliegue | Agregar smoke tests para flujos críticos |

---
