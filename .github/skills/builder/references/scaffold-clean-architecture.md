---
name: scaffold-clean-architecture-reference
description: Referencia completa del plugin Gradle Scaffold Clean Architecture de Bancolombia (tareas, parámetros, tipos de módulos, reglas de arquitectura, caché, extensión del plugin). Consultar antes de generar o modificar cualquier proyecto Java/Spring basado en el scaffold.
source: https://bancolombia.github.io/scaffold-clean-architecture/docs/intro
source_repo: https://github.com/bancolombia/scaffold-clean-architecture (carpeta /docs/docs, rama master)
plugin_id: co.com.bancolombia.cleanArchitecture
plugin_version_docs: 4.6.3
plugin_version_master: 4.7.0
generated: 2026-10-01
language: es (comandos, parámetros y valores se conservan literales en inglés)
---

# Scaffold Clean Architecture (Bancolombia) — Referencia para la skill de desarrollo

> **Cómo usar este documento.** Es la fuente de verdad para que la skill de desarrollo genere comandos y estructuras
> del scaffold. Los nombres de tareas, alias, parámetros y valores están copiados **literalmente** de la documentación
> oficial y verificados contra el código fuente del plugin. La skill **no debe inventar** parámetros ni tipos que no
> aparezcan aquí. Si el usuario usa una versión distinta del plugin, advertir que las opciones pueden variar y
> sugerir `gradle tasks` / `gradle help --task <tarea>` para confirmar.

## Índice

