"""Drawings MCP endpoint to provide drawing tools"""

import logging
from typing import Dict, Any

from mcp.server.fastmcp import FastMCP, Context

from .svg_generator import SVGGenerator

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
        self.svg_generator = SVGGenerator()

    def register_tools(self, mcp: FastMCP):
        """Register all drawing tools with the MCP server"""
        mcp.tool()(self.company_structure)

    async def company_structure(
            self,
            companies: Dict[str, Any],
            color_category: str = "professional",
            custom_colors: Dict[str, str] = None,
            focus_company: str = "",
            ctx: Context = None
    ) -> bytes:
        """
        Generates a company structure diagram as an SVG binary file.

        Args:
            companies: A dictionary defining the company structure.
            color_category: Color category for styling (professional, vibrant, pastel, monochrome, minimal, custom)
            custom_colors: Custom colors dictionary (used when color_category is "custom")
            focus_company: Identifier of the company to highlight with a different color

        Returns:
            SVG binary data of the company structure diagram.

        Example:
        Get company structure:
           company_structure(companies={"mindro": {"name": "Mindro BV", "parents": []}})
        """
        logger.info("Company structure request")

        try:
            # Generate SVG content using the new SVG generator
            svg_content = self.svg_generator.generate_company_diagram(
                companies, color_category, custom_colors, focus_company
            )
            
            # Convert SVG string to binary data
            svg_binary = svg_content.encode('utf-8')
            
            logger.info("Company structure diagram generated successfully.")
            return svg_binary
        except Exception as e:
            logger.error("Failed to generate company structure diagram: %s", e)
            error_svg = self.svg_generator._generate_error_svg(str(e))
            return error_svg.encode('utf-8') 
