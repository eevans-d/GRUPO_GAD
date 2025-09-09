import pytest
import asyncio
from src.core.database import DBCircuitBreaker, get_db_session

# =======================
# Tests de base de datos
# =======================

class DummySession:
    async def commit(self): pass
    async def rollback(self): pass
    async def close(self): pass

def test_circuit_breaker_basic():
    cb = DBCircuitBreaker(max_failures=2, reset_timeout=1)
    assert cb.can_attempt()
    cb.record_failure()
    assert cb.can_attempt()
    cb.record_failure()
    assert not cb.can_attempt()
    cb.reset()
    assert cb.can_attempt()

@pytest.mark.asyncio
async def test_circuit_breaker_timeout():
    cb = DBCircuitBreaker(max_failures=1, reset_timeout=0.1)
    cb.record_failure()
    assert not cb.can_attempt()
    await asyncio.sleep(0.2)
    assert cb.can_attempt()

@pytest.mark.asyncio
async def test_get_db_session_circuit_breaker(monkeypatch):
    from src.core.database import db_circuit_breaker
    db_circuit_breaker.open = True
    db_circuit_breaker.last_failure = asyncio.get_event_loop().time()
    with pytest.raises(RuntimeError):
        await get_db_session().__anext__()
    db_circuit_breaker.reset()
    assert db_circuit_breaker.can_attempt()
