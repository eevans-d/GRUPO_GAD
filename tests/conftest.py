"""
Archivo de configuración de pytest para las pruebas de la API.

Define fixtures para crear un entorno de prueba aislado y consistente:
- Configura una base de datos SQLite en memoria.
- Crea y destruye las tablas de la base de datos para cada sesión de prueba.
- Sobrescribe las dependencias de la aplicación para usar la base de datos de prueba.
- Proporciona un cliente de prueba de FastAPI (`TestClient`) para interactuar con la API.
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from sqlalchemy.ext.compiler import compiles
from sqlalchemy.dialects.postgresql import UUID as sa_UUID

from src.api.main import app
from src.core.database import get_db_session
from src.api.models.base import Base


# --- Parche para compatibilidad de UUID en SQLite ---
# SQLite no tiene un tipo UUID nativo, así que le decimos a SQLAlchemy
# que lo trate como un CHAR(32) cuando compile para SQLite.
@compiles(sa_UUID, "sqlite")
def compile_uuid_for_sqlite(element, compiler, **kw):
    return "CHAR(32)"


# --- Configuración de la Base de Datos de Prueba ---

# Usamos SQLite en memoria para pruebas.
# StaticPool es necesario para asegurar que se use la misma conexión a través de los threads
# que TestClient puede usar.
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)

# Creamos una fábrica de sesiones de prueba
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


# --- Sobrescritura de Dependencias ---


def override_get_db_session():
    """
    Dependencia de base de datos para ser usada durante las pruebas.
    Crea una nueva sesión para cada prueba y la cierra después.
    """
    database = TestingSessionLocal()
    try:
        yield database
    finally:
        database.close()


# Aplicamos la sobrescritura a la aplicación FastAPI
app.dependency_overrides[get_db_session] = override_get_db_session


# --- Fixtures de Pytest ---


@pytest.fixture(scope="session")
def db_engine():
    """
    Fixture de sesión que crea todas las tablas al inicio de las pruebas
    y las elimina al final.
    """
    # Importar todos los modelos para que se registren en Base.metadata

    # HACK: Anular el esquema para la compatibilidad con SQLite en pruebas
    Base.metadata.schema = None
    for table in Base.metadata.tables.values():
        table.schema = None

    Base.metadata.create_all(bind=engine)
    yield engine
    Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def db_session(db_engine):
    """
    Fixture de función que proporciona una sesión de base de datos limpia
    para cada prueba. Las transacciones se revierten al final.
    """
    connection = db_engine.connect()
    # Iniciar una transacción anidada
    transaction = connection.begin()
    # Vincular la sesión a esta conexión
    session = TestingSessionLocal(bind=connection)

    yield session

    session.close()
    # Revertir la transacción para limpiar los datos de la prueba
    transaction.rollback()
    connection.close()


@pytest.fixture(scope="function")
def client(db_session):
    """
    Fixture que proporciona un TestClient de FastAPI para cada prueba.
    Depende de la sesión de la base de datos para asegurar que el entorno
    esté listo.
    """
    # La dependencia get_db_session será satisfecha por override_get_db_session,
    # pero db_session asegura que la base de datos y las tablas estén listas.
    yield TestClient(app)
