# Modelo de Datos — AgroIA

> Generado por `genesis` a partir de `Documento_Arquitectura_AgroIA.md`.
> `builder` agregará entidades incrementalmente al generar cada recurso de dominio.
> No regenerar desde cero — solo añadir nuevas entidades.

## Convenciones

- **ID:** UUID v4 en todas las entidades
- **Timestamps:** `created_at`, `updated_at` en todas las tablas
- **Multi-tenancy:** `tenant_id` (UUID) en todas las tablas con datos de cliente
- **Soft delete:** `deleted_at` (timestamp nullable) para eliminaciones lógicas
- **Schemas:** `agroia` para datos de aplicación, `mlflow` para MLflow

## Entidades base (plomería)

### Usuario
| Campo | Tipo | Descripción |
|-------|------|-------------|
| id | UUID PK | Identificador único |
| email | String UNIQUE | Correo electrónico |
| password_hash | String | Hash bcrypt/argon2 |
| nombre | String | Nombre completo |
| rol | Enum(Admin/Cliente/Tecnico/Investigador) | Rol RBAC |
| tenant_id | UUID | Tenant (para clientes; null para admin/técnico) |
| consentimiento_datos | Boolean | Consentimiento Ley 1581 |
| created_at | Timestamp | Fecha de registro |

### Finca
| Campo | Tipo | Descripción |
|-------|------|-------------|
| id | UUID PK | Identificador único |
| usuario_id | UUID FK → Usuario | Dueño |
| tenant_id | UUID | Tenant |
| nombre | String | Nombre de la finca |
| ubicacion | Geometry(Point, 4326) | PostGIS |
| area_ha | Float | Área en hectáreas |
| created_at | Timestamp | Fecha de registro |

> **Nota:** Las entidades de dominio (Recomendacion, Cultivo, FichaTecnica, Discordancia, ReglaAgronomica, SensorReading, Membresia) serán agregadas por `builder` al generar los módulos correspondientes.
