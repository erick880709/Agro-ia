# Guía de Performance Testing (k6)

Playbook para diseñar y ejecutar pruebas de carga/estrés/spike sobre la API
o los flujos críticos de la aplicación, e interpretar resultados sin
inventar umbrales arbitrarios.

---

## Índice

- [Herramienta y Prerrequisito](#herramienta-y-prerrequisito)
- [Tipos de Prueba de Performance](#tipos-de-prueba-de-performance)
- [Definir Objetivos Antes de Escribir el Script](#definir-objetivos-antes-de-escribir-el-script)
- [Script Base de k6](#script-base-de-k6)
- [Ejecución y Umbrales como Quality Gate](#ejecución-y-umbrales-como-quality-gate)
- [Interpretar Resultados](#interpretar-resultados)
- [Convención de Id de Caso y Evidencia](#convención-de-id-de-caso-y-evidencia)

---

## Herramienta y Prerrequisito

Este playbook usa **k6**, que es un binario independiente (no un paquete
npm del proyecto) — no lo instala `scripts/ensure-qa-dependencies.mjs`.
Verificar/instalar antes de usar este playbook:

```bash
# macOS
brew install k6
# Linux (Debian/Ubuntu)
sudo gpg -k && sudo gpg --no-default-keyring --keyring /usr/share/keyrings/k6-archive-keyring.gpg --keyserver hkp://keyserver.ubuntu.com:80 --recv-keys C5AD17C747E3415A3642D57D77C6C491D6AC1D69
echo "deb [signed-by=/usr/share/keyrings/k6-archive-keyring.gpg] https://dl.k6.io/deb stable main" | sudo tee /etc/apt/sources.list.d/k6.list
sudo apt-get update && sudo apt-get install k6
# CI: usar la imagen oficial grafana/k6 en vez de instalar en cada corrida
```

Si `k6` no está disponible y no se puede instalar (permisos, red
corporativa), no simular resultados de performance — avisar al usuario que
este playbook requiere el binario y detenerse, igual que con cualquier otra
dependencia externa que este skill no puede resolver por sí solo.

## Tipos de Prueba de Performance

| Tipo | Objetivo | Cuándo usarlo |
|---|---|---|
| **Smoke** | Confirmar que el script funciona con carga mínima (1-2 VUs) | Siempre, antes de cualquier otro tipo |
| **Load** | Comportamiento bajo la carga esperada normal | Antes de un release con cambios en flujos de alto tráfico |
| **Stress** | Encontrar el punto de quiebre subiendo la carga progresivamente | Antes de una campaña/evento con pico esperado |
| **Spike** | Comportamiento ante un salto abrupto de tráfico | Flujos expuestos a picos impredecibles (promociones, notificaciones push) |
| **Soak (endurance)** | Detectar degradación/memory leaks en ejecución sostenida | Servicios de larga vida, antes de un release mayor |

## Definir Objetivos Antes de Escribir el Script

No correr una prueba de carga sin haber acordado explícitamente (con el
equipo de backend/negocio) al menos:

- Carga objetivo (usuarios concurrentes o requests/segundo esperados en
  producción, con margen).
- Umbral de latencia aceptable (p95/p99, no solo el promedio).
- Tasa de error aceptable bajo carga (ej. `< 1%`).
- Entorno objetivo — **nunca correr una prueba de carga significativa
  contra producción sin autorización explícita y coordinación previa**, y
  nunca contra un entorno compartido con otros equipos sin avisar.

Documentar esto en el plan de pruebas (`../../qa-ranger-plan-pruebas/templates/test_plan_template.md`, sección
de estrategia de ejecución) antes de generar el script.

## Script Base de k6

```javascript
// resources/qa/perf/login-load.js
import http from 'k6/http';
import { check, sleep } from 'k6';

export const options = {
  scenarios: {
    load: {
      executor: 'ramping-vus',
      startVUs: 0,
      stages: [
        { duration: '30s', target: 20 },  // ramp-up
        { duration: '2m', target: 20 },   // carga sostenida
        { duration: '30s', target: 0 },   // ramp-down
      ],
    },
  },
  thresholds: {
    http_req_duration: ['p(95)<800'],   // p95 bajo 800ms
    http_req_failed: ['rate<0.01'],     // menos de 1% de errores
  },
};

export default function () {
  const res = http.post(`${__ENV.QA_BASE_URL}/api/auth/login`, JSON.stringify({
    email: __ENV.QA_USER_EMAIL,
    password: __ENV.QA_USER_PASSWORD,
  }), { headers: { 'Content-Type': 'application/json' } });

  check(res, {
    'status es 200': (r) => r.status === 200,
    'responde en menos de 1s': (r) => r.timings.duration < 1000,
  });

  sleep(1);
}
```

## Ejecución y Umbrales como Quality Gate

```bash
k6 run --out json=resources/qa/perf/<runId>/results.json resources/qa/perf/login-load.js
```

Los `thresholds` del script actúan como quality gate: k6 termina con
código de salida distinto de cero si algún threshold falla, lo que permite
bloquear el pipeline igual que `--fail-on-no-go` en
`generate-execution-report.mjs` (ver `./markdown_test_runbook.md`). Guardar
el `results.json` bajo `resources/qa/perf/<runId>/` siguiendo la misma
convención de `runId` que el resto del skill.

## Interpretar Resultados

- **No reportar solo el promedio de latencia** — usar p95/p99, que reflejan
  la experiencia de la cola de usuarios peor servidos, no la mayoría.
- Una tasa de error que sube con la carga suele indicar saturación de un
  recurso específico (conexiones de base de datos, pool de threads) — no
  reportar solo "falló", correlacionar con métricas de infraestructura del
  entorno si están disponibles.
- Un resultado "PASS" contra los thresholds definidos no es una garantía
  de capacidad en producción si el entorno de prueba tiene recursos
  distintos (menos réplicas, base de datos más chica) — documentar esa
  diferencia explícitamente en el reporte.
- Comparar siempre contra una corrida base (baseline) previa cuando se
  evalúa si un cambio de código introdujo una regresión de performance, no
  solo contra el umbral absoluto.

## Convención de Id de Caso y Evidencia

Usar el prefijo `PERF-` para el caso en el runbook/plan (ej. `PERF-01
[high] - Login soporta 20 usuarios concurrentes con p95 < 800ms`). La
evidencia de este playbook no son video/trace de Playwright sino el
`results.json` de k6 y, si se generó, el reporte HTML
(`k6 run --out json=... --summary-export=resources/qa/perf/<runId>/summary.json`)
— igual guardado bajo `resources/qa/` para mantener todos los entregables
en un solo lugar (ver `../SKILL.md#estructura-de-entregables-carpeta-de-salida`).
