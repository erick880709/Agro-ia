---
name: linea-base-datos-<proyecto>
proyecto: <Proyecto>
actualizado: <AAAA-MM-DD>
fuentes: [16-Modelo-de-Datos.md, 17-Vista-de-Despliegue.md, repositorio]
---

# Línea base de datos — <Proyecto>

## Motores por ambiente
| Componente (CT-xx) | Motor | Versión | Modalidad | Dev | QA | Prod |
|---|---|---|---|---|---|---|

## Volumen y carga
| Tabla/colección | Filas/ítems hoy | Crecimiento | Pico QPS/TPS | Fuente |
|---|---|---|---|---|

## Continuidad
- RPO / RTO: <…> · PITR: <días> · Réplicas / multi-AZ / región: <…>
- Pruebas de restauración: <frecuencia, último resultado>

## Desarrollo
- Migraciones: <Flyway | Liquibase | golang-migrate | …>, ubicación <…>, reglas (sin edición de aplicadas, scripts no transaccionales)
- Acceso: <JPA | R2DBC | pgx | sqlc | Enhanced Client | Spring Data Mongo>, pool <Hikari/r2dbc-pool: tamaño>
- Pruebas con base real: <Testcontainers | LocalStack | …>

## Clasificación y retención
| DATA-xxx | Clasificación | Retención | Borrado/anonimización |
|---|---|---|---|

## Operación
- Ventanas de mantenimiento: <…> · Tolerancia a bloqueos: <N s> · Monitoreo: <Performance Insights, Query Store…>

## Decisiones y excepciones
| ID | Decisión/excepción | Motivo | Autoridad | Revisión |
|---|---|---|---|---|
