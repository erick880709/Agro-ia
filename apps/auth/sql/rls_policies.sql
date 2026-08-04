"""SQL para políticas RLS (Row-Level Security) en PostgreSQL.

Ejecutar UNA vez después de crear las tablas para activar
el aislamiento multi-tenant a nivel de base de datos.
"""

RLS_POLICIES_SQL = """
-- ═══════════════════════════════════════════════════════════
-- ACTIVAR RLS en tablas con tenant_id
-- ═══════════════════════════════════════════════════════════

ALTER TABLE agroia.recomendaciones ENABLE ROW LEVEL SECURITY;
ALTER TABLE agroia.discordancias ENABLE ROW LEVEL SECURITY;

-- Política: el usuario solo ve sus propios datos (tenant_id)
CREATE POLICY tenant_isolation_recomendaciones ON agroia.recomendaciones
    FOR ALL
    USING (tenant_id = current_setting('app.current_tenant')::uuid)
    WITH CHECK (tenant_id = current_setting('app.current_tenant')::uuid);

CREATE POLICY tenant_isolation_discordancias ON agroia.discordancias
    FOR ALL
    USING (tenant_id = current_setting('app.current_tenant')::uuid)
    WITH CHECK (tenant_id = current_setting('app.current_tenant')::uuid);

-- Las tablas compartidas (cultivos, reglas, modelos_ml) NO tienen RLS
-- Son datos multi-tenant accesibles para todos los clientes.

-- ═══════════════════════════════════════════════════════════
-- Política de seguridad para datos personales
-- ═══════════════════════════════════════════════════════════

-- Forzar que SIEMPRE se configure el tenant (no puede ser null)
ALTER TABLE agroia.recomendaciones
    ALTER COLUMN tenant_id SET NOT NULL;

ALTER TABLE agroia.discordancias
    ALTER COLUMN tenant_id SET NOT NULL;

-- ═══════════════════════════════════════════════════════════
-- Función helper para testing (solo en dev)
-- ═══════════════════════════════════════════════════════════

CREATE OR REPLACE FUNCTION agroia.set_tenant(p_tenant_id uuid)
RETURNS void AS $$
BEGIN
    PERFORM set_config('app.current_tenant', p_tenant_id::text, false);
END;
$$ LANGUAGE plpgsql;
"""

print("✅ Políticas RLS listas para ejecutar.")
print("   Conectar a PostgreSQL y ejecutar:")
print("   psql -U agroia -d agroia -f apps/auth/sql/rls_policies.sql")
