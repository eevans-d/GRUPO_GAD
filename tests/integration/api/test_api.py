"""
Pruebas de integración para los endpoints generales de la API.
"""
from httpx import AsyncClient


async def test_health_check(client: AsyncClient):
    """
    Verifica que el endpoint de salud funcione correctamente.

    Args:
        client: Fixture de AsyncClient proporcionado por conftest.py
    """
    # 1. Realizar la petición al endpoint
    response = await client.get("/api/v1/health")

    # 2. Verificar el código de estado
    assert response.status_code == 200

    # 3. Verificar el contenido de la respuesta
    assert response.json() == {"status": "ok"}