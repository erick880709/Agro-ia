# RF-004: Aislamiento de Datos entre Clientes

**Tipo:** Requerimiento funcional
**Fuente:** RFP-AgroInteligente-Colombia.md — Sección 5.2 (Aislamiento estricto de datos); Sección 6.3 (Seguridad)
**Prioridad:** Alta (Crítica)

## Descripción
El sistema debe garantizar que cada cliente (agricultor) únicamente visualice y acceda a la información de sus propias fincas. Bajo ninguna circunstancia un cliente podrá visualizar información de otros clientes. Este aislamiento aplica a todos los recursos del sistema: análisis de suelo, reportes, fincas registradas, conversaciones con el agente IA, datos de sensores, histórico de mediciones y cualquier otro dato generado o almacenado por la plataforma.

## Actores involucrados
- Cliente (Agricultor) — sujeto al aislamiento
- Administrador — acceso global por rol

## Criterios de aceptación
- Verificación de que un cliente autenticado no puede acceder a datos de otro cliente mediante manipulación de IDs en URLs o parámetros de API.
- Prueba de penetración que confirme el aislamiento total.
- No especificados en el RFP — definir mecanismo concreto de multi-tenancy con el proveedor (row-level security vs. esquema por cliente vs. base de datos por cliente).

## Dependencias / relacionados
- RF-002: Gestión de usuarios
- RF-003: Roles y permisos
- RT-015: Multi-tenancy
- RNF-004: Seguridad — autenticación/autorización

## Notas del analista
- El RFP deja abierta la implementación concreta del multi-tenancy (row-level security vs. esquema por cliente). Esto es una decisión arquitectónica con impacto significativo en el modelo de datos, rendimiento y costo de infraestructura. Se recomienda row-level security en PostgreSQL como punto de partida para MVP, migrable a esquema por cliente si la escala lo exige.
- Este requisito es de prioridad crítica porque su incumplimiento implicaría exposición de datos personales y posible violación de la Ley 1581 de 2012 (habeas data) en Colombia.
