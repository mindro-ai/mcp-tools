import pytest
from mcp_tools.health import HealthMCPServer
import asyncio

@pytest.fixture
def health_server():
    return HealthMCPServer({"version": "test", "description": "Test health endpoint"})

@pytest.mark.asyncio
async def test_get_health_status(health_server):
    result = await health_server.get_health_status()
    assert isinstance(result, dict)
    assert result["endpoint"] == "health"
    assert result["success"] is True
    assert result["status"] == "OK"
    assert "message" in result
    assert "timestamp" in result

@pytest.mark.asyncio
async def test_get_system_info(health_server):
    result = await health_server.get_system_info()
    assert isinstance(result, dict)
    assert result["endpoint"] == "health"
    assert result["success"] is True
    assert "platform" in result
    assert "python_version" in result
    assert "hostname" in result

@pytest.mark.asyncio
async def test_get_config(health_server):
    result = await health_server.get_config()
    assert isinstance(result, dict)
    assert result["endpoint"] == "health"
    assert result["success"] is True
    assert result["config"]["version"] == "test" 