"""Health MCP endpoint to provide system health information"""

import logging
import time
import platform
from typing import Dict, Any
from mcp.server.fastmcp import FastMCP, Context

logger = logging.getLogger("health-endpoint")


class HealthMCPServer:
    """Health MCP Server implementation to provide system health information"""
    
    def __init__(self, config: Dict[str, Any] = None):
        """
        Initialize the Health MCP Server
        
        Args:
            config: Configuration dictionary for the endpoint
        """
        self.config = config or {}
        self.mcp = FastMCP("Health MCP Server", log_level="ERROR")
        self._register_tools()
    
    def _register_tools(self):
        """Register all health tools with the MCP server"""
        self.mcp.tool()(self.get_health_status)
        self.mcp.tool()(self.get_system_info)
        self.mcp.tool()(self.get_config)
    
    async def get_health_status(
        self,
        ctx: Context = None
    ) -> Dict[str, Any]:
        """
        Get the current health status of the system.
        
        Returns:
        - Dictionary containing the health status information
        
        Example:
        Check system health:
           get_health_status()
        """
        logger.info("Health status request")
        
        health_status = {
            "status": "OK",
            "timestamp": time.time(),
            "message": "Service is live and healthy",
            "endpoint": "health",
            "success": True
        }
        
        logger.info("Health status: OK")
        return health_status
    
    async def get_system_info(
        self,
        ctx: Context = None
    ) -> Dict[str, Any]:
        """
        Get basic system information.
        
        Returns:
        - Dictionary containing system information
        
        Example:
        Get system information:
           get_system_info()
        """
        logger.info("System info request")
        
        try:
            system_info = {
                "platform": platform.system(),
                "python_version": platform.python_version(),
                "hostname": platform.node(),
                "endpoint": "health",
                "success": True
            }
            
            logger.info(f"System info retrieved for {system_info['platform']}")
            return system_info
            
        except Exception as e:
            logger.error(f"Error getting system info: {str(e)}")
            return {
                "error": str(e),
                "endpoint": "health",
                "success": False
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
            "endpoint": "health",
            "config": self.config,
            "success": True
        }
    
    def get_mcp_server(self) -> FastMCP:
        """Get the MCP server instance"""
        return self.mcp 