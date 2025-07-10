"""Tests for the base MCP server"""

import pytest
from mcp_tools.base_server import BaseMCPServer
from mcp_tools.health import HealthMCPServer


def test_base_server_creation():
    """Test that base MCP server can be created"""
    server = BaseMCPServer("Test Server")
    
    assert server.name == "Test Server"
    assert server.app is not None
    assert len(server.endpoints) == 0


def test_base_server_register_endpoint():
    """Test that endpoints can be registered"""
    base_server = BaseMCPServer("Test Server")
    health_server = HealthMCPServer({"test": "config"})
    
    base_server.register_endpoint("health", health_server)
    
    assert "health" in base_server.endpoints
    assert base_server.endpoints["health"] == health_server


def test_base_server_register_invalid_endpoint():
    """Test that invalid endpoints are rejected"""
    base_server = BaseMCPServer("Test Server")
    
    # Create an object without get_mcp_server method
    invalid_endpoint = object()
    
    with pytest.raises(ValueError, match=r"Endpoint server invalid must have a register_tools\(\) method"):
        base_server.register_endpoint("invalid", invalid_endpoint)


def test_base_server_get_app():
    """Test that the server returns its FastAPI app instance"""
    server = BaseMCPServer("Test Server")
    app = server.get_app()
    
    assert app is not None
    assert app == server.app 