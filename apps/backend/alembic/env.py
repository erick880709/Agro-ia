"""Alembic environment configuration for AgroIA backend."""

from logging.config import fileConfig

from alembic import context
from sqlalchemy import engine_from_config, pool

# ── Importar todos los modelos para que Alembic los detecte ──
from agroia.database import Base
from agroia_backend.models.recomendacion import Recomendacion  # noqa: F401
from agroia_backend.models.discordancia import Discordancia  # noqa: F401
from agroia_backend.models.regla_agronomica import ReglaAgronomica  # noqa: F401
from agroia_backend.models.modelo_ml import ModeloML  # noqa: F401
from agroia_backend.models.metrica_modelo import MetricaModelo  # noqa: F401

# ── Alembic Config ──
config = context.config
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata
config.set_main_option(
    "sqlalchemy.url",
    "postgresql://agroia:agroia_dev@localhost:5434/agroia",
)


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode (generate SQL without DB connection)."""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        version_table_schema="agroia",
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode (connected to DB)."""
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            version_table_schema="agroia",
        )
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
