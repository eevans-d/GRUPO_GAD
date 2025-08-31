"""
Archivo de configuración de pytest para las pruebas de la API.

Define fixtures para crear un entorno de prueba aislado y consistente:
- Configura una base de datos SQLite en memoria.
- Crea y destruye las tablas de la base de datos para cada sesión de prueba.
- Sobrescribe las dependencias de la aplicación para usar la base de datos de prueba.
- Proporciona un cliente de prueba de FastAPI (`TestClient`) para interactuar con la API.
"""
import asyncio
import pytest
import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from sqlalchemy.ext.compiler import compiles
from sqlalchemy.dialects.postgresql import UUID as sa_UUID

from src.api.main import app
from src.core.database import get_db_session
from src.api.models.base import Base


@pytest.fixture(scope="session")
def event_loop(request):
    """Crea una instancia del event loop por defecto para cada sesión de prueba."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


# --- Parche para compatibilidad de UUID en SQLite ---
# SQLite no tiene un tipo UUID nativo, así que le decimos a SQLAlchemy
# que lo trate como un CHAR(32) cuando compile para SQLite.
@compiles(sa_UUID, "sqlite")
def compile_uuid_for_sqlite(element, compiler, **kw):
    return "CHAR(32)"


# --- Configuración de la Base de Datos de Prueba ---

# Usamos SQLite en memoria para pruebas.
SQLALCHEMY_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

engine = create_async_engine(
    SQLALCHEMY_DATABASE_URL,
    poolclass=StaticPool,
)

# Creamos una fábrica de sesiones de prueba asíncrona
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
    Crea una nueva sesión para cada prueba y la cierra después.
    """
    async with TestingSessionLocal() as session:
        yield session


# Aplicamos la sobrescritura a la aplicación FastAPI
app.dependency_overrides[get_db_session] = override_get_db_session


# --- Fixtures de Pytest ---


@pytest_asyncio.fixture(scope="session")
async def db_engine():
    """
    Fixture de sesión que crea todas las tablas al inicio de las pruebas
    y las elimina al final.
    """
    # HACK: Anular el esquema para la compatibilidad con SQLite en pruebas
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
    Fixture de función que proporciona una sesión de base de datos asíncrona limpia
    para cada prueba. Las transacciones se revierten al final.
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
    # La dependencia get_db_session es sobrescrita, y db_session asegura que la tx está lista.
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac