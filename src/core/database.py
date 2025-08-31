# -*- coding: utf-8 -*-
"""
Configuración y gestión de la sesión de la base de datos.
"""

from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker # Changed import
# from sqlalchemy.orm import sessionmaker # Removed import

from config.settings import settings

# Crear el motor de base de datos asíncrono
async_engine = create_async_engine(
    str(settings.DB_URL),
    pool_pre_ping=True,
    echo=settings.DEBUG,
)

# Crear una fábrica de sesiones asíncronas
AsyncSessionFactory = async_sessionmaker( # Changed to async_sessionmaker
    bind=async_engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Dependencia de FastAPI para obtener una sesión de base de datos.
    """
    async with AsyncSessionFactory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
