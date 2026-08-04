# RF-017: Administración de la Plataforma

**Tipo:** Requerimiento funcional
**Fuente:** RFP-AgroInteligente-Colombia.md — Sección 5.15
**Prioridad:** Media

## Descripción
El administrador del sistema debe contar con un panel de administración que le permita gestionar todos los recursos de la plataforma:

- **Usuarios:** crear, editar, desactivar, cambiar rol, restablecer contraseñas.
- **Membresías:** definir y configurar planes (precios, límites de fincas/análisis, funcionalidades incluidas), activar/desactivar membresías de clientes.
- **Cultivos:** gestionar el catálogo de cultivos (crear, editar, desactivar fichas técnicas).
- **Reglas agronómicas:** configurar y mantener las reglas del motor de conocimiento (umbrales, compatibilidades, recomendaciones).
- **Sensores:** registrar, configurar y monitorear el estado de los sensores IoT.
- **Modelos de IA:** visualizar versiones de modelos, métricas de rendimiento, activar/desactivar modelos, iniciar reentrenamiento.
- **Estadísticas generales:** número de usuarios, fincas registradas, análisis realizados, membresías activas, uso de infraestructura, ingresos estimados.

## Actores involucrados
- Administrador

## Criterios de aceptación
- El panel de administración es accesible solo para usuarios con rol Administrador.
- Cada sección del panel permite operaciones CRUD sobre el recurso correspondiente.
- Las estadísticas se actualizan en tiempo real o con un retraso máximo de 1 hora.
- No especificados en el RFP — definir: ¿auditoría de acciones del administrador?, ¿panel de administración responsive o solo desktop?, ¿notificaciones al administrador (ej. sensor offline, modelo degradado)?

## Dependencias / relacionados
- RF-002: Gestión de usuarios
- RF-003: Roles y permisos
- RF-005: Gestión de membresías
- RF-009: Catálogo de cultivos
- RF-010: Motor de conocimiento agronómico

## Notas del analista
- El panel de administración es un frontend adicional que debe construirse en Angular 21, con acceso restringido por rol.
- Se recomienda implementar auditoría de acciones administrativas (quién hizo qué y cuándo) desde el inicio, ya que es un requisito de seguridad mencionado en la sección 6.3 del RFP.
