"""
Archivo de configuración de pytest para las pruebas de la API.

Define fixtures para crear un entorno de prueba aislado y consistente:
- Configura una base de datos SQLite en memoria.
- Crea y destruye las tablas de la base de datos para cada sesión de prueba.
- Sobrescribe las dependencias de la aplicación para usar la base de datos de prueba.
- Ofrece un cliente (`TestClient`) para interactuar con la API.
"""
import asyncio

import pytest
import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy.dialects.postgresql import UUID as sa_UUID
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.ext.compiler import compiles
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from src.api.main import app
from src.api.models.base import Base
from src.core.database import get_db_session


@pytest.fixture(scope="session")
def event_loop(request):
    """Crea una instancia del event loop por defecto para cada sesión de prueba."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


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

TestingSessionLocal = sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)


# --- Sobrescritura de Dependencias ---
async def override_get_db_session() -> AsyncSession:
    """
    Dependencia de base de datos para ser usada durante las pruebas.
    """
    async with TestingSessionLocal() as session:
        yield session


app.dependency_overrides[get_db_session] = override_get_db_session


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
            async with TestingSessionLocal(bind=connection) as session:
                yield session
                await session.flush()
                await transaction.rollback()


@pytest_asyncio.fixture(scope="function")
async def client(db_session: AsyncSession):
    """
    Fixture que proporciona un AsyncClient de httpx para cada prueba.
    """
    from httpx import ASGITransport
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
