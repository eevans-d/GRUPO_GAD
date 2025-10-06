"""
Archivo de configuración de pytest para las pruebas de la API.

Define fixtures para crear un entorno de prueba aislado y consistente:
- Configura una base de datos SQLite en memoria.
- Crea y destruye las tablas de la base de datos para cada sesión de prueba.
- Sobrescribe las dependencias de la aplicación para usar la base de datos de prueba.
- Ofrece un cliente (`TestClient`) para interactuar con la API.
"""

import pytest
import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy.dialects.postgresql import UUID as sa_UUID
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.ext.compiler import compiles
from sqlalchemy.pool import StaticPool
from typing import AsyncGenerator

from src.api.main import app
import threading
import time
import uvicorn
from typing import Iterator
from src.api.models.base import Base
from src.core.database import get_db_session
from jose import jwt
import os

ALGORITHM = "HS256"


## Eliminado event_loop fixture personalizado para apoyarnos en el fixture oficial
## de pytest-asyncio y evitar la advertencia de deprecación.


# --- Parche para compatibilidad de UUID en SQLite ---
@compiles(sa_UUID, "sqlite")
def compile_uuid_for_sqlite(element, compiler, **kw):
    return "CHAR(32)"


# --- Configuración de la Base de Datos de Prueba ---
SQLALCHEMY_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

engine = create_async_engine(
    SQLALCHEMY_DATABASE_URL,
    poolclass=StaticPool,
)

TestingSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


# --- Sobrescritura de Dependencias ---
async def override_get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Dependencia de base de datos para ser usada durante las pruebas.
    """
    async with TestingSessionLocal() as session:  # type: ignore[call-arg]
        yield session


# --- Fixture para generación de tokens JWT consistentes ---
@pytest.fixture(scope="session")
def token_factory():
    """Devuelve una función para crear JWTs consistentes con el SECRET_KEY actual.

    Ajusta SECRET_KEY en entorno si está vacío para evitar desajustes entre
    router y tests. Uso:

        def test_algo(token_factory):
            token = token_factory(123)
    """
    from config.settings import settings as _settings

    def _make(sub: str | int, **extra):
        secret = getattr(_settings, "SECRET_KEY", "") or os.environ.get("SECRET_KEY", "")
        if not secret:
            secret = "test-secret-key"
            os.environ["SECRET_KEY"] = secret
            # Intentar fijar en instancia interna (fail-tolerant)
            try:  # noqa: S110
                if getattr(_settings, "_inst", None) is not None:  # type: ignore[attr-defined]
                    _settings._inst.SECRET_KEY = secret  # type: ignore[attr-defined]
            except Exception:  # pragma: no cover
                pass
        payload = {"sub": str(sub), **extra}
        return jwt.encode(payload, secret, algorithm=ALGORITHM)

    return _make


# --- Fixtures de Pytest ---
@pytest_asyncio.fixture(scope="session")
async def db_engine():
    """
    Fixture de sesión que crea todas las tablas al inicio y las elimina al final.
    """
    Base.metadata.schema = None
    for table in Base.metadata.tables.values():
        table.schema = None

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield engine

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest_asyncio.fixture(scope="function")
async def db_session(db_engine):
    """
    Fixture que proporciona una sesión de BD asíncrona limpia para cada prueba.
    """
    async with db_engine.connect() as connection:
        async with connection.begin() as transaction:
            SessionLocalBind = async_sessionmaker(
                bind=connection,
                class_=AsyncSession,
                expire_on_commit=False,
            )
            async with SessionLocalBind() as session:  # type: ignore[call-arg]
                yield session
                await session.flush()
                await transaction.rollback()


@pytest_asyncio.fixture(scope="function")
async def client(db_session: AsyncSession):
    """
    Fixture que proporciona un AsyncClient de httpx para cada prueba.
    """
    # Override the database dependency to use the test session
    async def override_db():
        yield db_session
    
    app.dependency_overrides[get_db_session] = override_db
    
    from httpx import ASGITransport
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
    
    # Clean up override after test
    if get_db_session in app.dependency_overrides:
        del app.dependency_overrides[get_db_session]


# --- Fixture de servidor WebSocket real (para E2E) ---
@pytest.fixture(scope="session")
def ws_server() -> Iterator[str]:
    """Levanta un uvicorn real en un hilo para pruebas WebSocket E2E.

    Puerto fijo para simplicidad; si se requiriera parametrizar, se puede
    usar unused_tcp_port fixture en el futuro. Evitamos modificar lógica
    productiva (modo anclado).
    """
    host = "127.0.0.1"
    port = 8765
    config = uvicorn.Config(app, host=host, port=port, log_level="warning")
    server = uvicorn.Server(config)

    thread = threading.Thread(target=server.run, daemon=True)
    thread.start()

    timeout = time.time() + 10
    while not getattr(server, "started", False):  # type: ignore[attr-defined]
        if time.time() > timeout:
            raise RuntimeError("Timeout iniciando servidor uvicorn para pruebas WS")
        time.sleep(0.05)

    yield f"ws://{host}:{port}"

    server.should_exit = True
    thread.join(timeout=5)
