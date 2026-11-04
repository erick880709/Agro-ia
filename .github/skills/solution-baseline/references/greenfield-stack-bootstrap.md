# Bootstrap greenfield por stack

Usa esta referencia únicamente después de resolver arquitectura, repositorio, adaptador, motor y versiones exactas. Estos comandos son patrones parametrizados, no autorización para instalar herramientas globales, acceder a red o usar `latest`.

## Reglas comunes

1. Prefiere un arquetipo aprobado del catálogo. Usa el generador nativo como motor de ese arquetipo, no como sustituto de la selección gobernada.
2. Sustituye cada `<resolved-...>` por una versión exacta registrada en el run manifest.
3. Ejecuta primero en el workspace temporal del dry-run.
4. Reutiliza el gestor y lockfile decididos por la arquitectura; si faltan y cambian el resultado, regístralos como decisión pendiente.
5. No instales CLIs globales implícitamente.
6. Elimina ejemplos del framework únicamente en el render temporal y valida que no aporten comportamiento requerido.
7. No produzcas Dockerfile, Compose, pipelines, IaC, Helm, Kubernetes ni despliegues.

## Java y Kotlin

| Stack | Motor/comando parametrizado | Validación mínima |
|---|---|---|
| Spring Boot | Spring Initializr con `bootVersion=<resolved-spring-version>`, `javaVersion=<resolved-java-version>`, `type=<maven-project|gradle-project>` y dependencias aprobadas | Wrapper del proyecto: test y package/build |
| Quarkus | Maven/Gradle plugin fijado a `<resolved-quarkus-version>` | Test y package/build |
| Micronaut | CLI ejecutado en versión `<resolved-micronaut-version>` | Test y build |

No uses `curl` hacia Initializr sin permiso de red. Prefiere wrapper generado y registra Maven/Gradle como decisión, no como default universal.

## .NET

| Workload | Motor/comando parametrizado | Validación mínima |
|---|---|---|
| API con controllers | `dotnet new webapi -n <name> --framework <resolved-tfm> --use-controllers` cuando la versión instalada lo soporte | `dotnet restore`, `dotnet build`, `dotnet test` |
| Minimal API | `dotnet new webapi -n <name> --framework <resolved-tfm>` con opciones confirmadas por `dotnet new webapi --help` | Igual |
| Worker | `dotnet new worker -n <name> --framework <resolved-tfm>` | Igual |

Fija el SDK mediante el mecanismo aprobado del repositorio. Usa templates corporativos instalados por versión cuando existan; no descargues paquetes sin autorización.

## Python

| Workload | Motor/comando parametrizado | Validación mínima |
|---|---|---|
| FastAPI API/integrations | Copier/Cookiecutter corporativo; como fallback aprobado, inicializa el gestor resuelto y agrega FastAPI/servidor en versiones exactas | Sync/install, Ruff si está configurado, typecheck si aplica, Pytest |
| Worker | Arquetipo corporativo del broker/librería elegidos | Igual más smoke del dispatcher |
| Agent service | Arquetipo corporativo con proveedor abstraído y eval harness | Pytest y evals mínimas |
| Django | `django-admin startproject` desde un entorno con Django fijado | Checks, migraciones dry-run y tests |

No impongas Poetry, uv o pip: selecciona lo decidido por arquitectura/equipo y conserva un lockfile determinista.

## JavaScript y TypeScript

| Stack | Motor/comando parametrizado | Validación mínima |
|---|---|---|
| React + Vite | `npm create vite@<resolved-generator-version> <name> -- --template react-ts`, o generador Nx/Copier aprobado | Install reproducible, lint, test, typecheck/build |
| Next.js | `npx create-next-app@<resolved-generator-version> <name> <approved-options>` | Igual |
| NestJS | `npx @nestjs/cli@<resolved-cli-version> new <name> <approved-options>` | Igual |
| Angular | `npx @angular/cli@<resolved-cli-version> new <name> <approved-options>` | Igual |
| Vue | `npm create vue@<resolved-generator-version> <name>` | Igual |
| Svelte | Generador oficial fijado a `<resolved-generator-version>` | Igual |
| Express/Fastify/Hono | Arquetipo corporativo preferido; fallback nativo solo con dependencias exactas y contrato de estructura aprobado | Igual más health/smoke |

Respeta el package manager y su versión exacta fijados por la arquitectura y el lockfile del proyecto.

## Go, Ruby y PHP

| Stack | Motor/comando parametrizado | Validación mínima |
|---|---|---|
| Go | `go mod init <approved-module-path>` y dependencias exactas | `gofmt` check, lint configurado y `go test ./...` |
| Rails | `rails _<resolved-version>_ new <name> <approved-options>` | Lint y tests |
| Sinatra | Bundler y gemas fijadas por lockfile | Igual |
| Laravel | Composer `create-project` con versión exacta | Style/lint y PHPUnit |
| Symfony | Composer `create-project` con versión exacta | Igual |

El module/package path público es una decisión de identidad; no lo inventes.

## Stack no registrado

Consulta documentación oficial y crea primero un adaptador candidato con detectores, motor, comandos, permisos y pruebas contractuales. No improvises un comando de scaffold sobre el repositorio destino.

