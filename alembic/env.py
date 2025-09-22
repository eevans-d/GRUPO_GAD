# -*- coding: utf-8 -*-
"""
Configuración mejorada del entorno Alembic para GRUPO_GAD.

Esta versión incluye:
- Manejo robusto de URLs de base de datos
- Logging estructurado integrado
- Validación de conexiones
- Mejor manejo de errores
- Soporte para async/sync
"""

import asyncio
import os
import sys
from logging.config import fileConfig
from pathlib import Path
from typing import Optional

from sqlalchemy import pool, create_engine, text
from sqlalchemy.ext.asyncio import create_async_engine
from alembic import context

# Agregar el directorio raíz al path para imports
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Logging estructurado
try:
    from src.core.logging import get_logger
    migration_logger = get_logger("alembic.env")
    use_structured_logging = True
except ImportError:
    import logging
    migration_logger = logging.getLogger("alembic.env")
    use_structured_logging = False

# Importar modelos
try:
    from src.api.models import Base, Usuario, Efectivo, Tarea, HistorialEstado, MetricaTarea, tarea_efectivos
    target_metadata = Base.metadata
    
    if use_structured_logging:
        migration_logger.info(
            f"Modelos importados exitosamente: {len(Base.metadata.tables)} tablas"
        )
    else:
        migration_logger.info(f"Modelos importados: {len(Base.metadata.tables)} tablas")
        
except ImportError as e:
    target_metadata = None
    if use_structured_logging:
        migration_logger.error(
            f"Error importando modelos de la aplicación: {str(e)}"
        )
    else:
        migration_logger.error(f"Error importando modelos: {e}")

# Do not import Settings at module import time; import lazily inside functions


# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config


def get_database_url() -> Optional[str]:
    """
    Obtiene la URL de la base de datos de múltiples fuentes.
    
    Returns:
        URL de conexión a la base de datos o None si no se encuentra
    """
    # 1. Variable de entorno específica para Alembic
    url = os.getenv("ALEMBIC_DATABASE_URL")
    if url:
        if use_structured_logging:
            migration_logger.info("Usando URL de ALEMBIC_DATABASE_URL")
        else:
            migration_logger.info("Usando URL de ALEMBIC_DATABASE_URL")
        return url
    
    # 2. Variable de entorno general
    url = os.getenv("DATABASE_URL")
    if url:
        if use_structured_logging:
            migration_logger.info("Usando URL de DATABASE_URL")
        else:
            migration_logger.info("Usando URL de DATABASE_URL")
        return url
    
    # 3. Construir desde componentes de entorno
    db_components = {
        'host': os.getenv("DB_HOST", "localhost"),
        'port': os.getenv("DB_PORT", "5432"),
        'name': os.getenv("DB_NAME", "vibe_db"),  # Usar la BD que está corriendo
        'user': os.getenv("DB_USER", "user"),     # Credenciales del contenedor actual
        'password': os.getenv("DB_PASSWORD", "pass")
    }
    
    url = f"postgresql://{db_components['user']}:{db_components['password']}@{db_components['host']}:{db_components['port']}/{db_components['name']}"
    
    if use_structured_logging:
        migration_logger.info(
            f"URL construida desde componentes: {db_components['host']}:{db_components['port']}/{db_components['name']}"
        )
    else:
        migration_logger.info(f"URL construida desde componentes: {db_components['host']}:{db_components['port']}/{db_components['name']}")
    
    return url


def validate_database_connection(url: str) -> bool:
    """
    Valida que se pueda conectar a la base de datos.
    
    Args:
        url: URL de conexión a validar
        
    Returns:
        True si la conexión es exitosa, False en caso contrario
    """
    try:
        # Crear un motor temporal para validar la conexión
        engine = create_engine(url, pool_pre_ping=True)
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        engine.dispose()
        
        if use_structured_logging:
            migration_logger.info("Validación de conexión exitosa")
        else:
            migration_logger.info("Validación de conexión exitosa")
        
        return True
        
    except Exception as e:
        if use_structured_logging:
            migration_logger.error(f"Error validando conexión a base de datos: {str(e)}")
        else:
            migration_logger.error(f"Error validando conexión: {e}")
        
        return False

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
    if use_structured_logging:
        migration_logger.info("Iniciando migraciones en modo offline")
    else:
        migration_logger.info("Iniciando migraciones en modo offline")
    
    # Intentar obtener URL de múltiples fuentes
    url = get_database_url()
    
    # Fallback al método original si no se encuentra URL
    if not url:
        try:
            from config.settings import get_settings
            settings = get_settings()
            url = str(settings.assemble_db_url() or "")
        except Exception as e:
            if use_structured_logging:
                migration_logger.error(f"Error obteniendo configuración: {str(e)}")
            else:
                migration_logger.error(f"Error obteniendo configuración: {e}")
            raise
    
    if not url:
        raise RuntimeError("No se pudo obtener URL de base de datos para migraciones offline")
    
    if use_structured_logging:
        migration_logger.info("Configurando contexto de migración offline")
    else:
        migration_logger.info("Configurando contexto de migración offline")
    
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()
        
    if use_structured_logging:
        migration_logger.info("Migraciones offline completadas")
    else:
        migration_logger.info("Migraciones offline completadas")


