"""Tests for the base MCP server"""

import pytest
from mcp_tools.base_server import BaseMCPServer
from mcp_tools.health import HealthMCPServer


def test_base_server_creation():
    """Test that base MCP server can be created"""
    server = BaseMCPServer("Test Server")
    
    assert server.name == "Test Server"
    assert server.mcp is not None
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
    
    with pytest.raises(ValueError, match="must have a get_mcp_server"):
        base_server.register_endpoint("invalid", invalid_endpoint)


def test_base_server_get_mcp_server():
    """Test that the server returns its MCP server instance"""
    server = BaseMCPServer("Test Server")
    mcp_server = server.get_mcp_server()
    
    assert mcp_server is not None
    assert mcp_server == server.mcp 