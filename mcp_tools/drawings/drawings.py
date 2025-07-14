"""Drawings MCP endpoint to provide drawing tools"""

import logging
from typing import Dict, Any

from mcp.server.fastmcp import FastMCP, Context

from .company_structure import generate_diagram

logger = logging.getLogger("drawings-endpoint")


class DrawingsMCPServer:
    """Drawings MCP Server implementation to provide drawing tools"""

    def __init__(self, config: Dict[str, Any] = None):
        """
        Initialize the Drawings MCP Server
        
        Args:
            config: Configuration dictionary for the endpoint
        """
        self.config = config or {}

    def register_tools(self, mcp: FastMCP):
        """Register all drawing tools with the MCP server"""
        mcp.tool()(self.company_structure)

    async def company_structure(
            self,
            companies: Dict[str, Any],
            ctx: Context = None
    ) -> str:
        """
        Generates a company structure diagram as an SVG.

        Args:
            companies: A dictionary defining the company structure.

        Returns:
            An SVG string of the company structure diagram.

        Example:
        Get company structure:
           company_structure(companies={"mindro": {"name": "Mindro BV", "parents": []}})
        """
        logger.info("Company structure request")

        try:
            fig = generate_diagram(companies)
            # Using kaleido to convert to svg
            svg_image = fig.to_image(format="svg").decode("utf-8")
            logger.info("Company structure diagram generated successfully.")
            return svg_image
        except Exception as e:
            logger.error("Failed to generate company structure diagram: %s", e)
            return f"Error: {e}" 