def do_run_migrations(connection):
    """Ejecuta las migraciones con logging mejorado."""
    if use_structured_logging:
        migration_logger.info("Configurando contexto de migración con conexión")
    else:
        migration_logger.info("Configurando contexto de migración con conexión")
    
    context.configure(connection=connection, target_metadata=target_metadata)

    with context.begin_transaction():
        if use_structured_logging:
            migration_logger.info("Ejecutando migraciones en transacción")
        else:
            migration_logger.info("Ejecutando migraciones en transacción")
        
        context.run_migrations()
        
        if use_structured_logging:
            migration_logger.info("Migraciones ejecutadas exitosamente")
        else:
            migration_logger.info("Migraciones ejecutadas exitosamente")


async def run_migrations_online() -> None:
    """Run migrations in 'online' mode.

    In this scenario we need to create an Engine
    and associate a connection with the context.

    """
    if use_structured_logging:
        migration_logger.info("Iniciando migraciones en modo online (async)")
    else:
        migration_logger.info("Iniciando migraciones en modo online (async)")
    
    # Intentar obtener URL de múltiples fuentes
    db_url = get_database_url()
    
    # Fallback al método original si no se encuentra URL
    if not db_url:
        try:
            from config.settings import get_settings
            settings = get_settings()
            db_url = str(settings.assemble_db_url())
        except Exception as e:
            if use_structured_logging:
                migration_logger.error(f"Error obteniendo configuración: {str(e)}")
            else:
                migration_logger.error(f"Error obteniendo configuración: {e}")
            raise
    
    if not db_url:
        raise RuntimeError("DATABASE_URL could not be determined for alembic migrations")
    
    # Validar conexión antes de proceder
    sync_url = db_url.replace("postgresql+asyncpg://", "postgresql://")
    if not validate_database_connection(sync_url):
        raise RuntimeError("No se pudo validar la conexión a la base de datos")
    
    if use_structured_logging:
        migration_logger.info("Creando motor async para migraciones")
    else:
        migration_logger.info("Creando motor async para migraciones")
    
    # Asegurar que la URL sea async
    if not db_url.startswith("postgresql+asyncpg://"):
        db_url = db_url.replace("postgresql://", "postgresql+asyncpg://")
    
    connectable = create_async_engine(db_url, poolclass=pool.NullPool)

    try:
        async with connectable.connect() as connection:
            await connection.run_sync(do_run_migrations)
        
        if use_structured_logging:
            migration_logger.info("Migraciones online completadas exitosamente")
        else:
            migration_logger.info("Migraciones online completadas exitosamente")
            
    except Exception as e:
        if use_structured_logging:
            migration_logger.error(f"Error durante migraciones online: {str(e)}")
        else:
            migration_logger.error(f"Error durante migraciones online: {e}")
        raise
    finally:
        await connectable.dispose()


# Ejecución principal con manejo de errores mejorado
if context.is_offline_mode():
    if use_structured_logging:
        migration_logger.info("Ejecutando en modo offline")
    else:
        migration_logger.info("Ejecutando en modo offline")
    
    try:
        run_migrations_offline()
    except Exception as e:
        if use_structured_logging:
            migration_logger.error(f"Error en migraciones offline: {str(e)}")
        else:
            migration_logger.error(f"Error en migraciones offline: {e}")
        raise
else:
    if use_structured_logging:
        migration_logger.info("Ejecutando en modo online")
    else:
        migration_logger.info("Ejecutando en modo online")
    
    try:
        asyncio.run(run_migrations_online())
    except Exception as e:
        if use_structured_logging:
            migration_logger.error(f"Error en migraciones online: {str(e)}")
        else:
            migration_logger.error(f"Error en migraciones online: {e}")
        raise
