# -*- coding: utf-8 -*-
"""
Configuración mejorada para Alembic con logging y manejo de errores.

Incluye:
- Configuración robusta de conexiones
- Logging de migraciones
- Validación de environment
- Manejo de errores mejorado
"""

import asyncio
from logging.config import fileConfig
from pathlib import Path
import sys
import os

from sqlalchemy import pool
from sqlalchemy.ext.asyncio import create_async_engine
from alembic import context

# Agregar el directorio raíz al path para imports
ROOT_DIR = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT_DIR))

# Configurar logging para alembic
import logging
logger = logging.getLogger("alembic.env")

# Importar todos los modelos para registrar las tablas y relaciones  
try:
    from src.api.models import Base, Usuario, Efectivo, Tarea, HistorialEstado, MetricaTarea, tarea_efectivos
    logger.info("Modelos importados correctamente")
except ImportError as e:
    logger.error(f"Error importando modelos: {e}")
    raise

# Configuración de Alembic
config = context.config

# Función para obtener la URL de la base de datos
def get_database_url():
    """
    Obtiene la URL de la base de datos desde diferentes fuentes.
    
    Returns:
        str: URL de conexión a la base de datos
    """
    # Prioridad 1: Variable de ambiente
    db_url = os.getenv("DATABASE_URL")
    if db_url:
        logger.info("Usando DATABASE_URL desde variables de ambiente")
        return db_url
    
    # Prioridad 2: Settings del proyecto
    try:
        from config.settings import get_settings
        settings = get_settings()
        db_url = settings.assemble_db_url()
        if db_url:
            logger.info("Usando URL desde settings del proyecto")
            return str(db_url)
    except Exception as e:
        logger.warning(f"No se pudo obtener URL desde settings: {e}")
    
    # Prioridad 3: URL por defecto para desarrollo
    default_url = "postgresql+asyncpg://postgres:postgres@localhost:5432/grupogad"
    logger.info("Usando URL por defecto para desarrollo")
    return default_url

# Configurar la URL de la base de datos
try:
    database_url = get_database_url()
    config.set_main_option("sqlalchemy.url", database_url)
    logger.info(f"URL de base de datos configurada: {database_url.split('@')[0]}@****")
except Exception as e:
    logger.error(f"Error configurando URL de base de datos: {e}")
    raise

# Configurar logging desde archivo de configuración
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# MetaData target para autogenerate
target_metadata = Base.metadata


def run_migrations_offline() -> None:
    """
    Ejecuta migraciones en modo 'offline'.
    
    Configura el contexto con solo una URL y no un engine.
    Útil para generar SQL sin ejecutar.
    """
    url = config.get_main_option("sqlalchemy.url")
    if not url:
        raise ValueError("No se pudo obtener la URL de la base de datos")
    
    # Ocultar credenciales en los logs
    safe_url = url.split('@')[0] + "@****" if '@' in url else "****"
    logger.info(f"Ejecutando migraciones offline con URL: {safe_url}")
    
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
        compare_server_default=True,
        include_schemas=True,
    )

    with context.begin_transaction():
        logger.info("Iniciando transacción offline")
        context.run_migrations()
        logger.info("Migraciones offline completadas")


async def run_migrations_online() -> None:
    """
    Ejecuta migraciones en modo 'online'.
    
    Crea un engine real y conecta a la base de datos.
    """
    configuration = config.get_section(config.config_ini_section)
    if not configuration:
        raise ValueError("No se encontró sección de configuración en alembic.ini")
    
    # Obtener y validar URL
    db_url = config.get_main_option("sqlalchemy.url")
    if not db_url:
        raise ValueError("No se pudo obtener la URL de la base de datos para migraciones online")
    
    # Configurar engine asíncrono
    connectable = create_async_engine(
        db_url,
        poolclass=pool.NullPool,
        echo=False,  # Cambiar a True para debug de SQL
        future=True,
    )

    logger.info("Conectando a la base de datos para migraciones online")
    
    try:
        async with connectable.connect() as connection:
            logger.info("Conexión establecida exitosamente")
            
            await connection.run_sync(do_run_migrations)
            logger.info("Migraciones online completadas")
            
    except Exception as e:
        logger.error(f"Error durante migraciones online: {e}")
        raise
    finally:
        await connectable.dispose()
        logger.info("Engine de base de datos cerrado")


def do_run_migrations(connection):
    """
    Ejecuta las migraciones en la conexión sincrónica.
    
    Args:
        connection: Conexión SQLAlchemy sincrónica
    """
    context.configure(
        connection=connection,
        target_metadata=target_metadata,
        compare_type=True,
        compare_server_default=True,
        include_schemas=True,
        # Opciones adicionales para mejor tracking
        transaction_per_migration=True,
        transactional_ddl=True,
    )

    with context.begin_transaction():
        logger.info("Iniciando transacción para migraciones")
        context.run_migrations()


# Determinar modo de ejecución
if context.is_offline_mode():
    logger.info("Modo offline detectado")
    run_migrations_offline()
else:
    logger.info("Modo online detectado")
    asyncio.run(run_migrations_online())