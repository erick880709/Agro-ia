# Convenciones greenfield

Aplica estas convenciones únicamente cuando arquitectura, contratos, estándares del equipo, arquetipo y adaptador no hayan decidido el punto. Registra cada default como `inferred`, su fuente y cómo cambiarlo. Una instrucción explícita tiene prioridad.

## Decisiones que no deben inferirse silenciosamente

- Monorepo frente a polyrepo cuando haya varios ciclos de vida/equipos.
- Proveedor y flujo de identidad/autenticación.
- Identidad pública del paquete/módulo y estrategia de IDs persistentes.
- Gestor de paquetes si cambia lockfiles, tooling o soporte corporativo.
- Persistencia, broker o semántica de entrega.
- Contratos públicos, compatibilidad y estrategia de versionado.

Estas decisiones pueden dejar componentes bloqueados para apply, sin impedir discovery y plan.

## Naming idiomático

| Ecosistema | Archivos | Tipos | Funciones/métodos |
|---|---|---|---|
| Java/Kotlin | Convención del build/framework; tipos `PascalCase` | `PascalCase` | `camelCase` |
| .NET | `PascalCase.cs` | `PascalCase` | `PascalCase` |
| Python | `snake_case.py` | `PascalCase` | `snake_case` |
| Go | Convención del package, normalmente minúscula | Exportado `PascalCase` | Exportado `PascalCase`, privado `camelCase` |
| Ruby | `snake_case.rb` | `PascalCase` | `snake_case` |
| PHP | PSR del proyecto | `PascalCase` | `camelCase` |
| TypeScript backend | Convención del framework; Nest suele usar sufijos `*.service.ts` | `PascalCase` | `camelCase` |
| TypeScript frontend | Componentes `PascalCase.tsx`; hooks `useXxx.ts`; utilidades según repo | `PascalCase` | `camelCase` |

No renombres brownfield para imponer esta tabla.

## Dependencias e inversión de control

- Spring/.NET/NestJS: constructor injection mediante el contenedor nativo.
- FastAPI: dependencies en el boundary; evita acoplar dominio a `Depends`.
- Django/Rails/Laravel: sigue extensiones nativas antes de introducir un contenedor adicional.
- Express/Fastify/Go: composición explícita y simple; no agregues un framework DI sin requisito.

El dominio no depende del framework cuando el estilo arquitectónico aprobado exige esa separación.

## Errores y validación

- Valida entradas en el boundary mediante DTO/schema y conserva invariantes dentro del dominio.
- Centraliza traducción de errores en middleware/handler del borde.
- Usa códigos estables y trazables; no expongas stack traces o datos sensibles.
- Deriva el formato HTTP del OpenAPI/estándar aprobado. Si falta, registra un formato provisional como decisión inferida, no como contrato definitivo.
- Distingue autenticación (`401`) de autorización (`403`) y conflicto (`409`) según semántica.

## API y datos

- OpenAPI/AsyncAPI/schema aprobado prevalece sobre cualquier default.
- Fechas públicas en formato interoperable y zona explícita, normalmente ISO 8601 UTC.
- Paginación, envelope, ruta base e IDs son decisiones contractuales; no impongas `/api/v1`, `{data,meta}` o UUID sin evidencia.
- Inicializa conexión/migraciones solo cuando persistencia esté diseñada; no inventes entidades.

## Testing mínimo

| Workload | Evidencia greenfield mínima |
|---|---|
| Web | Render del app shell, manejo de error, prueba del vertical slice acordado y, si declara sistema de diseño, `check-design-conformance` sin violaciones |
| API/integrations | Health/liveness de aplicación, error mapping y prueba de contrato mínima |
| Worker | Arranque, dispatch de mensaje de prueba e idempotencia básica |
| Agent service | Arranque, proveedor abstraído, tool contract y evaluación mínima sin efectos reales |

Usa el runner del arquetipo/generador. No agregues un segundo framework de pruebas sin necesidad.

## Documentación

El README debe contener requisitos exactos, instalación reproducible, ejecución local, comandos de validación y variables sin secretos. Registra procedencia en blueprint/receipt, no mediante comentarios repetidos en cada archivo generado.

