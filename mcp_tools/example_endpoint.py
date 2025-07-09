"""Example MCP endpoint to demonstrate extensibility"""

import logging
from typing import Dict, Any
from mcp.server.fastmcp import FastMCP, Context

logger = logging.getLogger("example-endpoint")


class ExampleMCPServer:
    """Example MCP Server implementation to demonstrate extensibility"""
    
    def __init__(self, config: Dict[str, Any] = None):
        """
        Initialize the Example MCP Server
        
        Args:
            config: Configuration dictionary for the endpoint
        """
        self.config = config or {}
        self.mcp = FastMCP("Example MCP Server", log_level="ERROR")
        self._register_tools()
    
    def _register_tools(self):
        """Register all example tools with the MCP server"""
        self.mcp.tool()(self.hello_world)
        self.mcp.tool()(self.get_config)
    
    async def hello_world(
        self,
        name: str = "World",
        ctx: Context = None
    ) -> Dict[str, Any]:
        """
        A simple hello world tool to demonstrate endpoint functionality.
        
        Parameters:
        - name: Name to greet (default: "World")
        
        Returns:
        - Dictionary containing the greeting message
        
        Example:
        Say hello to someone:
           hello_world(name="Alice")
        """
        logger.info(f"Hello world request for name: {name}")
        
        message = f"Hello, {name}!"
        logger.info(f"Generated greeting: {message}")
        
        return {
            "message": message,
            "endpoint": "example",
            "success": True
        }
    
    async def get_config(
        self,
        ctx: Context = None
    ) -> Dict[str, Any]:
        """
        Get the configuration for this endpoint.
        
        Returns:
        - Dictionary containing the endpoint configuration
        
        Example:
        Get the endpoint configuration:
           get_config()
        """
        logger.info("Get config request")
        
        return {
            "endpoint": "example",
            "config": self.config,
            "success": True
        }
    
    def get_mcp_server(self) -> FastMCP:
        """Get the MCP server instance"""
        return self.mcp 