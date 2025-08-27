"""Drawings MCP endpoint to provide drawing tools"""

import logging
from typing import Dict, Any

from mcp.server.fastmcp import FastMCP, Context

from .company_structure import CompanyStructureGenerator

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
        self.company_structure_generator = CompanyStructureGenerator()

    def register_tools(self, mcp: FastMCP):
        """Register all drawing tools with the MCP server"""
        mcp.tool()(self.company_structure)

    async def company_structure(
            self,
            companies: Dict[str, Any],
            custom_colors: Dict[str, str],
            focus_company: str = "",
            ctx: Context = None
    ) -> bytes:
        """
        Generates a company structure diagram as an SVG binary file.

        Args:
            companies: A dictionary defining the company structure.
            custom_colors: Custom colors dictionary for styling
            focus_company: Identifier of the company to highlight with a different color

        Returns:
            SVG binary data of the company structure diagram.

        Example:
        Get company structure:
           company_structure(companies={"mindro": {"name": "Mindro BV", "parents": []}}, custom_colors={"company_color": "#4A90E2"})
        """
        logger.info("Company structure request")

        try:
            # Generate SVG content using the new SVG generator
            svg_content = self.company_structure_generator.generate_company_diagram(
                companies, custom_colors, focus_company
            )
            
            # Convert to binary data if it's a string, otherwise return as-is
            if isinstance(svg_content, str):
                svg_binary = svg_content.encode('utf-8')
            else:
                svg_binary = svg_content
            
            logger.info("Company structure diagram generated successfully.")
            return svg_binary
        except Exception as e:
            logger.error("Failed to generate company structure diagram: %s", e)
            error_svg = self.company_structure_generator._generate_error_svg(str(e))
            return error_svg.encode('utf-8') 
