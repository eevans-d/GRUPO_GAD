"""
Configuración y gestión de la sesión de la base de datos.
"""

import asyncio
import importlib
import os
from typing import Any, AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool
from tenacity import retry, stop_after_attempt, wait_exponential

from config.settings import settings

# --- Variables Globales para la Base de Datos ---
# Serán inicializadas por init_db()
async_engine: Any = None
AsyncSessionFactory: Any = None


def init_db(db_url: str) -> None:
    """
    Inicializa el motor de la base de datos y la fábrica de sesiones.
    Esta función se llama en el arranque de la aplicación.
    """
    global async_engine, AsyncSessionFactory

    # Configuración avanzada de pooling y timeout optimizada para producción
    POOL_SIZE = getattr(settings, "DB_POOL_SIZE", 10)  # Incrementado para mejor concurrencia
    MAX_OVERFLOW = getattr(settings, "DB_MAX_OVERFLOW", 20)  # Más conexiones en picos
    POOL_TIMEOUT = getattr(settings, "DB_POOL_TIMEOUT", 30)
    POOL_RECYCLE = getattr(settings, "DB_POOL_RECYCLE", 3600)  # Reciclar conexiones cada hora
    
    connect_args: dict[str, Any] = {}
    if db_url.startswith("sqlite"):
        # SQLite requiere este argumento para funcionar correctamente con asyncio
        connect_args = {"check_same_thread": False}

        create_kwargs: dict[str, Any] = {
            "pool_pre_ping": True,
            "echo": settings.DEBUG,
            "connect_args": connect_args,
        }
        # Usar StaticPool para bases en memoria
        if "memory" in db_url:
            create_kwargs["poolclass"] = StaticPool

        async_engine = create_async_engine(
            db_url,
            **create_kwargs,
        )
    else:
        # Configuración PostgreSQL optimizada para producción
        if "postgresql" in db_url:
            connect_args.update({
                "server_settings": {
                    "application_name": "grupo_gad_api",
                    "jit": "off",  # Desactivar JIT para consultas rápidas
                }
            })

            # Permitir deshabilitar SSL para asyncpg en entornos internos (Flycast)
            pg_sslmode = os.getenv("PGSSLMODE", "").lower()
            async_db_ssl = os.getenv("ASYNC_DB_SSL", "").lower()
            if pg_sslmode in {"disable", "allow"} or async_db_ssl in {"0", "false", "no"}:
                # asyncpg usa la clave "ssl": False para deshabilitar TLS
                connect_args["ssl"] = False

        async_engine = create_async_engine(
            db_url,
            pool_pre_ping=True,
            echo=settings.DEBUG,
            pool_size=POOL_SIZE,
            max_overflow=MAX_OVERFLOW,
            pool_timeout=POOL_TIMEOUT,
            pool_recycle=POOL_RECYCLE,
            connect_args=connect_args,
            # Configuraciones adicionales para optimización
            isolation_level="READ_COMMITTED",  # Nivel de aislamiento óptimo
            query_cache_size=1200,  # Cache de queries compiladas
        )

    # Crear una fábrica de sesiones asíncronas
    AsyncSessionFactory = async_sessionmaker(
        bind=async_engine,
        class_=AsyncSession,
        expire_on_commit=False,
        # Configuración de sesión optimizada
        autoflush=False,  # Control manual de flush para mejor performance
    )


def _ensure_initialized_default() -> None:
    """Ensure default in-memory SQLite engine/session factory exists.

    Esto permite que tests que importan AsyncSessionFactory sin haber llamado
    init_db() no fallen. En entornos reales, init_db() sobreescribirá estos
    valores con la configuración de la base de datos real.
    """
    global async_engine, AsyncSessionFactory
    if async_engine is None or AsyncSessionFactory is None:
        # Si el entorno ya define una URL de BD no-sqlite, no inicializar fallback
        db_url_env = os.getenv("DATABASE_URL", "")
        if db_url_env and not db_url_env.startswith("sqlite"):
            return

        # Intentar fallback solo si aiosqlite está disponible
        try:
            importlib.import_module("aiosqlite")
        except ImportError:
            # En entornos de runtime (docker) puede no estar instalado; init_db() se encargará
            return

        async_engine = create_async_engine(
            "sqlite+aiosqlite:///:memory:",
            echo=False,
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
        )
        AsyncSessionFactory = async_sessionmaker(
            bind=async_engine,
            class_=AsyncSession,
            expire_on_commit=False,
        )


# Inicializar por defecto para entornos de test/import sin init_db()
_ensure_initialized_default()


# --- Circuit Breaker para la Base de Datos ---
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
        
        now = asyncio.get_event_loop().time()
        if self.last_failure and (now - self.last_failure) > self.reset_timeout:
            self.reset()
            return True
        return False

db_circuit_breaker: DBCircuitBreaker = DBCircuitBreaker(max_failures=5, reset_timeout=60)


# --- Dependencia de Sesión de Base de Datos ---
@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Dependencia de FastAPI para obtener una sesión de base de datos.
    Utiliza reintentos (retry) y un circuit breaker para robustez.
    """
    if not AsyncSessionFactory:
        raise RuntimeError(
            "Database not initialized. Call init_db() on application startup."
        )

    if not db_circuit_breaker.can_attempt():
        raise RuntimeError(
            "DB circuit breaker is OPEN. Too many failures. Wait before retrying."
        )
    
    try:
        async with AsyncSessionFactory() as session:
            try:
                yield session
                # El commit explícito se elimina de aquí.
                # El código del endpoint es responsable de hacer commit.
            except Exception:
                await session.rollback()
                db_circuit_breaker.record_failure()
                raise
            finally:
                await session.close()
        # El reset se hace solo si la conexión fue exitosa
        db_circuit_breaker.reset()
    except Exception:
        # Captura fallos de conexión (p.ej. al crear la sesión)
        db_circuit_breaker.record_failure()
        raise
