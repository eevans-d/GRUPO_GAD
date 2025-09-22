import asyncio
from logging.config import fileConfig

from sqlalchemy import pool
from sqlalchemy.ext.asyncio import create_async_engine

from alembic import context

# Importar todos los modelos para registrar las tablas y relaciones
from src.api.models import Base, Usuario, Efectivo, Tarea, HistorialEstado, MetricaTarea, tarea_efectivos

# Do not import Settings at module import time; import lazily inside functions


# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Set the database URL from the settings object
try:
    # best-effort: if settings are available at import time use them, otherwise
    # leave the config unset and compute the URL lazily in the migration runners.
    from config.settings import get_settings

    maybe_settings = get_settings()
    if maybe_settings.assemble_db_url():
        config.set_main_option("sqlalchemy.url", str(maybe_settings.assemble_db_url()))
except Exception:
    # Do not fail import if environment is incomplete; alembic commands will
    # compute the URL at execution time.
    pass

# Interpret the config file for Python logging.
# This line sets up loggers basically.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# add your model's MetaData object here
# for 'autogenerate' support
target_metadata = Base.metadata

# other values from the config, defined by the needs of env.py,
# can be acquired:
# my_important_option = config.get_main_option("my_important_option")
# ... etc.

def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.

    """
    # Lazily obtain DB URL to tolerate missing env vars at import time
    from config.settings import get_settings

    settings = get_settings()
    url = str(settings.assemble_db_url() or "")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection):
    context.configure(connection=connection, target_metadata=target_metadata)

    with context.begin_transaction():
        context.run_migrations()


async def run_migrations_online() -> None:
    """Run migrations in 'online' mode.

    In this scenario we need to create an Engine
    and associate a connection with the context.

    """
    # Lazily instantiate settings and build engine only when running migrations
    from config.settings import get_settings

    settings = get_settings()
    db_url = settings.assemble_db_url()
    if not db_url:
        raise RuntimeError("DATABASE_URL could not be determined for alembic migrations")

    connectable = create_async_engine(str(db_url), poolclass=pool.NullPool)

    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)

    await connectable.dispose()


if context.is_offline_mode():
    run_migrations_offline()
else:
    asyncio.run(run_migrations_online())
