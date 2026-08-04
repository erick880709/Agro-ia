# RF-002: Gestión de Usuarios

**Tipo:** Requerimiento funcional
**Fuente:** RFP-AgroInteligente-Colombia.md — Sección 5.2; RFP-inicial.md — Sección 3 (Gestión de usuarios)
**Prioridad:** Alta

## Descripción
El sistema debe permitir la gestión completa del ciclo de vida de usuarios, incluyendo: registro de nuevos usuarios, inicio de sesión, recuperación de contraseña, cambio de contraseña y gestión del perfil de usuario. Cada usuario debe poder actualizar su información personal desde su perfil.

## Actores involucrados
- Agricultor (Cliente)
- Técnico Agrónomo
- Investigador IES
- Administrador

## Criterios de aceptación
- Registro con validación de correo electrónico.
- Inicio de sesión con credenciales (usuario/contraseña).
- Flujo de recuperación de contraseña por correo electrónico.
- Cambio de contraseña autenticado.
- Edición de datos de perfil (nombre, contacto, región).
- No especificados en el RFP — definir políticas de complejidad de contraseña, expiración de sesión, y si se requiere 2FA.

## Dependencias / relacionados
- RF-003: Roles y permisos
- RF-004: Aislamiento de datos entre clientes
- RNF-004: Seguridad — autenticación/autorización (JWT, OAuth2)

## Notas del analista
- El RFP menciona inicialmente solo roles Administrador y Cliente, pero el modelo de actores ampliado del documento consolidado incluye también Técnico Agrónomo e Investigador IES. Se asume el modelo ampliado de 4 roles.
- No se especifica si el registro será abierto (self-service) o por invitación/activación administrativa. Se recomienda definir con el cliente.
- No se menciona integración con redes sociales o identidad federada (Google, Microsoft). Se asume solo autenticación local.
