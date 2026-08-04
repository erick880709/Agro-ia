# RT-005: Base de Datos — PostgreSQL + PostGIS

**Tipo:** Requisito técnico
**Categoría:** Infraestructura / Persistencia
**Fuente:** RFP-AgroInteligente-Colombia.md — Sección 7.2

## Descripción
La plataforma debe utilizar **PostgreSQL** como base de datos relacional principal, con la extensión **PostGIS** para el manejo de datos geoespaciales.

**PostgreSQL** para:
- Datos transaccionales: usuarios, membresías, fincas, cultivos, reglas agronómicas.
- Datos de configuración: roles, permisos, catálogos.
- Relaciones entre entidades del dominio agronómico.

**PostGIS** para:
- Almacenamiento de coordenadas GPS de fincas (puntos y polígonos).
- Consultas geoespaciales (ej. encontrar todas las fincas en un radio de X km, calcular área).
- Integración con shapefiles del IGAC para datos edafológicos.

## Criterio medible / restricción concreta
- PostgreSQL 15+ con extensión PostGIS habilitada.
- Row-Level Security (RLS) para multi-tenancy si se elige ese enfoque.
- Conexiones manejadas con pool (PgBouncer o similar) para producción.
- Backups automatizados diarios con retención mínima de 30 días.
- No especificados en el RFP — definir: estrategia de multi-tenancy (ver RT-015), tamaño estimado de la base de datos, particionamiento de tablas de series temporales.

## Impacto en la arquitectura
- Un único clúster de PostgreSQL con réplicas de lectura para dashboards.
- PostGIS habilita consultas espaciales que serían imposibles o muy costosas en una base de datos no geoespacial.
- SQLAlchemy + GeoAlchemy2 como ORM con soporte geoespacial desde Python.
- Las series temporales de sensores pueden requerir particionamiento por tiempo o una base de datos complementaria (TimescaleDB, InfluxDB).

## Notas del analista
- PostgreSQL + PostGIS es el estándar de facto para aplicaciones que combinan datos transaccionales y geoespaciales.
- Para las series temporales de sensores IoT (millones de mediciones), se puede evaluar TimescaleDB (extensión de PostgreSQL) que ofrece compresión y consultas temporales optimizadas, manteniendo compatibilidad SQL.
- La decisión de multi-tenancy (RLS vs. esquema por cliente vs. base de datos por cliente) debe tomarse antes del diseño del modelo de datos. RLS es la opción más simple para empezar.
