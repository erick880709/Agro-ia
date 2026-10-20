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

## Módulo AGC-COST — catálogo de parámetros de costeo (F1, 2026-09-18)

Migración `045_costeo_parametros` · schema `agroia` · dinero en NUMERIC(18,4) (Decimal).
Auditoría en todas las tablas: `creado_por`/`creado_en`/`actualizado_por`/`actualizado_en`.

| Tabla | Propósito | Notas |
|-------|-----------|-------|
| `costeo_conjunto` | Conjunto versionado de parámetros | estados: borrador/en_revision/publicado/archivado; un solo publicado vigente por fecha |
| `costeo_servicio` | Servicio cotizable | unidad (punto/hectarea/dispositivo/dia/visita), requiere_lote, activo, orden; UNIQUE(conjunto_id, codigo) |
| `costeo_componente` | Componente de costo | tipo fijo/escalonado/por_unidad/por_distancia/por_jornada/porcentual/condicional; config JSONB; afectable_por_factores |
| `costeo_tramo` | Tramo escalonado (desde–hasta, valor, modo marginal/completo) | FK componente |
| `costeo_factor` | Escala de factor (dificultad, urgencia…) | aplicacion porcentual/multiplicativo; combinacion suma/multiplica |
| `costeo_factor_opcion` | Opción de factor con porcentaje | FK factor |
| `costeo_densidad` | Regla de densidad de muestreo por rango de área | opcional por cultivo |
| `costeo_zona` | Zona de desplazamiento (factor, km incluidos, tarifa km, peajes) | departamento + municipio opcional |
| `costeo_impuesto` | Impuesto/retención (base gravable, informativo) | informativo=true no suma al total |
| `costeo_politica` | Política comercial (márgenes, piso, redondeo, vigencia) | UNIQUE por conjunto |
| `costeo_descuento` | Regla de descuento/recargo con tope por rol | criterio, umbral, porcentaje, tope_rol JSONB |

## Módulo Voz — interacción por voz en el Asesor agronómico (2026-10-19)

Migración `047_voz` · schema `agroia` · RFP-AGROIA-001.

### ParametroVoz
Configuración global de la función de voz (una sola fila; se crea con valores por
defecto al primer acceso). Sin `tenant_id` (configuración global, no dato de cliente).

| Campo | Tipo | Descripción |
|-------|------|-------------|
| id | UUID PK | Identificador único |
| activado | Boolean | Activa/desactiva la función (default `true`) |
| duracion_maxima_segundos | Integer | Límite de duración por consulta (default `60`) |
| idioma | String(10) | Idioma de transcripción (default `es`) |
| created_at / updated_at | Timestamp | Auditoría |

### MetricaVoz
Agregado mensual de uso de voz (RF-036). Anónimo: sin referencia a usuarios, sin
audio ni contenido de consultas.

| Campo | Tipo | Descripción |
|-------|------|-------------|
| id | UUID PK | Identificador único |
| periodo | String(7) UNIQUE | Periodo de agregación `YYYY-MM` |
| consultas | Integer | Consultas enviadas por voz |
| errores | Integer | Errores de captura/transcripción |
| duracion_total_ms | BigInteger | Suma de duraciones (la media se calcula al leer) |
| created_at / updated_at | Timestamp | Auditoría |

> **Nota:** la transcripción en servidor no persiste entidad de audio — el audio se
> procesa en memoria y se descarta al terminar (RNF-019).

Próximas fases: `estimacion*` (F3), `cobro_*` (F5), `costeo_identidad*` (F4) — ver `resources/functional/hu/rfp-agc-cost.md`.
