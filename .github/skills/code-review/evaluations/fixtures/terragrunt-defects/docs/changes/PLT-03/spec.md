# PLT-03 — Base de datos de pagos en producción

## Objetivo
Agregar la base de datos Aurora PostgreSQL del servicio de pagos en la cuenta `prod` (us-east-1), consumiendo la red existente del stack `servicio-ejemplo`.

## Criterios de aceptación
- AC-01: La base de datos se declara como unit en `prod/us-east-1/pagos-db` usando el módulo `aurora-postgresql` del catálogo en una versión inmutable.
- AC-02: Las credenciales maestras no se almacenan en el repositorio; se leen de Secrets Manager o variables de entorno del pipeline.
- AC-03: El estado del unit queda aislado (clave propia) en el backend existente.
- AC-04: El pipeline de apply a producción sigue requiriendo aprobación del environment `prod`.
- AC-05: Se conserva compatibilidad con Terragrunt 1.x (sin comandos ni flags previos a 1.0).

## Restricciones
- No modificar la red existente.
