"""Tests for the NocoDB MCP server"""

import pytest
from mcp_tools.nocodb import NocoDBMCPServer


def test_nocodb_server_creation():
    """Test that NocoDB MCP server can be created with valid parameters"""
    server = NocoDBMCPServer(
        nocodb_url="https://example.com",
        api_token="test-token"
    )
    
    assert server.nocodb_url == "https://example.com"
    assert server.api_token == "test-token"
    assert server.mcp is not None


def test_nocodb_server_url_normalization():
    """Test that URLs are properly normalized (trailing slash removed)"""
    server = NocoDBMCPServer(
        nocodb_url="https://example.com/",
        api_token="test-token"
    )
    
    assert server.nocodb_url == "https://example.com"


def test_nocodb_server_has_mcp_server():
    """Test that the server has a get_mcp_server method and returns a FastMCP instance with expected public methods"""
    server = NocoDBMCPServer(
        nocodb_url="https://example.com",
        api_token="test-token"
    )

    mcp_server = server.get_mcp_server()
    assert mcp_server is not None
    # Check for public interface instead of private attributes
    assert hasattr(mcp_server, 'tool')
    assert callable(getattr(mcp_server, 'tool', None))
    assert hasattr(mcp_server, 'run')
    assert callable(getattr(mcp_server, 'run', None)) 