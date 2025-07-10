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