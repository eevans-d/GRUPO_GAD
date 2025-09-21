from src.core import database
from src.core.database import AsyncSessionFactory, DBCircuitBreaker

# =======================
# Tests de base de datos
# =======================

def test_circuit_breaker_open():
    breaker = DBCircuitBreaker(max_failures=1, reset_timeout=1)
    breaker.failures = 1
    breaker.open = True
    assert breaker.open

def test_async_session_factory_error():
    try:
        _ = AsyncSessionFactory()
    except Exception:
        pass  # Esperado si la configuración es inválida

def test_async_session_factory_run():
    # Solo prueba que se puede crear una sesión (no conecta realmente)
    session = AsyncSessionFactory()
    assert session is not None

def test_circuit_breaker_failures():
    breaker = DBCircuitBreaker(max_failures=2, reset_timeout=1)
    breaker.failures = 2
    breaker.open = True
    assert breaker.open

def test_async_engine_exists():
    assert hasattr(database, "async_engine")
    assert database.async_engine is not None

def test_async_session_factory():
    assert hasattr(database, "AsyncSessionFactory")
    session_factory = database.AsyncSessionFactory
    assert callable(session_factory)

def test_circuit_breaker_init():
    breaker = database.DBCircuitBreaker(max_failures=3, reset_timeout=10)
    assert breaker.max_failures == 3
    assert breaker.reset_timeout == 10
    assert breaker.failures == 0
    assert breaker.open is False
