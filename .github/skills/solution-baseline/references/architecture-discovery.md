# Descubrimiento arquitectónico

## Orden de evidencia

1. Contratos ejecutables aprobados: OpenAPI, AsyncAPI, schemas y modelos versionados.
2. ADR, arquitectura de solución, diseño detallado y restricciones explícitas.
3. Arquitectura UX y sistema de diseño aprobados del proyecto (especificaciones de pantalla, catálogo de componentes, tokens `*.tokens.json`, manifiesto de assets de marca), para componentes `web` y `library`.
4. Código, manifiestos, pruebas y comportamiento ejecutable del repositorio.
5. Roadmaps y documentos históricos.
6. Convenciones idiomáticas del stack, solo para vacíos reversibles.

Una fuente más reciente no sustituye automáticamente una más autoritativa. Reporta contradicciones con ruta, sección y efecto. Conserva funcionalidad existente mientras la decisión no ordene retirarla.

## Modelo normalizado por componente

Extrae:

- `id`, nombre, workload (`web`, `api`, `worker`, `agent`, `integrations`, `library`).
- Repositorio lógico, topología, lifecycle y ownership de equipo.
- Lenguaje, runtime, framework, gestor y restricciones de versión.
- Estilo arquitectónico, módulos, puertos, adaptadores y límites de dominio.
- APIs, eventos, schemas, productores, consumidores y estrategia de versionado.
- Persistencia, cache, colas e integraciones desde la perspectiva de aplicación.
- Autenticación, autorización, privacidad y controles `SEC-xxx`.
- Logging, métricas, trazas, health/readiness y resiliencia de aplicación.
- Pruebas, calidad, performance y accesibilidad pertinentes.
- Sistema de diseño (componentes `web`/`library`): fuente, tokens, catálogo de componentes, assets de marca, estado de evidencia y zonas donde se permiten literales de estilo.
- Dependencias entre componentes y barreras necesarias para paralelizar.
- Exclusiones, supuestos y decisiones pendientes.

Para cada valor registra `value`, `status: confirmed|inferred|pending` y `sources`. No persistas secretos.

## Decisión greenfield/brownfield

Un repositorio es brownfield si contiene código de aplicación, manifiestos, módulos, pruebas o una baseline previa, aunque el documento lo describa como futuro. README, licencia o carpeta `resources` sin aplicación no bastan para declararlo brownfield.

El modo se decide por repositorio o componente. Una solución puede ser híbrida.

## Criterio para preguntar

Pregunta solo cuando el vacío sea costoso de revertir o cambie topología, límites, contrato, identidad, seguridad, ownership, estilo o stack. Para decisiones reversibles, usa el default idiomático del adaptador y regístralo como `inferred`. Para decisiones materiales que pertenecen a arquitectura, emite un `architecture-gap` conforme a [architecture-handoff.md](./architecture-handoff.md). La selección o creación de un arquetipo no se devuelve a `archi` si el estado deseado ya está claro.