1. [Visión general y propósito](#1-visión-general-y-propósito)
2. [Capas de la arquitectura](#2-capas-de-la-arquitectura)
3. [Características (Reactor, Reactive Commons, Secrets Manager, Versionado)](#3-características)
4. [Analytics](#4-analytics)
5. [Requisitos e instalación](#5-requisitos-e-instalación)
6. [Quick Start](#6-quick-start)
7. [Catálogo de tareas (tabla resumen)](#7-catálogo-de-tareas-tabla-resumen)
8. [Generate Project — `ca`](#8-generate-project--cleanarchitecture--ca)
9. [Generate Model — `gm`](#9-generate-model--generatemodel--gm)
10. [Generate Use Case — `guc`](#10-generate-use-case--generateusecase--guc)
11. [Generate Driven Adapter — `gda`](#11-generate-driven-adapter--generatedrivenadapter--gda)
12. [Generate Entry Point — `gep`](#12-generate-entry-point--generateentrypoint--gep)
13. [Generate Helper — `gh`](#13-generate-helper--generatehelper--gh)
14. [Generate Pipeline — `gpl`](#14-generate-pipeline--generatepipeline--gpl)
15. [Generate Acceptance Test — `gat`](#15-generate-acceptance-test--generateacceptancetest--gat)
16. [Generate Performance Test — `gpt`](#16-generate-performance-test--generateperformancetest--gpt)
17. [Validate Structure — `vs`](#17-validate-structure--validatestructure--vs)
18. [Delete Module — `dm`](#18-delete-module--deletemodule--dm)
19. [Update Project — `u`](#19-update-project--updatecleanarchitecture--u)
20. [Avanzado: ArchUnit Analysis](#20-avanzado-archunit-analysis)
21. [Avanzado: Dependency Updater (`internalTask`)](#21-avanzado-dependency-updater-internaltask--it)
22. [Avanzado: Gradle Cache](#22-avanzado-optimización-con-gradle-cache)
23. [Contributing: extender el plugin](#23-contributing-extender-el-plugin)
24. [Opciones presentes en el código no documentadas en el sitio](#24-opciones-presentes-en-el-código-no-documentadas-en-el-sitio)
25. [Erratas detectadas en la documentación oficial](#25-erratas-detectadas-en-la-documentación-oficial)
26. [Guía rápida de decisión para la skill](#26-guía-rápida-de-decisión-para-la-skill)

---

## 1. Visión general y propósito

El **Scaffold Clean Architecture Gradle Plugin** crea proyectos con estructura de Clean Architecture, incluyendo las
dependencias y configuraciones necesarias para empezar a desarrollar bajo esos principios.

- Adopta los principios de **Clean Architecture de Robert C. Martin**: separación de responsabilidades y
  **regla de dependencia** (las dependencias siempre apuntan hacia adentro, de capas externas a internas).
- Se construye como un **proyecto Gradle multimódulo**.
- Genera proyectos **imperativos** (Spring Boot / Spring MVC) y **reactivos** (Spring WebFlux + Project Reactor).
- Licencia Apache 2.0. Calidad monitoreada con SonarCloud, Codecov y OpenSSF Scorecards.
- Existe una variante para **Elixir**: https://bancolombia.github.io/scaffold-clean-architecture-ex/
- Lectura recomendada: [Clean Architecture — Aislando los detalles](https://medium.com/bancolombia-tech/clean-architecture-aislando-los-detalles-4f9530f35d7a)

## 2. Capas de la arquitectura

### 2.1 Domain (capa más interna)

Encapsula la lógica y reglas de negocio mediante modelos de dominio y casos de uso. Define los **puertos como
interfaces** y los modelos/casos de uso como clases. Está compuesta por dos módulos Gradle:

| Módulo    | Responsabilidad |
|-----------|-----------------|
| `model`   | Modelos y entidades de dominio (representación de reglas y lógica de negocio). Define los **puertos (interfaces / gateways)** que usará `usecase`. |
| `usecase` | Casos de uso del sistema: lógica de aplicación. Reacciona a invocaciones de los `entry-points` y orquesta los flujos hacia `domain` usando los puertos definidos. |

### 2.2 Infrastructure

Contiene las tecnologías concretas e implementaciones de los puertos del dominio. Tres grupos de módulos:

| Grupo             | Responsabilidad |
|-------------------|-----------------|
| `entry-points`    | Puntos de entrada de la aplicación / inicio de los flujos de negocio (controladores REST, consumidores Kafka, etc.). |
| `driven-adapters` | Implementaciones externas al sistema: conexiones a servicios REST, SOAP, bases de datos, lectura de archivos planos y cualquier fuente de datos con la que se interactúe. |
| `helpers`         | Utilidades generales para Driven Adapters y Entry Points. |

### 2.3 Application (capa más externa)

Módulo `applications/app-service`. Ensambla los módulos, resuelve dependencias y **crea automáticamente los beans de los
casos de uso**, inyectándoles instancias concretas de las dependencias declaradas. Arranca la aplicación: es el
**único módulo** con `public static void main(String[] args)`.

### 2.4 Regla de dependencias entre módulos (resumen operativo)

```
app-service ──► entry-points, driven-adapters, helpers, usecase, model
entry-points / driven-adapters / helpers ──► usecase y/o model (+ dependencias externas)
usecase ──► model (ÚNICAMENTE)
model ──► (ninguna dependencia)
Infraestructura ──X──► app-service (prohibido)
```

## 3. Características

### 3.1 Project Reactor

[Reactor](https://projectreactor.io) es una librería reactiva altamente optimizada para aplicaciones no bloqueantes en
la JVM, basada en la [Reactive Streams Specification](https://github.com/reactive-streams/reactive-streams-jvm).
Soporta alto throughput con bajo consumo de memoria; apta para microservicios orientados a eventos.

Implementa dos publishers con back-pressure no bloqueante:
- [`Flux<T>`](https://projectreactor.io/docs/core/release/api/reactor/core/publisher/Flux.html) — 0..N elementos.
- [`Mono<T>`](https://projectreactor.io/docs/core/release/api/reactor/core/publisher/Mono.html) — 0..1 elemento.

### 3.2 Reactive Commons

[Reactive Commons](https://reactivecommons.org/reactive-commons-java) es una API reactiva para comunicación asíncrona
dirigida por mensajes, basada en Reactor. Permite publicar mensajes sobre un bus de eventos como **RabbitMQ** (y Kafka,
según la opción `--tech` de los módulos asíncronos) y consumirlos con APIs funcionales con back-pressure.
Semánticas de mensaje soportadas: **Events, Commands y Queries**.

### 3.3 Secrets Manager

Los adapters pueden configurarse para obtener secretos en tiempo de ejecución desde un Secrets Manager u otro servicio,
evitando secretos en el código. Utilidad: https://github.com/bancolombia/secrets-manager
(Relacionado: parámetros `--secret` y el driven adapter `secrets` con `--secrets-backend`.)

### 3.4 Versionado

Se usa [Semantic Versioning](https://semver.org) `MAJOR.MINOR.PATCH`:
- **MAJOR**: cambios incompatibles de API.
- **MINOR**: nueva funcionalidad retrocompatible.
- **PATCH**: corrección de errores retrocompatible.
Etiquetas adicionales de pre-release y metadata de build están disponibles como extensiones.

## 4. Analytics

El plugin recolecta estadísticas de uso de tareas (salvo que se desactive explícitamente). Al ejecutar cualquier tarea
se notifica la recolección; tras habilitar/deshabilitar explícitamente ya no se vuelve a notificar.

| Tarea | Alias | Parámetro | Valores |
|-------|-------|-----------|---------|
| `analytics` | `a` | `--enabled` | `true`, `false` |

```shell
gradle analytics --enabled true    # gradle a --enabled true  → habilita y suprime el aviso
gradle analytics --enabled false   # gradle a --enabled false → deshabilita
```

**Qué se recolecta:** comandos y flags de cada ejecución; sistema operativo y versión; vendor y versión de Java;
versiones de especificación y runtime de Java; versión del plugin; lenguaje (`java`); nombre de la tarea; información
del workspace (lenguaje, usuario que ejecuta); para `generateUseCase`, `generateModel`, `generateHelper` y `deleteModule`
se envía el **nombre**; para todas las tareas: tipo y nombre, duración y tipo de proyecto (reactive/imperative).

> Recomendación para la skill: en entornos corporativos/bancarios sugerir `gradle a --enabled false` como paso inicial
> si la política de la organización restringe telemetría.

## 5. Requisitos e instalación

- **Java JRE 17 o superior.**
- **Gradle 9.2.1 o superior** (recomendado también para habilitar todas las propiedades de caché, ver §22).
- Plugin en Gradle Plugin Portal: https://plugins.gradle.org/plugin/co.com.bancolombia.cleanArchitecture

Crear un directorio para el proyecto y un `build.gradle` con:

```groovy
plugins {
    id 'co.com.bancolombia.cleanArchitecture' version '4.6.3'
}
```

Listar tareas disponibles:

```bash
gradle tasks
```

## 6. Quick Start

### Mac OS / Linux

```sh
mkdir scaffold-quick-start
cd scaffold-quick-start
echo "plugins {
    id 'co.com.bancolombia.cleanArchitecture' version '4.6.3'
}" > build.gradle
gradle wrapper
./gradlew ca --name=ScaffoldQuickStart
./gradlew gep --type webflux
./gradlew bootRun
```

### Windows — PowerShell

```powershell
New-Item -ItemType Directory -Name "scaffold-quick-start"
Set-Location -Path "scaffold-quick-start"
@"
plugins {
    id 'co.com.bancolombia.cleanArchitecture' version '4.6.3'
}
"@ | Set-Content -Path "build.gradle"
gradle wrapper
.\gradlew ca --name=ScaffoldQuickStart
.\gradlew gep --type webflux
.\gradlew bootRun
```

### Windows — CMD

```cmd
@echo off
mkdir scaffold-quick-start
cd scaffold-quick-start
(
echo plugins {
echo     id 'co.com.bancolombia.cleanArchitecture' version '4.6.3'
echo }
) > build.gradle
gradle wrapper
gradlew ca --name=ScaffoldQuickStart
gradlew gep --type webflux
gradlew bootRun
```

Resultado: abrir http://localhost:8080/api/usecase/path → responde string vacío. Para cambiar la respuesta, modificar la
clase `Handler` en `entry-points/reactive-web`.

## 7. Catálogo de tareas (tabla resumen)

| Tarea (nombre largo)       | Alias | Parámetros obligatorios | Propósito |
|----------------------------|-------|-------------------------|-----------|
| `cleanArchitecture`        | `ca`  | —                       | Genera la estructura base del proyecto |
| `generateModel`            | `gm`  | `--name`                | Modelo + gateway (interface) en `domain/model` |
| `generateUseCase`          | `guc` | `--name`                | Caso de uso en `domain/usecase` |
| `generateDrivenAdapter`    | `gda` | `--type` (+`--name` si `generic`) | Módulo en `infrastructure/driven-adapters` |
| `generateEntryPoint`       | `gep` | `--type` (+`--name` si `generic`) | Módulo en `infrastructure/entry-points` |
| `generateHelper`           | `gh`  | `--name`                | Módulo en `infrastructure/helpers` |
| `generatePipeline`         | `gpl` | `--type`                | Pipeline CI en `./deployment/` |
| `generateAcceptanceTest`   | `gat` | —                       | Subproyecto Karate en `./deployment/` |
| `generatePerformanceTest`  | `gpt` | `--type`                | Pruebas de performance en `./performance-test/` |
| `validateStructure`        | `vs`  | —                       | Valida la regla de dependencias y buenas prácticas |
| `deleteModule`             | `dm`  | `--module`              | Elimina un subproyecto |
| `updateCleanArchitecture`  | `u`   | —                       | Actualiza plugin y dependencias |
| `analytics`                | `a`   | `--enabled`             | Habilita/deshabilita analytics |
| `internalTask`             | `it`  | `--action`              | Tareas internas (p. ej. actualizador de dependencias) |

Sintaxis de parámetros: Gradle acepta `--param=valor` y `--param valor`. Se puede usar `gradle` o `./gradlew`
(preferir `./gradlew` una vez generado el wrapper).

## 8. Generate Project — `cleanArchitecture | ca`

Genera la estructura Clean Architecture en el proyecto.

> ⚠️ **Precaución:** ejecutarla sobre un proyecto existente **sobrescribe `main.gradle`, `build.gradle` y
> `gradle.properties`**.

| Parámetro      | Descripción | Uso | Default |
|----------------|-------------|-----|---------|
| `package`      | Paquete principal/base del proyecto | `--package=<desired.base.package>` | `co.com.bancolombia` |
| `type`         | Enfoque reactivo o imperativo | `--type=<imperative or reactive>` | `reactive` |
| `name`         | Nombre del proyecto | `--name=<Project name>` | `cleanArchitecture` |
| `lombok`       | Usar Lombok | `--lombok=<true or false>` | `true` |
| `metrics`      | Habilitar métricas con Micrometer | `--metrics=<true or false>` | `true` |
| `mutation`     | Habilitar framework de mutation testing | `--mutation=<true or false>` | `true` |
| `java-version` | Versión de Java | `--java-version=<17, 21 or 25>` | `25` |

(Ver §24 para `--force` y `--example`, presentes en el código.)

```shell
gradle cleanArchitecture --package=co.com.bancolombia --type=reactive --name=NameProject --lombok=true
gradle ca --package=co.com.bancolombia --type=reactive --name=NameProject --lombok=true
```

Estructura generada:

```bash
📦NameProject
┣ 📂applications
┃ ┗ 📂app-service
┃ ┃ ┣ 📂src
┃ ┃ ┃ ┣ 📂main
┃ ┃ ┃ ┃ ┣ 📂java
┃ ┃ ┃ ┃ ┃ ┗ 📂[package]
┃ ┃ ┃ ┃ ┃ ┃ ┣ 📂config
┃ ┃ ┃ ┃ ┃ ┃ ┃ ┗ 📜[configs and beans]
┃ ┃ ┃ ┃ ┃ ┃ ┗ 📜MainApplication.java
┃ ┃ ┃ ┃ ┗ 📂resources
┃ ┃ ┃ ┃ ┃ ┣ 📜[properties]
┃ ┃ ┃ ┗ 📂test
┃ ┃ ┃ ┃ ┗ 📂java
┃ ┃ ┃ ┃ ┃ ┗ 📂[package]
┃ ┃ ┗ 📜build.gradle
┣ 📂deployment
┃ ┣ 📜[Dockerfile, Pipelines as a code]
┣ 📂domain
┃ ┣ 📂model
┃ ┃ ┣ 📂src/main/java/[package]
┃ ┃ ┣ 📂src/test/java/[package]
┃ ┃ ┗ 📜build.gradle
┃ ┗ 📂usecase
┃ ┃ ┣ 📂src/main/java/[package]
┃ ┃ ┣ 📂src/test/java/[package]/usecase
┃ ┃ ┗ 📜build.gradle
┣ 📂infrastructure
┃ ┣ 📂driven-adapters
┃ ┣ 📂entry-points
┃ ┗ 📂helpers
┣ 📜.gitignore
┣ 📜build.gradle
┣ 📜gradle.properties
┣ 📜lombok.config
┣ 📜main.gradle
┣ 📜README.md
┗ 📜settings.gradle
```

## 9. Generate Model — `generateModel | gm`

Genera una clase y una interface (gateway) en la capa model. Parámetro obligatorio: `name`.

```shell
gradle generateModel --name=[modelName]
gradle gm --name [modelName]
```

```bash
📦domain
┣ 📂model
┃ ┣ 📂src/main/java/[package]/model
┃ ┃ ┣ 📂gateways
┃ ┃ ┃ ┗ 📜ModelRepository.java
┃ ┃ ┗ 📜Model.java
┃ ┣ 📂src/test/java/[package]/model
┃ ┗ 📜build.gradle
```

Convención resultante: paquete `[package].model.<nombre>`; puerto en `gateways/<Nombre>Repository.java`.
Respetar las reglas ArchUnit §20 (sin sufijos `dto/request/response` ni nombres de tecnología).

## 10. Generate Use Case — `generateUseCase | guc`

Genera una clase de caso de uso. Parámetro obligatorio: `name`.

```shell
gradle generateUseCase --name=[useCaseName]
gradle guc --name [useCaseName]
```

```bash
📦domain
┗ 📂usecase
┃ ┣ 📂src/main/java/[package]/usecase/business
┃ ┃ ┗ 📜BusinessUseCase.java
┃ ┣ 📂src/test/java/[package]/usecase/business
┃ ┗ 📜build.gradle
```

Convención: paquete `[package].usecase.<nombre>`, clase `<Nombre>UseCase`. Atributos deben ser `final`
(regla ArchUnit 2.5). Los beans de use case se crean automáticamente en `app-service`.

## 11. Generate Driven Adapter — `generateDrivenAdapter | gda`

Genera un módulo en `infrastructure/driven-adapters`. Obligatorio: `--type`. Si el tipo es `generic`, también `--name`.

```shell
gradle generateDrivenAdapter --type=[drivenAdapterType]
gradle gda --type [drivenAdapterType]
```

### 11.1 Tipos y parámetros

| Type                     | Nombre                           | Parámetro           | Valores                                | Default               |
|--------------------------|----------------------------------|---------------------|----------------------------------------|-----------------------|
| `generic`                | Empty Driven Adapter             | `--name`            | String                                 | —                     |
| `asynceventbus`          | Async Event Bus                  | `--eda`             | `true`, `false`                        | `false`               |
|                          |                                  | `--tech`            | `rabbitmq`, `kafka`, `rabbitmq,kafka`  | `rabbitmq`            |
| `binstash`               | Bin Stash                        | `--cache-mode`      | `LOCAL`, `CENTRALIZED`, `HYBRID`       | `LOCAL`               |
| `cognitotokenprovider`   | Cognito token generator          | —                   | —                                      | —                     |
| `dynamodb`               | Dynamo DB adapter                | —                   | —                                      | —                     |
| `jpa`                    | JPA Repository                   | `--secret`          | `true`, `false`                        | `false`               |
| `kms`                    | AWS Key Management Service       | —                   | —                                      | —                     |
| `mongodb`                | Mongo Repository                 | `--secret`          | `true`, `false`                        | `false`               |
| `mq`                     | JMS MQ Client to send messages   | —                   | —                                      | —                     |
| `r2dbc`                  | R2dbc Postgresql Client          | —                   | —                                      | —                     |
| `redis`                  | Redis                            | `--mode`            | `template`, `repository`               | `template`            |
|                          |                                  | `--secret`          | `true`, `false`                        | `false`               |
| `restconsumer`           | Rest Client Consumer             | `--url`             | String (URL)                           | —                     |
|                          |                                  | `--from-swagger`    | File path                              | `swagger.yaml`        |
| `rsocket`                | RSocket Requester                | —                   | —                                      | —                     |
| `s3`                     | AWS Simple Storage Service       | —                   | —                                      | —                     |
| `secrets`                | Secrets Manager Bancolombia      | `--secrets-backend` | `aws_secrets_manager`, `vault`         | `aws_secrets_manager` |
| `secretskafkastrimzi`    | Secrets for Kafka Strimzi        | `--secret-name`     | String                                 | —                     |
| `sqs`                    | SQS message sender               | —                   | —                                      | —                     |

### 11.2 Notas por opción

- `--eda=true` (asynceventbus): habilita el modo Event-Driven Architecture de Reactive Commons.
- `--tech`: tecnología de broker para Reactive Commons; `rabbitmq,kafka` genera soporte para ambos.
- `--secret=true` (jpa, mongodb, redis): integra la obtención de credenciales vía Secrets Manager (genera p. ej.
  `config/DBSecret.java` en JPA).
- `--mode` (redis): `template` (ReactiveRedisTemplate/RedisTemplate) o `repository` (estilo repositorio).
- `--url` (restconsumer): URL base del servicio a consumir. `--from-swagger`: genera el cliente a partir de un
  archivo OpenAPI/Swagger.
- `--cache-mode` (binstash): estrategia de caché `LOCAL`, `CENTRALIZED` o `HYBRID`.
- `--secrets-backend` (secrets): `aws_secrets_manager` o `vault` (HashiCorp Vault).

### 11.3 Ejemplos

```shell
gradle gda --type=generic --name=PaymentsCore
gradle gda --type=jpa --secret=true
gradle gda --type=redis --mode=repository --secret=true
gradle gda --type=restconsumer --url=https://api.example.com
gradle gda --type=restconsumer --from-swagger=swagger.yaml
gradle gda --type=asynceventbus --eda=true --tech=kafka
gradle gda --type=secrets --secrets-backend=vault
gradle gda --type=binstash --cache-mode=HYBRID
gradle gda --type=secretskafkastrimzi --secret-name=my-kafka-secret
```

### 11.4 Estructura de ejemplo (jpa)

```bash
📦infrastructure
┣ 📂driven-adapters
┃ ┗ 📂jpa-repository
┃ ┃ ┣ 📂src/main/java/[package]/jpa
┃ ┃ ┃ ┣ 📂config
┃ ┃ ┃ ┃ ┗ 📜DBSecret.java
┃ ┃ ┃ ┣ 📂helper
┃ ┃ ┃ ┃ ┗ 📜AdapterOperations.java
┃ ┃ ┃ ┣ 📜JPARepository.java
┃ ┃ ┃ ┗ 📜JPARepositoryAdapter.java
┃ ┃ ┣ 📂src/test/java/[package]/jpa/helper
┃ ┃ ┗ 📜build.gradle
```

## 12. Generate Entry Point — `generateEntryPoint | gep`

Genera un módulo en `infrastructure/entry-points`. Obligatorio: `--type`. Si es `generic`, también `--name`.

```shell
gradle generateEntryPoint --type=[entryPointType]
gradle gep --type [entryPointType]
```

### 12.1 Tipos y parámetros

| Type                  | Nombre                                  | Parámetro                    | Valores                                   | Default                |
|-----------------------|-----------------------------------------|------------------------------|-------------------------------------------|------------------------|
| `generic`             | Empty Entry Point                       | `--name`                     | String                                    | —                      |
| `grpc`                | gRPC Server Entry Point                 | —                            | —                                         | —                      |
| `asynceventhandler`   | Async Event Handler                     | `--eda`                      | `true`, `false`                           | `false`                |
|                       |                                         | `--tech`                     | `rabbitmq`, `kafka`, `rabbitmq,kafka`     | `rabbitmq`             |
| `graphql`             | API GraphQL                             | `--pathgql`                  | String (path)                             | `/graphql`             |
| `kafka`               | Kafka Consumer                          | —                            | —                                         | —                      |
| `mcp`                 | MCP Server (Model Context Protocol)     | `--name`                     | String                                    | —                      |
|                       |                                         | `--enable-tools`             | `true`, `false`                           | `true`                 |
|                       |                                         | `--enable-resources`         | `true`, `false`                           | `true`                 |
|                       |                                         | `--enable-prompts`           | `true`, `false`                           | `true`                 |
|                       |                                         | `--enable-security`          | `true`, `false`                           | `true`                 |
|                       |                                         | `--enable-audit`             | `true`, `false`                           | `true`                 |
| `mq`                  | JMS MQ Client to listen messages        | —                            | —                                         | —                      |
| `restmvc`             | API REST (Spring Boot Starter Webmvc)   | `--server`                   | `tomcat`, `jetty`                         | `tomcat`               |
|                       |                                         | `--authorization`            | `true`, `false`                           | `false`                |
|                       |                                         | `--versioning`               | `HEADER`, `PATH`, `NONE`                  | `NONE`                 |
|                       |                                         | `--from-swagger`             | File path                                 | `swagger.yaml`         |
|                       |                                         | `--swagger`                  | `true`, `false`                           | `false`                |
| `rsocket`             | Rsocket Controller Entry Point          | —                            | —                                         | —                      |
| `sqs`                 | SQS Listener                            | —                            | —                                         | —                      |
| `webflux`             | API REST (Spring Boot Starter WebFlux)  | `--router`                   | `true`, `false`                           | `true`                 |
|                       |                                         | `--authorization`            | `true`, `false`                           | `false`                |
|                       |                                         | `--versioning`               | `HEADER`, `PATH`, `NONE`                  | `NONE`                 |
|                       |                                         | `--from-swagger`             | File path                                 | `swagger.yaml`         |
|                       |                                         | `--swagger`                  | `true`, `false`                           | `false`                |
| `kafkastrimzi`        | Kafka Strimzi Consumer Entry Point      | `--name`                     | String                                    | —                      |
|                       |                                         | `--topic-consumer`           | String (topic name)                       | `test-with-registries` |
| `agent`               | Spring AI A2A Reactive Agent            | `--name`                     | String                                    | nombre del proyecto    |
|                       |                                         | `--agent-enable-kafka`       | `true`, `false`                           | `true`                 |
|                       |                                         | `--agent-enable-mcp-client`  | `true`, `false`                           | `true`                 |
|                       |                                         | `--agent-role`               | `collaborative`, `supervisor`, `hybrid`   | `collaborative`        |

### 12.2 Notas por opción (REST)

- `--router` (webflux): `true` genera **Router Functions** (`RouterRest` + `Handler`); `false` genera controladores
  anotados (`@RestController`).
- `--authorization=true`: habilita autorización de requests mediante **JWT**.
- `--versioning`: estrategia de versionado de API — `HEADER`, `PATH` o `NONE`. En el código se describe como
  "disponible solo con router function" (aplica a webflux con `--router=true`).
- `--swagger=true`: agrega configuración Swagger/OpenAPI al entry point REST.
- `--from-swagger=<archivo>`: genera el entry point a partir de un `swagger.yaml` (contract-first).
- `--server` (restmvc): servidor web embebido.

| Referencia **serverOption** | Nombre                  |
|-----------------------------|-------------------------|
| `tomcat`                    | Tomcat server (default) |
| `jetty`                     | Jetty server            |

```shell
gradle generateEntryPoint --type=restmvc --server=[serverOption]
gradle gep --type=restmvc --server=[serverOption]
```

Ejemplos:

```shell
gradle gep --type=webflux --router=true --authorization=true --versioning=PATH --swagger=true
gradle gep --type=webflux --from-swagger=swagger.yaml
gradle gep --type=restmvc --server=jetty --authorization=true
gradle gep --type=graphql --pathgql=/api/graphql
gradle gep --type=asynceventhandler --eda=true --tech=rabbitmq,kafka
gradle gep --type=generic --name=BatchTrigger
```

Estructura genérica:

```bash
📦infrastructure
┣ 📂entry-points
┃ ┗ 📂generic
┃ ┃ ┣ 📂src/main/java/[package]/generic
┃ ┃ ┣ 📂src/test/java/[package]/generic
┃ ┃ ┗ 📜build.gradle
```

### 12.3 Kafka Strimzi Consumer (`kafkastrimzi`)

```shell
gradle generateEntryPoint --type=kafkastrimzi
gradle gep --type=kafkastrimzi
gradle generateEntryPoint --type=kafkastrimzi --name=myConsumer --topic-consumer=myTopic
gradle gep --type=kafkastrimzi --name=myConsumer --topic-consumer=myTopic
```

Genera un entry point especializado para consumir mensajes Kafka usando Strimzi, con parámetros personalizados.
Complemento natural: driven adapter `secretskafkastrimzi`.

### 12.4 MCP Server (`mcp`)

Genera un **servidor MCP reactivo** (Spring AI) con capacidades de Tools, Resources y Prompts.

```shell
gradle generateEntryPoint --type=mcp
gradle gep --type=mcp
```

| Parámetro            | Valores        | Default | Descripción |
|----------------------|----------------|---------|-------------|
| `--name`             | String         | `null`  | Nombre del MCP Server |
| `--enable-tools`     | `true`/`false` | `true`  | Habilita Tools |
| `--enable-resources` | `true`/`false` | `true`  | Habilita Resources |
| `--enable-prompts`   | `true`/`false` | `true`  | Habilita Prompts |
| `--enable-security`  | `true`/`false` | `true`  | Seguridad OAuth2 / Entra ID |
| `--enable-audit`     | `true`/`false` | `true`  | Audit logging (requiere AOP) |

```shell
# Todas las capacidades (por defecto incluye seguridad y auditoría)
gradle generateEntryPoint --type=mcp
# Solo Tools
gradle generateEntryPoint --type=mcp --enable-tools=true --enable-resources=false --enable-prompts=false
# Solo Resources
gradle generateEntryPoint --type=mcp --enable-tools=false --enable-resources=true --enable-prompts=false
# Nombre personalizado
gradle generateEntryPoint --type=mcp --name=BancolombiaAssistant
# Sin seguridad (solo modo desarrollo)
gradle generateEntryPoint --type=mcp --enable-security=false
# Sin auditoría
gradle generateEntryPoint --type=mcp --enable-audit=false
```

Estructura generada:

```bash
infrastructure/
└── entry-points/
    └── mcp-server/
        ├── build.gradle
        └── src/
            ├── main/java/[package]/mcp/
            │   ├── tools/        (HealthTool.java, ExampleTool.java)
            │   ├── resources/    (SystemInfoResource.java, UserInfoResource.java)
            │   ├── prompts/      (ExamplePrompt.java)
            │   └── audit/        (McpAuditAspect.java)          # si audit habilitado
            └── test/java/[package]/mcp/
                ├── tools/ resources/ prompts/
                └── audit/        (McpAuditAspectTest.java)      # si audit habilitado
applications/
└── app-service/src/
    ├── main/java/co/com/bancolombia/config/McpSecurityConfig.java      # si security habilitado
    └── test/java/co/com/bancolombia/config/McpSecurityConfigTest.java  # si security habilitado
```

Configuración automática en `application.yaml`:

```yaml
spring:
  ai:
    mcp:
      server:
        protocol: "STATELESS"
        name: "${spring.application.name}"
        version: "1.0.0"
        type: "ASYNC"
        instructions: |
          Reactive MCP Server with capabilities:
          - Tools: Executable tools
          - Resources: Access to system and user data
          - Prompts: Custom conversation templates

          Security: Authenticated via Entra ID (Bearer Token)
        streamable-http:
          mcp-endpoint: "/mcp/${spring.application.name}"
        capabilities:
          tool: true
          resource: true
          prompt: true
        request-timeout: "30s"
  # Si --enable-security=true
  security:
    oauth2:
      resourceserver:
        jwt:
          issuer-uri: https://login.microsoftonline.com/${TENANT_ID}/v2.0
          client-id: ${CLIENT_ID}

jwt:
  json-exp-roles: /roles  # JSON path para extracción de roles
```

**Seguridad (`McpSecurityConfig`, por defecto activa):**
- OAuth2 Resource Server que valida JWT de Entra ID.
- Validación de audiencia (`aud`), app ID (`appid`) e issuer.
- Extracción de roles desde claims con JSON path configurable.
- Method Security: habilita `@PreAuthorize` para RBAC.
- Endpoints públicos: actuator `health` e `info`.
- Log explícito de accesos denegados (usuario y path).

**Auditoría (`McpAuditAspect`, por defecto activa):**
- Audita todas las llamadas a métodos `@Tool`, `@McpResource` y `@McpPrompt`.
- Registra: **quién** (client ID del JWT: `appid`, `azp` o `aud`), **qué** (clase, método, argumentos),
  **cuándo** (timestamp del logging), **resultado** (éxito/fallo), **performance** (ms).
- Soporte reactivo con `Mono`; contexto de seguridad desde `ReactiveSecurityContextHolder`.

```
📊 [AUDIT] TOOL llamado por: a1b2c3d4-client-id | Método: ExampleTool.echo | Args: ["hello"]
✅ [AUDIT] TOOL exitoso | Client: a1b2c3d4-client-id | Método: ExampleTool.echo | Tiempo: 45ms
```

**Desarrollo de componentes:**

```java
// Tool
@Component
public class CalculatorTool {
    @McpTool(name = "multiply", description = "Multiplies two numbers")
    public Mono<Integer> multiply(
            @McpToolParam(description = "First number", required = true) int a,
            @McpToolParam(description = "Second number", required = true) int b) {
        return Mono.just(a * b);
    }
}

// Resource
@Component
public class ConfigResource {
    @McpResource(uri = "resource://config/app", name = "app-config", description = "Application configuration")
    public Mono<ReadResourceResult> getConfig() {
        return Mono.fromCallable(() -> { /* Implementation */ });
    }
}

// Prompt
@Component
public class SupportPrompt {
    @McpPrompt(name = "customer-support", description = "Generates a customer support prompt")
    public Mono<GetPromptResult> customerSupport(@McpArg(name = "issue", required = true) String issue) {
        return Mono.fromCallable(() -> { /* Implementation */ });
    }
}
```

### 12.5 Agent — Spring AI A2A (`agent`)

Genera un esqueleto reactivo **A2A (Agent-to-Agent)** sobre Spring AI y WebFlux. Expone dos endpoints REST estándar A2A:
`POST /message:send` y `GET /.well-known/agent-card.json`; opcionalmente transporte Kafka. Usa el protocolo A2A con
identificadores de correlación y traza para observabilidad.

El adapter de chat es **mutuamente excluyente**:
- `--agent-enable-mcp-client=true` → agrega `mcp-client`.
- `--agent-enable-mcp-client=false` → agrega `spring-ai-adapter`.

```shell
gradle generateEntryPoint --type=agent
gradle gep --type=agent
```

| Parámetro                   | Valores | Default | Descripción |
|-----------------------------|---------|---------|-------------|
| `--name`                    | String  | nombre del proyecto | Nombre del agente (usado en `spring.application.name`) |
| `--agent-enable-kafka`      | `true`/`false` | `true` | Agrega consumer + producer Kafka |
| `--agent-enable-mcp-client` | `true`/`false` | `true` | Usa `mcp-client` en lugar de `spring-ai-adapter` para tool use |
| `--agent-role`              | `collaborative`/`supervisor`/`hybrid` | `collaborative` | Rol del agente; determina exposición REST y adapters |

Roles:
- `collaborative`: REST + Kafka + MCP client (comportamiento por defecto).
- `supervisor`: REST + Kafka + spring-ai-adapter; expone endpoint REST de negocio.
- `hybrid`: combina capacidades collaborative y supervisor.

```shell
gradle generateEntryPoint --type=agent --name=my-agent --agent-role=collaborative
gradle generateEntryPoint --type=agent --name=my-agent --agent-role=supervisor
gradle generateEntryPoint --type=agent --name=my-agent --agent-role=hybrid
# Mínimo: solo REST, sin Kafka ni MCP → spring-ai-adapter como implementación de ChatGateway
gradle generateEntryPoint --type=agent --name=my-agent --agent-role=collaborative --agent-enable-kafka=false --agent-enable-mcp-client=false
```

Estructura generada:

```bash
domain/
├── model/src/main/java/[package]/model/
│   ├── a2a/
│   │   ├── SendMessageRequest.java   # Envelope de request A2A entrante
│   │   ├── SendMessageResponse.java  # Envelope de response A2A saliente
│   │   ├── Message.java              # Contenido (role + content)
│   │   ├── Task.java                 # Resultado con estado y tiempos
│   │   ├── Error.java                # Modelo de error estructurado
│   │   └── AgentCard.java            # Metadata para /.well-known/agent-card.json
│   └── chat/gateways/
│       ├── ChatGateway.java          # Puerto: prompt → LLM → Mono<String>
│       └── AgentResponseGateway.java # Puerto: publicar respuesta en Kafka
└── usecase/src/main/java/[package]/usecase/
    └── AgentChatUseCase.java         # Lógica central: llamada LLM + ruteo de respuesta
infrastructure/
├── entry-points/reactive-web/
│   ├── build.gradle
│   └── src/main/java/[package]/api/
│       ├── Handler.java              # POST /message:send
│       ├── RouterRest.java           # /message:send + /.well-known/agent-card.json
│       └── config/ (CorsConfig.java, JacksonConfig.java [JsonMapper, Jackson 3], SecurityHeadersConfig.java)
│   └── src/test/java/[package]/api/ (HandlerTest.java, RouterRestTest.java)
└── driven-adapters/
    ├── mcp-client/ ... mcpclient/adapter/ChatGatewayAdapter.java     # si --agent-enable-mcp-client=true
    └── spring-ai-adapter/ ... chat/SpringAiChatAdapter.java           # si --agent-enable-mcp-client=false
# Si --agent-enable-kafka=true:
infrastructure/entry-points/reactive-web/src/main/java/[package]/kafka/
├── consumer/ (KafkaConsumer.java, config/KafkaConfig.java)
└── producer/ (KafkaProducerAdapter.java, config/KafkaProducerConfig.java)
```

Configuración automática en `application.yaml`:

```yaml
spring:
  application:
    name: "my-agent"
  ai:
    openai:
      api-key: "${LLM_API_KEY:lm-studio}"
      base-url: "${LLM_URL:http://localhost:1234}"
      chat:
        options:
          model: "${LLM_MODEL:local-model}"
          temperature: "0.0"
    # Si --agent-enable-mcp-client=true
    mcp:
      client:
        streamable-http:
          connections:
            mcp-server-1:
              url: "${MCP_SERVER_URL:http://localhost:8080}"
              endpoint: "${MCP_SERVER_ENDPOINT:/mcp/stream}"
# Si --agent-enable-kafka=true
adapters:
  kafka:
    consumer:
      topic: "${KAFKA_CONSUMER_TOPIC:ms_test-commands}"
    producer:
      topic: "${KAFKA_PRODUCER_TOPIC:ms_test-responses}"
agent:
  system-prompt: "You are a specialised agent called 'my-agent'. Use available MCP tools. Respond in JSON."
cors:
  allowed-origins: "${CORS_ALLOWED_ORIGINS:http://localhost:4200}"
```

### 12.6 gRPC Server (`grpc`)

Usa la integración oficial [Spring gRPC](https://docs.spring.io/spring-grpc/reference/)
(`spring-boot-starter-grpc-server`). Incluye configuración de Protocol Buffers, servicio de ejemplo y mapeo de errores.

```shell
gradle generateEntryPoint --type=grpc
gradle gep --type=grpc
```

```bash
infrastructure/entry-points/grpc/
├── build.gradle
└── src/
    ├── main/java/[package]/grpc/ (GrpcServerEntryPoint.java, mapper/ErrorMapper.java)
    ├── main/proto/service.proto
    └── test/java/[package]/grpc/GrpcServerEntryPointTest.java
```

`application.yaml`:

```yaml
spring:
  grpc:
    server:
      port: ${GRPC_SERVER_PORT:9090}
```

| Dependencia | Descripción |
|-------------|-------------|
| `spring-boot-starter-grpc-server` | Integración oficial Spring Boot para gRPC |
| `grpc-services` | Servicios gRPC (health, reflection) |
| `spring-grpc-test` | Utilidades de testing Spring gRPC |
| `protobuf-gradle-plugin` | Plugin Gradle para compilar proto |

`service.proto` generado:

```protobuf
syntax = "proto3";
package grpc;
import "google/protobuf/empty.proto";
option java_multiple_files = true;
option java_package = "co.com.bancolombia.grpc";

service CustomService {
  rpc getById(Request) returns (Response);
  rpc health(google.protobuf.Empty) returns (HealthResponse);
}
message Request { string id = 1; }
message Response { string id = 1; string message = 2; }
message HealthResponse { string status = 1; }
```

Compilar:

```shell
./gradlew :grpc:generateProto
./gradlew :grpc:compileJava
```

Personalización: (1) editar `service.proto`; (2) inyectar use cases en `GrpcServerEntryPoint` e implementar métodos;
(3) mapear excepciones de dominio en `ErrorMapper`.

Ejemplo de nueva RPC:

```protobuf
service CustomService {
  rpc createUser(CreateUserRequest) returns (CreateUserResponse);
}
message CreateUserRequest { string name = 1; string email = 2; }
message CreateUserResponse { string id = 1; string status = 2; }
```

```java
@Override
public void createUser(CreateUserRequest request, StreamObserver<CreateUserResponse> responseObserver) {
    try {
        var result = createUserUseCase.execute(request.getName(), request.getEmail());
        CreateUserResponse response = CreateUserResponse.newBuilder()
                .setId(result.getId())
                .setStatus("CREATED")
                .build();
        responseObserver.onNext(response);
        responseObserver.onCompleted();
    } catch (Exception e) {
        responseObserver.onError(errorMapper.map(e));
    }
}
```

## 13. Generate Helper — `generateHelper | gh`

Genera un módulo en `infrastructure/helpers`. Parámetro obligatorio: `name`. (Tipo único en el código: `generic`.)

```shell
gradle generateHelper --name=[helperName]
gradle gh --name=[helperName]
```

## 14. Generate Pipeline — `generatePipeline | gpl`

Genera un pipeline CI en `./deployment/`. Obligatorio: `--type`. Opcional: `--mono-repo` (default `false`).

```shell
gradle generatePipeline --type=[pipelineType] --mono-repo=[true | false]
gradle gpl --type=[pipelineType] --mono-repo=[true | false]
```

| pipelineType | Nombre            |
|--------------|-------------------|
| `azure`      | Azure Pipeline    |
| `circleci`   | CircleCI Pipeline |
| `github`     | GitHub Action     |
| `jenkins`    | Jenkins Pipeline  |

## 15. Generate Acceptance Test — `generateAcceptanceTest | gat`

Genera un subproyecto con [Karate](https://github.com/intuit/karate) dentro de `./deployment/`.
Opcional: `--name` (default `acceptanceTest`).

```shell
gradle generateAcceptanceTest --name=[acceptanceTestProjectName]
gradle gat --name=[acceptanceTestProjectName]
```

> Karate combina automatización de pruebas de API, mocks, pruebas de performance y automatización UI en un único
> framework. Sintaxis BDD (estilo Cucumber) neutral al lenguaje; aserciones y reportes HTML integrados; ejecución
> paralela.

## 16. Generate Performance Test — `generatePerformanceTest | gpt`

Genera pruebas de performance en `./performance-test/`. Obligatorio: `--type`.

```shell
gradle generatePerformanceTest --type=[performanceType]
gradle gpt --type=[performanceType]
```

| performanceType | Nombre                  |
|-----------------|-------------------------|
| `jmeter`        | Jmeter Performance Test |

## 17. Validate Structure — `validateStructure | vs`

Valida que no se violen las referencias entre módulos, además de otras buenas prácticas verificadas en el archivo
`ArchitectureTest` generado en los tests unitarios de `app-service`.

```shell
gradle validateStructure
gradle vs
```

**Regla de dependencia (Robert C. Martin):** las dependencias de código fuente solo apuntan hacia adentro; nada en un
círculo interno puede conocer algo de un círculo externo.

Validaciones:
1. **Model**: sin ninguna dependencia.
2. **UseCase**: depende **únicamente** del módulo Model.
3. **Infraestructura**: permite cualquier dependencia externa; permite depender de Model y/o UseCase;
   **no** debe depender de AppService.

**Whitelist de dependencias** (p. ej. BOMs inyectados transversalmente que harían fallar las reglas 1 y 2):

```groovy
dependencies {
  implementation(platform("com.myorg:my-bom:0.0.1"))
}
```

Error típico:

```bash
Validating Model Module
 --- Dependency com.myorg:some-bom is not allowed in Model Layer
```

Solución en `build.gradle` (nombres separados por coma):

```groovy
cleanPlugin {
  modelProps {
     whitelistedDependencies = "my-bom, <dep2>, <depN..>"
  }
}
```

## 18. Delete Module — `deleteModule | dm`

Elimina un subproyecto. Obligatorio: `--module`.

```shell
gradle deleteModule --module=[name]
gradle dm --module=[name]
```

## 19. Update Project — `updateCleanArchitecture | u`

Actualiza el plugin y las dependencias en todos los subproyectos. También actualiza Spring, Lombok, Gradle y otras
dependencias según la versión del plugin; ocasionalmente modifica archivos estructurales del proyecto.

| Parámetro        | Descripción | Default |
|------------------|-------------|---------|
| `--dependencies` | Lista de dependencias a actualizar en formato `group:artifact` (p. ej. `co.com.bancolombia:cleanArchitecture`) | todas |
| `--git`          | Verificación de cambios sin commit en git; `--git false` la omite | verificación activa |

```shell
gradle updateCleanArchitecture --dependencies=[dependency1, dependency2, ...]
gradle u --dependencies=[dependency1, dependency2, ...]
gradle u --git false
```

> Recomendación oficial: **hacer commit antes de ejecutar** esta tarea.

## 20. Avanzado: ArchUnit Analysis

El scaffold aplica reglas ArchUnit predefinidas para reforzar restricciones de arquitectura.

| Regla | Tipo | Enunciado |
|-------|------|-----------|
| Rule_1.5 | Reactive Programming | Flujos reactivos deben usar clientes **async** de AWS SDK (p. ej. `kmsAsyncClient` en vez de `kmsClient`, con `Mono.fromFuture`) |
| Rule_2.2 | Clean Architecture | Clases de dominio no deben tener **sufijos técnicos** |
| Rule_2.4 | Clean Architecture | Clases de dominio (entidades, gateways, use cases) no deben tener **nombres de tecnología** |
| Rule_2.7 (campos) | Clean Architecture | Campos de modelos/use cases no deben tener nombres de tecnología |
| Rule_2.5 | Concurrency Safe Code | Use cases solo con atributos `final` |
| Rule_2.7 (beans) | Concurrency Safe Code | Beans solo con atributos `final` (inyección por constructor) |

### Rule_2.2 — sufijos prohibidos

```properties
arch.unit.forbiddenDomainSuffixes=dto,request,response
```

Insensible a mayúsculas (`dto` = `Dto` = `DTO`).

```java
// ❌ package co.com.bancolombia.model.userrequest; public class UserRequest { ... }
// ✅ package co.com.bancolombia.model.user;        public class User { ... }
```

### Rule_2.4 — nombres de tecnología prohibidos

```properties
arch.unit.forbiddenDomainClassNames=rabbit,sqs,sns,ibm,dynamo,aws,mysql,postgres,redis,mongo,rsocket,r2dbc,http,kms,s3,graphql,kafka
```

Insensible a mayúsculas. Ej.: `DynamoUserGateway` ❌ → `UserGateway` ✅; `RabbitMessage` ❌ → `Message` ✅.

### Rule_2.7 (campos) — misma lista que Rule_2.4

```java
// ❌ private String rabbitContentType;
// ✅ private String contentType;
```

### Rule_2.5 — use cases inmutables

```java
// ❌
@RequiredArgsConstructor
public class NotifyUsersUseCase {
    private NotificationGateway notifier; // No Compliant
    private User user;                    // No Compliant (estado compartido)
}

// ✅
@RequiredArgsConstructor
public class NotifyUsersUseCase {
    private final NotificationGateway notifier;
    public void notify(User user) { sendMessage(user); }
    private void sendMessage(User user) { notifier.send("notification", user.getEmail()); }
}
```

### Rule_2.7 (beans) — inyección por constructor en lugar de `@Value` en campo

```java
// ❌
@Component
public class MyService {
    @Value("${external-service.endpoint}")
    private String endpoint;
}

// ✅
@Component
public class MyService {
    private final String endpoint;
    public MyService(@Value("${external-service.endpoint}") String endpoint) {
        this.endpoint = endpoint;
    }
}
```

### Omitir reglas (no recomendado)

En `gradle.properties`:

```properties
package=co.com.bancolombia
systemProp.version=3.20.15
reactive=true
lombok=true
metrics=true
language=java
org.gradle.parallel=true
systemProp.sonar.gradle.skipCompile=true
arch.unit.skip=true
```

## 21. Avanzado: Dependency Updater (`internalTask | it`)

Permite usar el plugin como actualizador de dependencias de cualquier proyecto Java (no es `updateCleanArchitecture`).

1. Agregar el plugin al `build.gradle` (ver §5).
2. En `gradle.properties` (como en [commons-jms](https://github.com/bancolombia/commons-jms/blob/main/gradle.properties)):
   ```properties
   onlyUpdater=true
   ```
3. Ejecutar:
   ```bash
   ./gradlew it --action UPDATE_DEPENDENCIES
   ```

Actualiza dependencias Gradle y versiones de plugins Gradle. Valores de `--action` en el código:
`UPDATE_DEPENDENCIES`, `SONAR_CHECK`.

## 22. Avanzado: Optimización con Gradle Cache

### Ciclo de vida de build de Gradle

1. **Initialization**: detecta `settings.gradle(.kts)`, crea `Settings`, determina proyectos del build y crea un
   `Project` por cada uno.
2. **Configuration**: evalúa los `build.gradle(.kts)` y crea el grafo de tareas.
3. **Execution**: programa y ejecuta tareas (orden por dependencias, posible paralelismo).

### Tipos de caché

| Caché | Fase que optimiza | Mecanismo |
|-------|-------------------|-----------|
| **Build Cache** | Execution | Reutiliza outputs de tareas cuyos inputs no cambiaron; local o remoto (HTTP) |
| **Configuration Cache** | Configuration | Reutiliza el grafo de tareas y la configuración; salta la fase de configuración |

**Build Cache** — ventajas: menos tiempo (evita recompilar/re-testear), colaboración (caché remoto compartido con CI),
implementación simple.

```properties
org.gradle.caching=true
```
```bash
./gradlew build --build-cache
```

**Configuration Cache** — modo de ejecución preferido desde **Gradle 9.0**. Ventajas: omite configuración, ejecución
paralela de tareas por defecto, liberación de memoria de configuración.

```properties
org.gradle.configuration-cache=true
org.gradle.configuration-cache.problems=warn          # tratar incompatibilidades como warnings (migración)
org.gradle.configuration-cache.parallel=true          # incubating; síntoma de incompatibilidad: ConcurrentModificationException
org.gradle.configuration-cache.integrity-check=true   # Gradle 8.14+; solo para diagnóstico (penaliza rendimiento)
org.gradle.configuration-cache.read-only=true         # Gradle 9.1.0+; usa caché solo en hit, útil en CI efímero
```

### Configuración por defecto en proyectos del scaffold

`gradle.properties` generado:

```properties
org.gradle.caching=true
org.gradle.parallel=true
org.gradle.configuration-cache=true
org.gradle.configuration-cache.parallel=true
org.gradle.configuration-cache.integrity-check=false
org.gradle.configuration-cache.read-only=false
```

Caché local **específico del proyecto** en `settings.gradle` (no usa `GRADLE_USER_HOME`):

```groovy
buildCache {
    local {
        directory = new File(rootDir, 'build-cache')
    }
}
```

Ventajas: **aislamiento**, **portabilidad** (se mueve con el proyecto) y **limpieza** (borrar `build-cache/`).

### Benchmark oficial (`./gradlew clean jacocoMergedReport`, Mac M3 Pro, 16 GB)

| Escenario | Resultado |
|-----------|-----------|
| Primera compilación (descarga de dependencias) | 39 tareas, 33 ejecutadas, 6 UP-TO-DATE — ~114 s (1 min 54 s) |
| Sin build cache, dependencias ya en caché | ~35.4–35.5 s |
| Con todas las cachés | 23 FROM-CACHE, 16 ejecutadas — ~4.5–4.8 s |

Reducción aproximada de **87%** frente al build sin caché. Ejecuciones posteriores sin cambios quedan `UP-TO-DATE`
casi instantáneamente.

## 23. Contributing: extender el plugin

Aplica cuando la skill deba **modificar el propio plugin** (nuevos tipos de adapter/entry point), no para usarlo.

### 23.1 Flujo

1. **Fork** y clonar:
   ```bash
   git clone git@github.com:username/scaffold-clean-architecture.git
   cd scaffold-clean-architecture
   git remote add upstream https://github.com/bancolombia/scaffold-clean-architecture.git
   git fetch upstream
   git config user.name "My name"
   git config user.email "my personal or business email"
   ```
2. **Hook** pre-commit (formatea y ejecuta tests): `./gradlew installGitHooks`. Formatear manualmente:
   `./gradlew spotlessApply`.
3. **Branch** desde master: `git checkout -b my-branch -t upstream/master` (nombres con guiones, concisos; PR
   contra `master`).
4. Implementar cambios (ver §23.4).

### 23.2 Commits

- **Conventional Commits** obligatorio.
- Modo imperativo ("Fix", "Add", "Change").
- Resumen ≤ 50 caracteres (máximo 72).
- Todo en minúsculas salvo nombres propios, acrónimos y referencias a código.
- Segunda línea en blanco.
- Breaking changes (semver-major): explicar razón, cuándo se dispara y el cambio exacto.
- El cuerpo explica *qué* y *por qué*, no *cómo*.

```text
test: add functional test for non-standard base libraries
ci: support for Ubuntu 18 & CentOS 7
deps: upgrade express to 4.17.1
```

### 23.3 Criterios de Pull Request

- Referenciar el issue; incluir tests; documentar features nuevas en `/docs`.
- Historia limpia (rebase/squash): cada commit cambia una sola cosa.
- ⚠️ Release continuo: cada PR fusionado se publica automáticamente → revisión exhaustiva.
- **UpgradeAction obligatorio** (desde 2.3.0) si se modifica cualquier archivo estructural (`main.gradle`,
  `build.gradle`, `applications/app-service/build.gradle`, `gradle.properties`, etc.); si falta, **el PR se rechaza**.
  - Paquete: `co.com.bancolombia.factory.upgrades.actions`.
  - Nombre: `UpgradeY{year}M{month}D{day}{DescriptiveName}` — ej. `UpgradeY2024M01D19SonarSkipCompile`.
  - Permite que proyectos antiguos reciban los cambios con `gradle updateCleanArchitecture`.
- **Nuevas tareas**: extender `AbstractCleanArchitectureDefaultTask` o `AbstractResolvableTypeTask` y anotar con
  `@CATask` (name, description, shortcut).
- **Convención de parámetros**: multi-palabra con guiones (`--server-name`, `--module-type`, `--base-package`);
  una palabra sin guiones (`--type`, `--name`, `--package`).
- **Module factories**: prefijo del tipo en el nombre (p. ej. `DrivenAdapterR2DBC` → tipo inferido `R2DBC`).

| Tipo           | Paquete de la factory |
|----------------|-----------------------|
| DrivenAdapter  | `co.com.bancolombia.factory.adapters` |
| EntryPoint     | `co.com.bancolombia.factory.entrypoints` |
| AcceptanceTest | `co.com.bancolombia.factory.tests.acceptance` |
| PerformaceTest | `co.com.bancolombia.factory.tests.performance` |
| Helper         | `co.com.bancolombia.factory.helpers` |
| Pipeline       | `co.com.bancolombia.factory.pipelines` |

### 23.4 Implementar o modificar un módulo

**Templating con Mustache** (en `resources`). Variables que impactan las plantillas:
- `lombok` (default `true`): si se usan anotaciones Lombok, implementar también versión vanilla.
- `metrics` (default `true`): generar métricas solo si está activo.
- `reactive` (default `false` en plantillas): determina el directorio `<module-name>` (imperativo) o
  `<module-name>-reactive`.

Variables predefinidas: `projectName`, `projectNameLower`, `package` (ej. `co.com.bancolombia.sample`),
`packagePath` (ej. `co/com/bancolombia/sample`) y todas las constantes de `Constants` (ej. `PLUGIN_VERSION`).

**Paso 1 — Plantillas:**

| Tipo de módulo  | Ruta de recursos |
|-----------------|------------------|
| Driven Adapter  | `resources/driven-adapter/<module-name>(-reactive)` |
| Entry Point     | `resources/entry-point/<module-name>(-reactive)` |
| Helper          | `resources/helper/<module-name>(-reactive)` |
| Pipeline        | `resources/pipeline/<module-name>` |
| Test            | `resources/test/<module-name>` |

Convención de nombres de plantilla: minúsculas con guiones (`mongo-repository-adapter.java.mustache`); tests con
`.test` antes de la extensión (`commands-handler.test.java.mustache`); subdirectorios para agrupar
(`mongo-repository/config/mongo-config.java.mustache`).

**Paso 2 — ModuleFactory:**

```java
public interface ModuleFactory {
    void buildModule(ModuleBuilder builder) throws IOException, CleanException;
}
```

Operaciones comunes de `ModuleBuilder`:

| Método | Uso |
|--------|-----|
| `setupFromTemplate(String resourceGroup)` | Carga `definition.json` con `folders` (directorios a crear) y `files` (mapa plantilla → ruta destino, admite `{{language}}`, `{{packagePath}}`) |
| `appendToSettings(String module, String baseDir)` | Agrega el módulo a `settings.gradle` |
| `appendDependencyToModule(String module, String dependency)` | Agrega dependencia a un módulo (usar `Utils.buildImplementationFromProject(builder.isKotlin(), ":dynamodb")`) |
| `appendToProperties(String path)` | Obtiene/crea un `ObjectNode` en `application.yaml` |

```json
{
  "folders": ["infrastructure/driven-adapters/dynamo-db/src/test/{{language}}/{{packagePath}}/dynamodb/helper"],
  "files": {
    "driven-adapter/dynamo-db/build.gradle.mustache": "infrastructure/driven-adapters/dynamo-db/build.gradle"
  }
}
```

```java
String dependency = Utils.buildImplementationFromProject(builder.isKotlin(), ":dynamodb");
builder.appendDependencyToModule(APP_SERVICE, dependency);

builder.appendToProperties("spring.datasource")
       .put("url", "jdbc:h2:mem:test")
       .put("driverClassName", "org.h2.Driver");
```

**Paso 3 — Registrar el tipo en el enum:**

| Tipo | Enum |
|------|------|
| Driven Adapter | `co.com.bancolombia.factory.adapters.ModuleFactoryDrivenAdapter.DrivenAdapterType` |
| Entry Point    | `co.com.bancolombia.factory.entrypoints.ModuleFactory.EntryPoint` |
| Helper         | `co.com.bancolombia.factory.helpers.ModuleFactoryHelpers.EntryPointType` |
| Pipeline       | `co.com.bancolombia.factory.pipelines.ModuleFactoryPipeline.PipelineType` |
| Test           | `co.com.bancolombia.factory.tests.ModuleFactoryTests` |

**Paso 4 — Bloque de instanciación** en la factory class correspondiente (`ModuleFactoryDrivenAdapter`,
`entrypoints.ModuleFactory`, `ModuleFactoryHelpers`, `ModuleFactoryPipeline`, `ModuleFactoryTests`).

**Paso 5 — Nuevos parámetros (opcional):**

```java
@Option(option = "name", description = "Set driven adapter name when GENERIC type")
public void setName(String name) { this.name = name; }

builder.addParam("task-param-name", name);   // registrar
builder.getParam("task-param-name");         // consumir en código o plantilla
```

**Modificar un módulo existente:** modificar plantillas y la module factory correspondiente siguiendo lo anterior.

### 23.5 Probar localmente

1. Hacer los cambios.
2. Cambiar versión en `gradle.properties`: `systemProp.version=2.4.1.1`.
3. Publicar: `gradle publishToMavenLocal`.
4. Generar un proyecto con el plugin local:

**Opción A — `build.gradle`:**

```groovy
buildscript {
    repositories { mavenLocal(); mavenCentral() }
    dependencies { classpath "co.com.bancolombia.cleanArchitecture:scaffold-clean-architecture:2.4.1.1" }
}
apply plugin: "co.com.bancolombia.cleanArchitecture"
```

**Opción B — `settings.gradle` + `build.gradle`:**

```groovy
// build.gradle
plugins { id "co.com.bancolombia.cleanArchitecture" version "2.4.1.1" }
// settings.gradle (al inicio del archivo)
pluginManagement { repositories { mavenLocal(); gradlePluginPortal() } }
```

Luego ejecutar `gradle ca` con los argumentos deseados. Tras `ca`, volver a ajustar `build.gradle`/`settings.gradle`
con la sintaxis local, ya que la tarea los sobrescribe.

## 24. Opciones presentes en el código no documentadas en el sitio

Verificadas en `src/main/java/co/com/bancolombia/task` (rama master, versión 4.7.0). Usar con precaución y confirmar
con `gradle help --task <tarea>` en la versión del usuario.

| Tarea | Opción | Descripción en el código | Default |
|-------|--------|--------------------------|---------|
| `ca` | `--force` | "Force regenerates all files" | `false` |
| `ca` | `--example` | "Generate locally for example" | `false` |
| `it` | `--action SONAR_CHECK` | Acción interna adicional | — |

Versiones de referencia en `Constants.java` (master): plugin `4.7.0`, Spring Boot `4.1.1`, Lombok `1.18.48`,
Gradle wrapper `9.8.0`. La documentación publicada aún referencia el plugin `4.6.3`.

## 25. Erratas detectadas en la documentación oficial

- En "Getting Started", el enlace a *Generate Helper* apunta a `tasks/generate-entry-point`.
- En ArchUnit, el texto dice `arch.unit.ski=true`; la propiedad correcta (como en el ejemplo) es `arch.unit.skip=true`.
- La numeración `Rule_2.7` se repite para dos reglas distintas (campos con nombres de tecnología y beans con
  atributos `final`).
- Errores tipográficos menores: `entry-poits`, `shoud`, `aproach`, `PerformaceTest`.
- El ejemplo de "Generate Project" muestra `--type=reactive` y la tabla dice `imperative or reactive`.

## 26. Guía rápida de decisión para la skill

> Sección de apoyo derivada de la referencia anterior (no forma parte del sitio oficial).

| Necesidad del usuario | Comando |
|-----------------------|---------|
| Nuevo microservicio reactivo | `./gradlew ca --package=<pkg> --type=reactive --name=<Nombre> --java-version=<17\|21\|25>` |
| Nuevo microservicio imperativo | `./gradlew ca --package=<pkg> --type=imperative --name=<Nombre>` |
| Entidad de dominio + puerto | `./gradlew gm --name=<Entidad>` |
| Caso de uso | `./gradlew guc --name=<Accion>` |
| API REST reactiva | `./gradlew gep --type=webflux [--router] [--authorization] [--versioning] [--swagger]` |
| API REST imperativa | `./gradlew gep --type=restmvc [--server=tomcat\|jetty]` |
| API contract-first | `./gradlew gep --type=webflux\|restmvc --from-swagger=<archivo>` |
| Consumir REST externo | `./gradlew gda --type=restconsumer --url=<url>` o `--from-swagger=<archivo>` |
| Base relacional (imperativo) | `./gradlew gda --type=jpa [--secret=true]` |
| PostgreSQL reactivo | `./gradlew gda --type=r2dbc` |
| MongoDB / DynamoDB / Redis | `gda --type=mongodb` / `dynamodb` / `redis [--mode]` |
| Publicar eventos (Reactive Commons) | `./gradlew gda --type=asynceventbus [--eda] [--tech]` |
| Escuchar eventos (Reactive Commons) | `./gradlew gep --type=asynceventhandler [--eda] [--tech]` |
| Kafka consumer simple / Strimzi | `gep --type=kafka` / `gep --type=kafkastrimzi --name --topic-consumer` |
| IBM MQ (JMS) enviar / escuchar | `gda --type=mq` / `gep --type=mq` |
| AWS SQS enviar / escuchar | `gda --type=sqs` / `gep --type=sqs` |
| AWS S3 / KMS / Cognito | `gda --type=s3` / `kms` / `cognitotokenprovider` |
| Secretos (AWS SM / Vault) | `./gradlew gda --type=secrets --secrets-backend=aws_secrets_manager\|vault` |
| GraphQL | `./gradlew gep --type=graphql [--pathgql]` |
| gRPC | `./gradlew gep --type=grpc` |
| RSocket server / client | `gep --type=rsocket` / `gda --type=rsocket` |
| Servidor MCP para IA | `./gradlew gep --type=mcp --name=<Nombre> [flags --enable-*]` |
| Agente IA A2A | `./gradlew gep --type=agent --name=<n> --agent-role=collaborative\|supervisor\|hybrid` |
| Módulo vacío personalizado | `gda --type=generic --name=<n>` / `gep --type=generic --name=<n>` / `gh --name=<n>` |
| Pipeline CI | `./gradlew gpl --type=azure\|circleci\|github\|jenkins [--mono-repo=true]` |
| Pruebas de aceptación / performance | `./gradlew gat [--name]` / `./gradlew gpt --type=jmeter` |
| Validar arquitectura | `./gradlew vs` (y tests `ArchitectureTest` en app-service) |
| Actualizar proyecto | commit previo → `./gradlew u [--dependencies=...]` |
| Eliminar módulo | `./gradlew dm --module=<nombre>` |

Las prácticas de código dentro de esta estructura (inyección, errores, JPA,
transacciones, Reactor, pruebas) están en el
[perfil Java/Spring](stacks/java-spring/spring-profile.md).

**Reglas que la skill debe respetar al generar código dentro del scaffold:**

1. Nunca hacer que `model` dependa de algo, ni que `usecase` dependa de algo distinto de `model`.
2. Nunca hacer que un módulo de infraestructura dependa de `app-service`.
3. Nombres de dominio sin sufijos `Dto/Request/Response` ni tecnologías (`rabbit, sqs, sns, ibm, dynamo, aws, mysql,
   postgres, redis, mongo, rsocket, r2dbc, http, kms, s3, graphql, kafka`) — ni en clases ni en campos.
4. Use cases y beans: atributos `final`, inyección por constructor; `@Value` solo en parámetros del constructor.
5. En proyectos reactivos: retornar `Mono`/`Flux`, no bloquear y usar clientes AWS `*AsyncClient` con `Mono.fromFuture`.
6. Puertos en `model/.../gateways`; implementaciones en `driven-adapters`; el ensamblaje lo hace `app-service`.
7. Advertir que `ca` sobrescribe `main.gradle`, `build.gradle` y `gradle.properties` en proyectos existentes, y que
   `u` debe ejecutarse tras hacer commit.
8. Para `mcp`, desactivar `--enable-security` solo en desarrollo.
