"""Company structure diagram generator for MCP Drawing Client using Plotly

This module uses Plotly to generate company structure diagrams and converts them to SVG format
for compatibility with the MCP protocol.

The module is specifically designed for creating hierarchical company structure visualizations
with support for ownership percentages, entity types, and custom styling.
"""

import logging
import math
from typing import Dict, Any, Set, Optional, List, Tuple

import plotly.graph_objects as go
from plotly.subplots import make_subplots

from .constants import (
    SVG_WIDTH, SVG_HEIGHT_BASE, SVG_HEIGHT_PER_LEVEL,
    BOX_WIDTH, BOX_HEIGHT, BOX_MARGIN, ENTITY_TYPES,
    ENTITY_STYLES, CONNECTION_STYLES, OWNERSHIP_THRESHOLDS, DEFAULT_COLORS
)


class CompanyStructureGenerator:
    """Generator for company structure diagrams using Plotly with SVG output
    
    This class specifically handles the generation of company hierarchy diagrams
    and converts them to SVG format for MCP protocol compatibility.
    """
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def generate_company_diagram(self, companies_data: Dict[str, Any], custom_colors: Dict[str, str], focus_company: str = "") -> str:
        """Generate a company structure diagram using Plotly and convert to SVG"""
        try:
            # Calculate positions and hierarchy
            company_positions = {}
            max_level = 0
            
            # Find root companies (no parents)
            root_companies = self._find_root_companies(companies_data)
            
            # Calculate levels and positions
            max_level = self._calculate_hierarchy_levels(companies_data, root_companies, company_positions)
            
            # Group companies by level
            level_companies = self._group_companies_by_level(company_positions)
            
            # Create Plotly figure
            fig = self._create_plotly_figure(companies_data, level_companies, custom_colors, focus_company, max_level)
            
            # Convert to SVG
            svg_content = fig.to_image(format="svg", width=SVG_WIDTH, height=SVG_HEIGHT_BASE + (max_level + 1) * SVG_HEIGHT_PER_LEVEL)
            
            return svg_content
            
        except Exception as e:
            self.logger.error(f"Error generating SVG diagram: {e}")
            return self._generate_error_svg(str(e))
    
    def _create_plotly_figure(self, companies_data: Dict[str, Any], level_companies: Dict[int, list], 
                            custom_colors: Dict[str, str], focus_company: str, max_level: int) -> go.Figure:
        """Create a Plotly figure for the company structure diagram"""
        
        # Create figure
        fig = go.Figure()
        
        # Define colors using constants instead of magic numbers
        colors = {
            "person": custom_colors.get("person_color", DEFAULT_COLORS["person_color"]),
            "investor": custom_colors.get("investor_color", DEFAULT_COLORS["investor_color"]),
            "trust": custom_colors.get("trust_color", DEFAULT_COLORS["trust_color"]),
            "foundation": custom_colors.get("foundation_color", DEFAULT_COLORS["foundation_color"]),
            "company": custom_colors.get("company_color", DEFAULT_COLORS["company_color"]),
            "focus_company": custom_colors.get("focus_company_color", DEFAULT_COLORS["focus_company_color"])
        }
        
        # Add company boxes
        self._add_company_boxes(fig, companies_data, level_companies, colors, focus_company, custom_colors)
        
        # Add connections
        self._add_connections(fig, companies_data, level_companies, colors)
        
        # Update layout
        fig.update_layout(
            width=SVG_WIDTH,
            height=SVG_HEIGHT_BASE + (max_level + 1) * SVG_HEIGHT_PER_LEVEL,
            showlegend=False,
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            xaxis=dict(
                showgrid=False,
                showticklabels=False,
                range=[0, SVG_WIDTH],
                fixedrange=True
            ),
            yaxis=dict(
                showgrid=False,
                showticklabels=False,
                range=[0, SVG_HEIGHT_BASE + (max_level + 1) * SVG_HEIGHT_PER_LEVEL],
                scaleanchor="x",
                scaleratio=1,
                fixedrange=True
            ),
            margin=dict(l=0, r=0, t=0, b=0)
        )
        
        return fig
    
    def _add_company_boxes(self, fig: go.Figure, companies_data: Dict[str, Any], 
                          level_companies: Dict[int, list], colors: Dict[str, str], focus_company: str, custom_colors: Dict[str, str]):
        """Add company boxes to the Plotly figure"""
        
        max_level = max(level_companies.keys()) if level_companies else 0
        
        for level in sorted(level_companies.keys()):
            companies_in_level = level_companies[level]
            level_width = len(companies_in_level) * (BOX_WIDTH + BOX_MARGIN) - BOX_MARGIN
            start_x = (SVG_WIDTH - level_width) // 2
            
            for i, company_id in enumerate(companies_in_level):
                company_data = companies_data[company_id]
                company_name = company_data.get('name', company_id)
                entity_type = company_data.get('type', 'company')
                
                x = start_x + i * (BOX_WIDTH + BOX_MARGIN) + BOX_WIDTH // 2
                # Flip the Y coordinate so that root companies (level 0) are at the top
                y = 80 + (max_level - level) * SVG_HEIGHT_PER_LEVEL + BOX_HEIGHT // 2
                
                # Determine color
                if focus_company and company_id == focus_company:
                    fill_color = colors["focus_company"]
                    line_color = custom_colors.get("focus_company_border", DEFAULT_COLORS["focus_company_stroke"])
                    line_width = 4
                else:
                    fill_color = colors.get(entity_type, colors["company"])
                    line_color = self._darken_color(fill_color)
                    line_width = 2
                
                # Add rectangle
                fig.add_shape(
                    type="rect",
                    x0=x - BOX_WIDTH // 2,
                    y0=y - BOX_HEIGHT // 2,
                    x1=x + BOX_WIDTH // 2,
                    y1=y + BOX_HEIGHT // 2,
                    fillcolor=fill_color,
                    line=dict(color=line_color, width=line_width),
                    layer="below"
                )
                
                # Add text
                fig.add_annotation(
                    x=x,
                    y=y,
                    text=company_name,
                    showarrow=False,
                    font=dict(
                        size=12,
                        color=custom_colors.get("custom_font_color", DEFAULT_COLORS["custom_font_color"])
                    )
                )
    
    def _add_connections(self, fig: go.Figure, companies_data: Dict[str, Any], 
                        level_companies: Dict[int, list], colors: Dict[str, str]):
        """Add connection lines between companies"""
        
        for company_id, company_data in companies_data.items():
            parents = company_data.get('parents', [])
            
            for parent in parents:
                # Handle both old format (string) and new format (object with id and percentage)
                if isinstance(parent, str):
                    parent_id = parent
                    ownership_percentage = None
                elif isinstance(parent, dict):
                    parent_id = parent.get('id')
                    ownership_percentage = parent.get('percentage')
                else:
                    continue
                
                # Get positions
                parent_pos = self._get_company_position(parent_id, level_companies)
                child_pos = self._get_company_position(company_id, level_companies)
                
                if parent_pos and child_pos:
                    # Determine line style based on ownership percentage
                    line_style = self._get_connection_style(ownership_percentage)
                    
                    # Add connection line - connect from center of parent to center of child
                    fig.add_shape(
                        type="line",
                        x0=parent_pos[0],
                        y0=parent_pos[1] - BOX_HEIGHT // 2,  # Connect from bottom center of parent
                        x1=child_pos[0],
                        y1=child_pos[1] + BOX_HEIGHT // 2,   # Connect to top center of child
                        line=dict(
                            color=line_style["stroke_color"],
                            width=line_style["stroke_width"],
                            dash=line_style["stroke_dasharray"] if line_style["stroke_dasharray"] != "none" else None
                        ),
                        layer="below"
                    )
                    
                    # Add ownership percentage label if available
                    if ownership_percentage is not None:
                        sanitized_percentage = self._sanitize_percentage(ownership_percentage)
                        if sanitized_percentage is not None:
                            # Position label at the midpoint of the connection line
                            label_x = (parent_pos[0] + child_pos[0]) / 2
                            label_y = (parent_pos[1] + child_pos[1]) / 2
                            
                            fig.add_annotation(
                                x=label_x,
                                y=label_y,
                                text=f"{sanitized_percentage}%",
                                showarrow=False,
                                font=dict(
                                    family="Segoe UI, Arial, sans-serif",
                                    size=12,
                                    color=DEFAULT_COLORS["custom_font_color"]
                                ),
                                xanchor="center",
                                yanchor="middle"
                            )
    
    def _get_company_position(self, company_id: str, level_companies: Dict[int, list]) -> Optional[Tuple[float, float]]:
        """Get the position of a company in the diagram"""
        max_level = max(level_companies.keys()) if level_companies else 0
        
        for level, companies_in_level in level_companies.items():
            if company_id in companies_in_level:
                level_width = len(companies_in_level) * (BOX_WIDTH + BOX_MARGIN) - BOX_MARGIN
                start_x = (SVG_WIDTH - level_width) // 2
                index = companies_in_level.index(company_id)
                x = start_x + index * (BOX_WIDTH + BOX_MARGIN) + BOX_WIDTH // 2
                # Flip the Y coordinate so that root companies (level 0) are at the top
                y = 80 + (max_level - level) * SVG_HEIGHT_PER_LEVEL + BOX_HEIGHT // 2
                return (x, y)
        return None
    
    def _sanitize_percentage(self, ownership_percentage) -> Optional[float]:
        """Sanitize ownership percentage value"""
        if ownership_percentage is not None:
            try:
                if isinstance(ownership_percentage, str):
                    value_str = ownership_percentage.strip().rstrip('%').strip()
                    parsed = float(value_str) if value_str else None
                elif isinstance(ownership_percentage, (int, float)):
                    parsed = float(ownership_percentage)
                else:
                    parsed = None
                if parsed is not None and parsed >= 0:
                    return parsed
            except Exception:
                pass
        return None
    
    def _find_root_companies(self, companies_data: Dict[str, Any]) -> list:
        """Find root companies (no parents)"""
        root_companies = []
        for company_id, company_data in companies_data.items():
            if not company_data.get('parents'):
                root_companies.append(company_id)
        
        # If no root companies, use the first company as root
        if not root_companies and companies_data:
            root_companies = [list(companies_data.keys())[0]]
        
        return root_companies
    
    def _calculate_hierarchy_levels(self, companies_data: Dict[str, Any], root_companies: list, company_positions: Dict[str, int]) -> int:
        """Calculate hierarchy levels for all companies"""
        max_level = 0
        
        def calculate_level(company_id: str, level: int = 0, visited: Set[str] = None) -> int:
            if visited is None:
                visited = set()
            
            if company_id in visited:
                return level
            
            visited.add(company_id)
            company_positions[company_id] = level
            current_max = level
            
            # Find children of this company
            children = []
            for child_id, child_data in companies_data.items():
                parents = child_data.get('parents', [])
                for parent in parents:
                    if isinstance(parent, str):
                        parent_id = parent
                    elif isinstance(parent, dict):
                        parent_id = parent.get('id')
                    else:
                        continue
                    
                    if parent_id == company_id:
                        children.append(child_id)
                        break
            
            for child_id in children:
                child_level = calculate_level(child_id, level + 1, visited)
                current_max = max(current_max, child_level)
            
            return current_max
        
        # Calculate levels starting from root companies
        for root in root_companies:
            max_level = max(max_level, calculate_level(root))
        
        return max_level
    
    def _group_companies_by_level(self, company_positions: Dict[str, int]) -> Dict[int, list]:
        """Group companies by their hierarchy level"""
        level_companies = {}
        for company_id, level in company_positions.items():
            if level not in level_companies:
                level_companies[level] = []
            level_companies[level].append(company_id)
        return level_companies
    
    def _get_connection_style(self, ownership_percentage: Optional[float]) -> Dict[str, Any]:
        """Get connection style based on ownership percentage"""
        if ownership_percentage is None:
            return CONNECTION_STYLES["default"]
        
        if ownership_percentage >= OWNERSHIP_THRESHOLDS["majority"]:
            return CONNECTION_STYLES["majority_ownership"]
        elif ownership_percentage >= OWNERSHIP_THRESHOLDS["minority"]:
            return CONNECTION_STYLES["minority_ownership"]
        else:
            return CONNECTION_STYLES["default"]
    
    def _darken_color(self, hex_color: str, factor: float = 0.8) -> str:
        """Darken a hex color by a factor"""
        try:
            # Remove # if present
            hex_color = hex_color.lstrip('#')
            # Convert to RGB
            r = int(hex_color[0:2], 16)
            g = int(hex_color[2:4], 16)
            b = int(hex_color[4:6], 16)
            # Darken
            r = int(r * factor)
            g = int(g * factor)
            b = int(b * factor)
            # Convert back to hex
            return f"#{r:02x}{g:02x}{b:02x}"
        except Exception:
            return hex_color
    
    def _generate_error_svg(self, error_message: str) -> str:
        """Generate an error SVG when diagram generation fails"""
        return f'''<svg width='400' height='200' xmlns='http://www.w3.org/2000/svg'>
    <rect width="400" height="200" fill="{DEFAULT_COLORS['error_background']}"/>
    <text x='200' y='100' text-anchor='middle' font-family='Segoe UI, Arial' font-size='14' fill='{DEFAULT_COLORS['error_text']}'>
        Error generating diagram: {error_message}
    </text>
</svg>'''
