"""Base MCP Server for handling multiple endpoints"""

import logging
from typing import Dict, Any, Optional
from mcp.server.fastmcp import FastMCP, Context

from . import DEFAULT_NAME, DEFAULT_PORT, DEFAULT_LOG_LEVEL, DEFAULT_TRANSPORT

logger = logging.getLogger("mcp-base-server")


class BaseMCPServer:
    """Base class for MCP servers that can handle multiple endpoints"""
    
    def __init__(self, name: str = DEFAULT_NAME, port: int = DEFAULT_PORT, log_level: str = DEFAULT_LOG_LEVEL):
        """
        Initialize the base MCP server
        
        Args:
            name: Name of the MCP server
            port: Port number for the server
            log_level: Logging level for the server
        """
        self.name = name
        self.port = port
        self.log_level = log_level
        self.mcp = FastMCP(name, port=port, log_level=log_level)
        self.endpoints: Dict[str, Any] = {}
        
    def register_endpoint(self, name: str, endpoint_server) -> None:
        """
        Register an MCP endpoint server
        
        Args:
            name: Name of the endpoint
            endpoint_server: The endpoint server instance that has a get_mcp_server() method
        """
        if not hasattr(endpoint_server, 'get_mcp_server'):
            raise ValueError(f"Endpoint server {name} must have a get_mcp_server() method")
        
        self.endpoints[name] = endpoint_server
        logger.info("Registered endpoint: %s", name)
        
        # Note: The FastMCP class doesn't provide a way to retrieve registered tools,
        # so we can't copy tools from endpoint servers. Each endpoint server should
        # register its tools directly with its own FastMCP instance.
        # The tools will be available when the endpoint server's MCP instance is run.
        
    def get_mcp_server(self) -> FastMCP:
        """Get the main MCP server instance"""
        return self.mcp
    
    def run(self, transport: str = DEFAULT_TRANSPORT, port: int = DEFAULT_PORT) -> None:
        """Run the MCP server"""
        logger.info("Starting %s with %d endpoints", self.name, len(self.endpoints))
        for endpoint_name in self.endpoints:
            logger.info("  - %s", endpoint_name)
        
        # Since we can't merge tools from multiple FastMCP instances,
        # we'll run the first available endpoint server's MCP instance
        if self.endpoints:
            # Get the first endpoint and run its MCP server
            first_endpoint_name = list(self.endpoints.keys())[0]
            first_endpoint = self.endpoints[first_endpoint_name]
            endpoint_mcp = first_endpoint.get_mcp_server()
            
            logger.info("Running MCP server from endpoint: %s", first_endpoint_name)
            logger.info("Transport: %s, Port: %s", transport, port)
            
            try:
                if transport in ["sse", "streamable-http"]:
                    # For SSE/streamable-http transport, we need to run with uvicorn
                    import uvicorn
                    
                    logger.info("Starting %s server on port %d", transport.upper(), port)
                    
                    # Warning: FastMCP's SSE implementation doesn't properly apply mount paths
                    # if mount_path != "/" and transport == "sse":
                    #     logger.warning("Mount path '%s' is set but SSE endpoint will be available at /sse (not %s/sse)", 
                    #                  mount_path, mount_path)
                    
                    # Configure the endpoint's FastMCP instance with the correct port
                    endpoint_mcp.settings.port = port
                    
                    endpoint_mcp.run(transport=transport)
                else:
                    # Default stdio transport
                    endpoint_mcp.run(transport=transport)
            except Exception as e:
                logger.error("Error running MCP server: %s", str(e))
                raise
        else:
            logger.error("No endpoints available to run")
            raise RuntimeError("No endpoints available to run") 
