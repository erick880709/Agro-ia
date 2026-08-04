# RF-005: Gestión de Membresías

**Tipo:** Requerimiento funcional
**Fuente:** RFP-AgroInteligente-Colombia.md — Sección 5.3; RFP-inicial.md — Sección 3 (Gestión de Membresías)
**Prioridad:** Media

## Descripción
El sistema debe gestionar un modelo de suscripción por membresías que controle el acceso a funcionalidades según el plan contratado. Los tipos de membresía definidos son: Mensual, Semestral y Anual. Cada membresía debe definir límites sobre:

- Número máximo de fincas que el cliente puede registrar.
- Número máximo de análisis (consultas al motor predictivo) que puede realizar.
- Acceso al agente conversacional IA (sí/no).
- Acceso al historial de reportes generados.

La arquitectura debe estar preparada para integrar una pasarela de pagos en el futuro, aunque en el MVP la integración con pagos puede quedar simulada o pendiente.

## Actores involucrados
- Cliente (Agricultor) — consulta y adquiere membresías
- Administrador — define y configura los planes de membresía

## Criterios de aceptación
- El sistema restringe el acceso a funcionalidades según el plan activo del cliente.
- El sistema notifica al cliente cuando alcanza el límite de fincas o análisis de su plan.
- La arquitectura de pagos está definida y documentada, con endpoints preparados para integrar la pasarela.
- No especificados en el RFP — definir: precios de cada plan, ¿período de gracia al expirar?, ¿renovación automática?, ¿downgrade/upgrade entre planes?

## Dependencias / relacionados
- RF-002: Gestión de usuarios
- RF-006: Gestión de fincas
- RF-021: Integración con pasarela de pagos (futuro)

## Notas del analista
- El MVP debe implementar la lógica de límites y control de acceso por membresía, pero la integración real con pasarela de pagos se difiere a una fase posterior.
- Los valores concretos de cada plan (precio, límites numéricos) no están definidos en el RFP. Se recomienda definirlos con el cliente antes del desarrollo.
- No se menciona un plan gratuito o de prueba (freemium/trial). Evaluar si es necesario para la estrategia de adopción.
