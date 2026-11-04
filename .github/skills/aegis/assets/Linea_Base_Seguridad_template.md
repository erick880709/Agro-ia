---
name: linea-base-seguridad-<proyecto>
proyecto: <Proyecto>
actualizado: <AAAA-MM-DD>
fuente_19_1: <ruta a 19.1 de archi o "no existe">
---

# Línea base de seguridad — <Proyecto>

## Datos y clasificación
- Datos tratados: <PII, financieros, credenciales, PAN, salud…>
- Clasificación y dueño: <…>
- Ambientes con datos reales: <solo prod | …>

## Regulación y marcos aplicables
- <PCI DSS v4.0.1 sí/no — alcance> · <SFC CE 007/2018> · <Ley 1581/2012> · <ISO 27001:2022> · <otro>
- Confirmado por: <área/persona>

## Exposición e identidad
- Exposición: <Internet | interna | B2B | terceros>
- IdP y tokens: <Azure External ID / Entra / Cognito…>, <JWT bearer | cookie BFF>, multi-tenant: <sí/no>
- Validaciones obligatorias del token: <iss, aud, exp, tid, scp/roles>

## Stacks y arquitectura
- Stacks: <Java 21 + Spring Boot 3.x WebFlux (Scaffold) | Go 1.2x | Angular 1x | Terragrunt 1.x>
- Nube y cuentas: <AWS org / Azure suscripciones / GCP proyectos>

## Herramientas existentes
- SAST: <Sonar | Checkmarx | Semgrep | ninguna> · SCA: <…> · Secretos: <…> · IaC: <…> · DAST: <…>
- Dueño del pipeline DevSecOps: <Vulcano | equipo X>

## Riesgos aceptados y excepciones
| ID | Descripción | Autoridad | Compensación | Revisión |
|---|---|---|---|---|

## Decisiones de seguridad del proyecto
- <p. ej. "tokens solo en memoria en el SPA; refresh en cookie HttpOnly del BFF">
