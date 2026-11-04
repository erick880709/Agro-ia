# Plomería base de aplicación

La baseline debe arrancar y demostrar sus límites antes del primer módulo de negocio. Genera estas piezas mediante el arquetipo/adaptador, una vez por componente, y clasifica su ownership.

## Piezas transversales

1. Configuración tipada y validada al arranque, más `.env.example` sin secretos.
2. Bootstrap/composition root que ensambla configuración, logging, errores, routers/handlers y adapters.
3. Manejo centralizado de errores sin filtrar stack traces o datos sensibles.
4. Logging estructurado con correlación y nivel por ambiente.
5. Health/liveness de la aplicación; readiness solo comprueba dependencias diseñadas y controlables.
6. Telemetría de aplicación desacoplada del backend operacional elegido por Vulcano.
7. Prueba observable del camino mínimo.
8. README de desarrollo local y comandos reales.

No conectes bases de datos, brokers o proveedores solo porque son comunes. Inicialízalos únicamente cuando la arquitectura y los contratos de aplicación los requieran.

## API o integrations service

- Router/host raíz, configuración, error mapping, auth boundary y correlación.
- Endpoints de health/liveness; readiness con timeouts y sin revelar detalles sensibles.
- Modelos/clients generados desde contrato congelado cuando aplique.
- Puerto/adaptador de persistencia configurado sin entidades inventadas.
- Pruebas de arranque, health, error y contrato mínimo.

### Hexagonal/Clean

```text
domain/          sin dependencias de framework ni entidades inventadas
application/     puertos y servicios transversales mínimos
adapters/in/     host/router y health
adapters/out/    configuración de dependencias aprobadas
bootstrap/       composition root
```

### Layered/MVC

```text
controllers/     health/error boundary
services/        servicios transversales mínimos
repositories/    solo interfaces/configuración requerida
configuration/   bootstrap y wiring
```

### Modular o vertical slice

```text
app/root         módulo/host raíz
features/health  slice inicial observable
shared           errores, configuración, logging y contratos
```

CQRS no debe enrutar health a través del command bus; health verifica el host y dependencias directamente.

## Web

- App shell y providers globales mínimos.
- Error boundary y fallback de navegación.
- Router con rutas estructurales aprobadas, sin inventar features.
- Cliente tipado/adapter HTTP desde contrato si existe.
- Auth boundary sin credenciales ni proveedor ficticio.
- Sistema de diseño aprobado consumido desde tokens, catálogo y assets congelados del proyecto (capability `design-system`), sin valores de marca fijados en la plantilla; accesibilidad base y mocks de desarrollo cuando correspondan.
- Prueba de render y un vertical slice no destructivo.

## Worker

- Bootstrap, configuración y logging.
- Dispatcher tipado por versión de mensaje.
- Idempotencia, retry y dead-letter como comportamiento de aplicación cuando estén diseñados.
- Apagado seguro y comando/probe de health apropiado.
- Prueba de dispatch sin broker real cuando exista stub aprobado.

## Agent service

- Frontera de proveedor de modelos.
- Registry de tools tipadas y sin efectos reales por defecto.
- Timeouts, límites, retry/circuit breaker según arquitectura.
- Confirmación humana para acciones sensibles.
- Memoria/persistencia solo si ownership y privacidad están definidos.
- Eval harness mínimo y prueba del flujo sin secretos.

## Persistencia y migraciones

Si están diseñadas, configura el ORM/driver, conexión y estructura de migraciones sin crear modelos de negocio ficticios. Health no debe bloquear por una dependencia que la arquitectura clasifica como opcional; readiness sí puede reflejarla con semántica explícita.

## Exclusiones

Esta plomería no incluye Dockerfile, Compose, pipelines, IaC, Helm, Kubernetes, despliegue, dashboards o alertas productivas. Entrega a Vulcano runtimes, puertos, health endpoints, dependencias y variables requeridas.

