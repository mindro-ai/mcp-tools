"""Base MCP Server for handling multiple endpoints"""

import logging
from typing import Dict, Any

import uvicorn
from fastapi import FastAPI
from mcp.server.fastmcp import FastMCP

from . import DEFAULT_NAME, DEFAULT_PORT, DEFAULT_LOG_LEVEL

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
        self.app = FastAPI()
        self.endpoints: Dict[str, Any] = {}

    def register_endpoint(self, name: str, endpoint_server: Any) -> None:
        """
        Register an MCP endpoint server
        
        Args:
            name: Name of the endpoint
            endpoint_server: The endpoint server instance that has a register_tools() method
        """
        if not hasattr(endpoint_server, 'register_tools'):
            raise ValueError(f"Endpoint server {name} must have a register_tools() method")

        # Create a new FastMCP instance for each endpoint, configured with its mount path
        endpoint_mcp = FastMCP(
            f"{self.name} - {name} Endpoint",
            log_level=self.log_level,
            root_path=f"/{name}"
        )

        # Register the endpoint's tools with the new MCP instance
        endpoint_server.register_tools(endpoint_mcp)

        # Mount the MCP instance's app at the specified path
        self.app.mount(f"/{name}", endpoint_mcp.sse_app())
        
        self.endpoints[name] = endpoint_server
        logger.info("Registered endpoint: %s at /%s/sse", name, name)

    def get_app(self) -> FastAPI:
        """Get the main FastAPI app instance"""
        return self.app

    def run(self) -> None:
        """Run the MCP server"""
        logger.info("Starting %s with %d endpoints", self.name, len(self.endpoints))
        for endpoint_name in self.endpoints:
            logger.info("  - /%s/sse", endpoint_name)

        if not self.endpoints:
            logger.error("No endpoints available to run")
            raise RuntimeError("No endpoints available to run")

        uvicorn.run(self.app, host="0.0.0.0", port=self.port, log_level=self.log_level.lower()) 


"""Base MCP Server for handling multiple endpoints"""

import logging
from typing import Dict, Any

import uvicorn
from fastapi import FastAPI
from mcp.server.fastmcp import FastMCP

from . import DEFAULT_NAME, DEFAULT_PORT, DEFAULT_LOG_LEVEL

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
        self.app = FastAPI()
        self.endpoints: Dict[str, Any] = {}

    def register_endpoint(self, name: str, endpoint_server: Any) -> None:
        """
        Register an MCP endpoint server
        
        Args:
            name: Name of the endpoint
            endpoint_server: The endpoint server instance that has a register_tools() method
        """
        if not hasattr(endpoint_server, 'register_tools'):
            raise ValueError(f"Endpoint server {name} must have a register_tools() method")

        # Create a new FastMCP instance for each endpoint, configured with its mount path
        endpoint_mcp = FastMCP(
            f"{self.name} - {name} Endpoint",
            log_level=self.log_level,
            root_path=f"/{name}"
        )

        # Register the endpoint's tools with the new MCP instance
        endpoint_server.register_tools(endpoint_mcp)

        # Mount the MCP instance's app at the specified path
        self.app.mount(f"/{name}", endpoint_mcp.sse_app())
        
        self.endpoints[name] = endpoint_server
        logger.info("Registered endpoint: %s at /%s/sse", name, name)

    def get_app(self) -> FastAPI:
        """Get the main FastAPI app instance"""
        return self.app

    def run(self) -> None:
        """Run the MCP server"""
        logger.info("Starting %s with %d endpoints", self.name, len(self.endpoints))
        for endpoint_name in self.endpoints:
            logger.info("  - /%s/sse", endpoint_name)

        if not self.endpoints:
            logger.error("No endpoints available to run")
            raise RuntimeError("No endpoints available to run")

        uvicorn.run(self.app, host="0.0.0.0", port=self.port, log_level=self.log_level.lower()) 







# """Base MCP Server for handling multiple endpoints"""

# import logging
# from typing import Dict, Any

# import uvicorn
# from fastapi import FastAPI
# from mcp.server.fastmcp import FastMCP

# from . import DEFAULT_NAME, DEFAULT_PORT, DEFAULT_LOG_LEVEL

# logger = logging.getLogger("mcp-base-server")


# class BaseMCPServer:
#     """Base class for MCP servers that can handle multiple endpoints"""

#     def __init__(self, name: str = DEFAULT_NAME, port: int = DEFAULT_PORT, log_level: str = DEFAULT_LOG_LEVEL):
#         """
#         Initialize the base MCP server
#         """
#         self.name = name
#         self.port = port
#         self.log_level = log_level
#         self.app = FastAPI()
#         self.endpoints: Dict[str, Any] = {}

#     def register_endpoint(self, name: str, endpoint_server: Any) -> None:
#         """
#         Register an MCP endpoint server
#         """
#         if not hasattr(endpoint_server, 'register_tools'):
#             raise ValueError(f"Endpoint server {name} must have a register_tools() method")

#         # Create a new FastMCP instance for each endpoint
#         endpoint_mcp = FastMCP(
#             f"{self.name} - {name} Endpoint",
#             log_level=self.log_level,
#             root_path=f"/{name}",
#             stateless_http=True  # ✅ no session_id required
#         )

#         # Register the endpoint's tools
#         endpoint_server.register_tools(endpoint_mcp)

    
#         # Mount both streaming (SSE) and standard HTTP apps under this endpoint
#         self.app.mount(f"/{name}/sse", endpoint_mcp.sse_app())
#         self.app.mount(f"/{name}/http", endpoint_mcp.streamable_http_app())

#         self.endpoints[name] = endpoint_server
#         logger.info("Registered endpoint: %s", name)
#         logger.info("  - SSE path:   /%s/sse", name)
#         logger.info("  - HTTP path:  /%s/http", name)

#     def get_app(self) -> FastAPI:
#         """Get the main FastAPI app instance"""
#         return self.app

#     def run(self) -> None:
#         """Run the MCP server"""
#         logger.info("Starting %s with %d endpoints", self.name, len(self.endpoints))
#         for endpoint_name in self.endpoints:
#             logger.info("  - /%s/sse", endpoint_name)
#             logger.info("  - /%s/http", endpoint_name)

#         if not self.endpoints:
#             logger.error("No endpoints available to run")
#             raise RuntimeError("No endpoints available to run")

#         uvicorn.run(self.app, host="0.0.0.0", port=self.port, log_level=self.log_level.lower())




