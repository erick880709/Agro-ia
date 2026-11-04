# PLT-04 — Stack de reportes en non-prod

## Objetivo
Desplegar el servicio de reportes en `non-prod` (us-east-1) reutilizando los units `ejemplo` y `ejemplo-tabla` del catálogo.

## Criterios de aceptación
- AC-01: Nuevo stack `non-prod/us-east-1/reportes/terragrunt.stack.hcl` con los units del catálogo en la versión `v1.1.0` (la misma de non-prod).
- AC-02: El servicio depende de la tabla mediante `autoinclude` con mocks limitados a validate/plan/init.
- AC-03: Sin cambios en `prod`, `root.hcl` ni el pipeline.
