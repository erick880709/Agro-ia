# Adaptadores por stack

El registro canónico vive en `../adapters/registry.json`. Un adaptador detecta el stack, propone un motor nativo, define comandos de validación y traduce el protocolo común. No es un agente autónomo.

Para patrones de bootstrap parametrizados lee [greenfield-stack-bootstrap.md](./greenfield-stack-bootstrap.md). No copies comandos históricos que usen `latest`; resuelve primero una versión exacta.

## Selección

1. Detecta primero herramientas ya usadas por el repositorio.
2. Respeta decisiones de arquitectura y lockfiles.
3. Prefiere generadores con schema, dry-run/árbol virtual y migraciones.
4. Fija versión exacta antes de ejecutar.
5. Si no existe adaptador, continúa con discovery/plan y registra `adapter: pending`; no inventes comandos destructivos.

## Baseline mínima por workload

### Web

App shell, rutas y lazy loading aplicables, cliente tipado desde contrato, estado remoto, auth boundary, sistema de diseño derivado de tokens congelados (capability `design-system`), errores, pruebas/mocks, accesibilidad básica y vertical slice. Usa la versión de runtime y el gestor de paquetes exactos definidos por la arquitectura/lockfile del proyecto. Los adaptadores web declaran como validaciones opcionales `design-conformance` (`npm run lint:design`) y `a11y` (`npm run test:a11y`) cuando el proyecto expone esos scripts; `check-design-conformance` del skill aplica siempre que el componente declare `design_system`.

### API

Bootstrap, límites de dominio/aplicación/adaptadores según patrón, modelos contract-first, validación, errores, correlación, seguridad, persistencia diseñada, health/telemetría y pruebas unitarias/integración/contrato.

### Worker

Dispatcher, mensajes versionados, idempotencia, retry/dead-letter a nivel de aplicación, apagado seguro, actualización de estado y pruebas.

### Agent service

Frontera de proveedor, tools tipadas, confirmación humana para acciones sensibles, límites/timeouts/retry, memoria según ownership y evaluaciones mínimas.

### Integrations

ACL por sistema, modelos externos confinados, idempotencia, retry/deduplicación/reconciliación, contratos internos y stubs.

## Validaciones

Usa comandos declarados por el repositorio o adaptador. Ejecuta al menos manifest/schema validation, install/restore cuando sea seguro, lint/format check, build/typecheck, unit tests y smoke test pertinente. No declares éxito solo porque se crearon archivos.

## Extensión del registro

Un nuevo adaptador requiere descriptor validable, detectores no ejecutables, comandos con efectos declarados, pruebas contractuales y owner. Mantén las reglas del stack en el adaptador, no en `SKILL.md` ni en el orquestador.
