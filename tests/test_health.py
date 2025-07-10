import pytest
from mcp_tools.health import HealthMCPServer

@pytest.fixture
def health_server():
    return HealthMCPServer({"version": "test", "description": "Test health endpoint"})

@pytest.mark.asyncio
async def test_get_health_status(health_server):
    result = await health_server.get_health_status()
    assert isinstance(result, dict)
    assert result["endpoint"] == "health"
    assert result["success"] is True
    assert result["status"] == "Healthy"
    assert "message" in result
    assert "timestamp" in result 