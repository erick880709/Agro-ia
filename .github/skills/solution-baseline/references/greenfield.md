# Greenfield

## Precondiciones

- Existe arquitectura aprobada o el usuario acepta explícitamente los pendientes identificados.
- El destino no contiene código de aplicación, o es una ruta nueva autorizada.
- Contratos compartidos y topología están definidos.
- Arquetipo, capabilities y versiones exactas están resueltos.

## Procedimiento

1. Crea el blueprint y el run manifest.
2. Resuelve primero el catálogo; no generes desde memoria si hay arquetipo compatible.
3. Ejecuta dry-run en un workspace temporal.
4. Valida el resultado completo antes de copiarlo al destino.
5. Aplica parámetros no sensibles y overlays declarados.
6. Produce un vertical slice mínimo de infraestructura de aplicación: bootstrap, configuración, error handling, logging, health y pruebas.
7. Incluye contratos o clientes generados desde fuentes aprobadas cuando corresponda.
8. Ejecuta gates del stack en el destino.
9. Escribe receipt y handoff a `builder`.

No implementes entidades o historias de negocio que no sean necesarias para demostrar la integración básica. No generes artefactos de Vulcano.

Para materializar el componente lee, según corresponda:

- [Bootstrap greenfield por stack](./greenfield-stack-bootstrap.md).
- [Convenciones greenfield](./greenfield-conventions.md).
- [Plomería base de aplicación](./application-plumbing.md).

## Topología

No asumas monorepo o polyrepo. Usa la decisión arquitectónica y el ownership/ciclo de cambio. Si falta y cambia materialmente el resultado, solicítala antes de aplicar; puedes continuar con discovery y plan.

## Genesis

Cuando una solicitud llegue como Genesis, usa este mismo modo y contratos. No mantengas receipts o estructuras alternativas. Registra `invocation_alias: genesis` si se necesita trazabilidad de adopción. El skill Genesis es solo un alias deprecated y no ejecuta un generador propio.
