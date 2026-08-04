# RNF-004: Seguridad — Autenticación y Autorización

**Tipo:** Requerimiento no funcional
**Categoría:** Seguridad
**Fuente:** RFP-AgroInteligente-Colombia.md — Sección 6.3

## Descripción
El sistema debe implementar mecanismos robustos de autenticación y autorización:

- **Autenticación:** basada en JWT (JSON Web Tokens) con soporte para OAuth2.
- **Autorización:** control de acceso basado en roles (RBAC) con verificación en cada endpoint de API.
- Todas las comunicaciones cliente-servidor deben estar cifradas mediante HTTPS/TLS.
- La información sensible debe cifrarse en reposo (datos personales de agricultores, credenciales, información financiera).
- Gestión segura de credenciales y secretos (uso de vault o servicio de gestión de secretos del cloud provider).

## Criterio medible / restricción concreta
- TLS 1.2 o superior para todas las comunicaciones HTTP.
- Algoritmo de firma JWT: RS256 o superior (clave asimétrica).
- Rotación periódica de secretos y claves de API.
- No especificados en el RFP — definir: tiempo de expiración del token JWT, política de refresh tokens, algoritmo de hashing de contraseñas (bcrypt/argon2).

## Impacto en la arquitectura
- API Gateway como punto central de autenticación/autorización.
- Microservicios con validación de token JWT en cada petición.
- Vault (HashiCorp Vault o AWS Secrets Manager) para gestión de secretos.
- Base de datos con cifrado en reposo (TDE o equivalente).
- Network Policy en Kubernetes para aislar servicios por nivel de sensibilidad.

## Notas del analista
- JWT + OAuth2 es un estándar de industria adecuado para arquitecturas de microservicios.
- La mención de "redes privadas virtuales (VPC)" en el RFP sugiere despliegue en AWS con VPC y subnets privadas para componentes críticos (bases de datos, workers de ML).
- El RFP no menciona explícitamente cumplimiento de normas como ISO 27001 o SOC2. Para el mercado colombiano, la referencia principal es la Ley 1581 de 2012 (protección de datos personales).
