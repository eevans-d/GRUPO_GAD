"""
Configuración y gestión de la sesión de la base de datos.
"""

import asyncio
from typing import AsyncGenerator, Any

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from tenacity import retry, stop_after_attempt, wait_exponential

from config.settings import settings

# Configuración avanzada de pooling y timeout
POOL_SIZE = getattr(settings, "DB_POOL_SIZE", 5)
MAX_OVERFLOW = getattr(settings, "DB_MAX_OVERFLOW", 10)
POOL_TIMEOUT = getattr(settings, "DB_POOL_TIMEOUT", 30)


db_url = str(settings.DATABASE_URL)
if db_url.startswith("sqlite"):
    # SQLite no soporta argumentos de pooling avanzados
    async_engine = create_async_engine(
        db_url,
        pool_pre_ping=True,
        echo=settings.DEBUG,
    )
else:
    async_engine = create_async_engine(
        db_url,
        pool_pre_ping=True,
        echo=settings.DEBUG,
        pool_size=POOL_SIZE,
        max_overflow=MAX_OVERFLOW,
        pool_timeout=POOL_TIMEOUT,
    )

# Crear una fábrica de sesiones asíncronas
AsyncSessionFactory = async_sessionmaker(
    bind=async_engine,
    class_=AsyncSession,
    expire_on_commit=False,
)



# -*- coding: utf-8 -*-
"""
Configuración y gestión de la sesión de la base de datos.
"""

import asyncio
from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from tenacity import retry, stop_after_attempt, wait_exponential

from config.settings import settings

# Configuración avanzada de pooling y timeout
POOL_SIZE = getattr(settings, "DB_POOL_SIZE", 5)
MAX_OVERFLOW = getattr(settings, "DB_MAX_OVERFLOW", 10)
POOL_TIMEOUT = getattr(settings, "DB_POOL_TIMEOUT", 30)


db_url = str(settings.DATABASE_URL)
if db_url.startswith("sqlite"):
    # SQLite no soporta argumentos de pooling avanzados
    async_engine = create_async_engine(
        db_url,
        pool_pre_ping=True,
        echo=settings.DEBUG,
    )
else:
    async_engine = create_async_engine(
        db_url,
        pool_pre_ping=True,
        echo=settings.DEBUG,
        pool_size=POOL_SIZE,
        max_overflow=MAX_OVERFLOW,
        pool_timeout=POOL_TIMEOUT,
    )

# Crear una fábrica de sesiones asíncronas
AsyncSessionFactory = async_sessionmaker(
    bind=async_engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


# Circuit breaker básico
class DBCircuitBreaker:
    max_failures: int
    reset_timeout: int
    failures: int
    last_failure: float | None
    open: bool

    def __init__(self, max_failures: int = 5, reset_timeout: int = 60) -> None:
        self.max_failures = max_failures
        self.reset_timeout = reset_timeout
        self.failures = 0
        self.last_failure = None
        self.open = False

    def record_failure(self) -> None:
        self.failures += 1
        self.last_failure = asyncio.get_event_loop().time()
        if self.failures >= self.max_failures:
            self.open = True

    def reset(self) -> None:
        self.failures = 0
        self.open = False
        self.last_failure = None

    def can_attempt(self) -> bool:
        if not self.open:
            return True
        # Si ha pasado el timeout, resetear
        now = asyncio.get_event_loop().time()
        if self.last_failure and (now - self.last_failure) > self.reset_timeout:
            self.reset()
            return True
        return False

db_circuit_breaker: DBCircuitBreaker = DBCircuitBreaker(max_failures=5, reset_timeout=60)

@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Dependencia de FastAPI para obtener una sesión de base de datos con retry y circuit breaker.
    """
    if not db_circuit_breaker.can_attempt():
        raise RuntimeError("DB circuit breaker is OPEN. Too many failures. Wait before retrying.")
    try:
        async with AsyncSessionFactory() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                db_circuit_breaker.record_failure()
                raise
            finally:
                await session.close()
        db_circuit_breaker.reset()
    except Exception:
        db_circuit_breaker.record_failure()
        raise