"""Tests del health check del backend."""
import pytest
from httpx import ASGITransport, AsyncClient
from agroia_backend.main import app


@pytest.mark.asyncio
async def test_health_check():
    """Verifica que el endpoint de salud responde correctamente."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] in ("ok", "degraded")
    assert data["version"] == "0.1.0"
    assert "database" in data
