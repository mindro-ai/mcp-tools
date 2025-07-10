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
    
    def register_tools(self, mcp: FastMCP):
        """Register all health tools with the MCP server"""
        mcp.tool()(self.get_health_status)
    
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
            "status": "Healthy",
            "timestamp": time.time(),
            "message": "Service is live and healthy",
            "endpoint": "health",
            "success": True
        }
        
        logger.info("Health status: OK")
        return health_status
