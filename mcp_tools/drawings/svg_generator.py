"""SVG generator for MCP Drawing Client"""

import logging
import math
from typing import Dict, Any, Set, Optional

from .constants import (
    SVG_WIDTH, SVG_HEIGHT_BASE, SVG_HEIGHT_PER_LEVEL,
    BOX_WIDTH, BOX_HEIGHT, BOX_MARGIN, ENTITY_TYPES,
    ENTITY_STYLES, CONNECTION_STYLES, OWNERSHIP_THRESHOLDS,
    COLOR_CATEGORIES
)


class SVGGenerator:
    """Generator for SVG diagrams with enhanced styling"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def generate_company_diagram(self, companies_data: Dict[str, Any], color_category: str = "professional", custom_colors: Dict[str, str] = None, focus_company: str = "") -> str:
        """Generate a simple SVG diagram locally"""
        try:
            # Get the color category styles
            if color_category == "custom" and custom_colors:
                # Build custom color category dynamically
                entity_styles = {
                    "person": {
                        "shape": "rectangle",
                        "fill_color": custom_colors.get("person_color", "#FF6B6B"),
                        "stroke_color": self._darken_color(custom_colors.get("person_color", "#FF6B6B")),
                        "text_color": custom_colors.get("custom_font_color", "#333333"),
                        "icon": ""
                    },
                    "investor": {
                        "shape": "rectangle",
                        "fill_color": custom_colors.get("investor_color", "#F8BBD9"),
                        "stroke_color": self._darken_color(custom_colors.get("investor_color", "#F8BBD9")),
                        "text_color": custom_colors.get("custom_font_color", "#333333"),
                        "icon": ""
                    },
                    "trust": {
                        "shape": "rectangle",
                        "fill_color": custom_colors.get("investor_color", "#F8BBD9"),
                        "stroke_color": self._darken_color(custom_colors.get("investor_color", "#F8BBD9")),
                        "text_color": custom_colors.get("custom_font_color", "#333333"),
                        "icon": ""
                    },
                    "foundation": {
                        "shape": "rectangle",
                        "fill_color": custom_colors.get("foundation_color", "#96CEB4"),
                        "stroke_color": self._darken_color(custom_colors.get("foundation_color", "#96CEB4")),
                        "text_color": custom_colors.get("custom_font_color", "#333333"),
                        "icon": ""
                    },
                    "company": {
                        "shape": "rectangle",
                        "fill_color": custom_colors.get("company_color", "#4A90E2"),
                        "stroke_color": self._darken_color(custom_colors.get("company_color", "#4A90E2")),
                        "text_color": custom_colors.get("custom_font_color", "#333333"),
                        "icon": ""
                    },
                    "focus_company": {
                        "shape": "rectangle",
                        "fill_color": custom_colors.get("focus_company_color", "#FFD93D"),  # Configurable focus company color
                        "stroke_color": custom_colors.get("focus_company_border", "#FF0000"),  # Configurable border color
                        "stroke_width": 4,  # Thicker border for focus company
                        "text_color": "#333333",  # Dark text for contrast
                        "icon": ""
                    }
                }
                # Background is always transparent
                background_color = "transparent"
            else:
                entity_styles = COLOR_CATEGORIES.get(color_category, COLOR_CATEGORIES["professional"])
                # Override focus company styling if provided in custom_colors
                if custom_colors and "focus_company" in entity_styles:
                    if "focus_company_color" in custom_colors:
                        entity_styles["focus_company"]["fill_color"] = custom_colors["focus_company_color"]
                    if "focus_company_border" in custom_colors:
                        entity_styles["focus_company"]["stroke_color"] = custom_colors["focus_company_border"]
                    if "border_color" in custom_colors:
                        # Apply border color to all companies
                        for entity_type in entity_styles:
                            if entity_type != "focus_company":
                                entity_styles[entity_type]["stroke_color"] = custom_colors["border_color"]
                background_color = "transparent"  # Always transparent
            
            # Calculate positions and hierarchy
            company_positions = {}
            max_level = 0
            
            # Find root companies (no parents)
            root_companies = self._find_root_companies(companies_data)
            
            # Calculate levels and positions
            max_level = self._calculate_hierarchy_levels(companies_data, root_companies, company_positions)
            
            # Generate SVG content
            svg_content = self._generate_svg_header(max_level, entity_styles, background_color)
            
            # Group companies by level
            level_companies = self._group_companies_by_level(company_positions)
            
            # Draw connections first (so they appear behind boxes)
            svg_content += self._generate_connections(companies_data, company_positions, level_companies)
            
            # Draw company boxes with color category and focus company
            svg_content += self._generate_company_boxes(companies_data, level_companies, entity_styles, focus_company)
            
            # Legend removed for cleaner look
            
            svg_content += '</svg>'
            
            return svg_content
            
        except Exception as e:
            self.logger.error(f"Error generating SVG diagram: {e}")
            return self._generate_error_svg(str(e))
    
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
    
    def _generate_svg_header(self, max_level: int, entity_styles: Dict[str, Any], background_color: str) -> str:
        """Generate the SVG header with styles and definitions"""
        svg_height = SVG_HEIGHT_BASE + (max_level + 1) * SVG_HEIGHT_PER_LEVEL  # No legend space needed
        
        # Check if this is minimal style (no fill colors)
        is_minimal = all(style["fill_color"] == "none" for style in entity_styles.values())
        
        # Generate dynamic gradients based on color category
        gradient_defs = ""
        if not is_minimal:
            for entity_type, style in entity_styles.items():
                fill_color = style["fill_color"]
                stroke_color = style["stroke_color"]
                gradient_id = f"{entity_type}Gradient"
                gradient_defs += f'''
        <linearGradient id="{gradient_id}" x1="0%" y1="0%" x2="100%" y2="100%">
            <stop offset="0%" style="stop-color:{fill_color};stop-opacity:1" />
            <stop offset="100%" style="stop-color:{stroke_color};stop-opacity:1" />
        </linearGradient>'''
        
        return f'''<?xml version="1.0" encoding="UTF-8"?>
<svg width="{SVG_WIDTH}" height="{svg_height}" xmlns="http://www.w3.org/2000/svg">
    <defs>
        <marker id="arrowhead" markerWidth="6" markerHeight="5" 
                refX="5" refY="2.5" orient="auto">
            <polygon points="0 0, 6 2.5, 0 5" fill="#999999" />
        </marker>
        <marker id="majority-arrow" markerWidth="6" markerHeight="5" 
                refX="5" refY="2.5" orient="auto">
            <polygon points="0 0, 6 2.5, 0 5" fill="#999999" />
        </marker>
        <marker id="minority-arrow" markerWidth="6" markerHeight="5" 
                refX="5" refY="2.5" orient="auto">
            <polygon points="0 0, 6 2.5, 0 5" fill="#999999" />
        </marker>
        <marker id="joint-arrow" markerWidth="6" markerHeight="5" 
                refX="5" refY="2.5" orient="auto">
            <polygon points="0 0, 6 2.5, 0 5" fill="#999999" />
        </marker>
        
        <!-- Dynamic gradients based on color category -->{gradient_defs}
        
        <style>
            .entity-text {{
                font-family: 'Segoe UI', Arial, sans-serif;
                font-size: 9px;
                font-weight: 600;
                text-anchor: middle;
                dominant-baseline: middle;
            }}
            .percentage-text {{
                font-family: 'Segoe UI', Arial, sans-serif;
                font-size: 12px;
                font-weight: bold;
                text-anchor: middle;
                dominant-baseline: middle;
            }}
        </style>
    </defs>
    
    <!-- Background -->
    <rect width="{SVG_WIDTH}" height="{svg_height}" fill="{background_color}"/>
'''
    
    def _generate_connections(self, companies_data: Dict[str, Any], company_positions: Dict[str, int], level_companies: Dict[int, list]) -> str:
        """Generate connection lines between companies with ownership styling"""
        svg_content = ""
        
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
                
                if parent_id in company_positions and company_id in company_positions:
                    connection_svg = self._generate_single_connection(
                        parent_id, company_id, company_positions, level_companies, ownership_percentage, companies_data
                    )
                    svg_content += connection_svg
        
        return svg_content
    
    def _generate_single_connection(self, parent_id: str, child_id: str, company_positions: Dict[str, int], 
                                  level_companies: Dict[int, list], ownership_percentage: Optional[float] = None, 
                                  companies_data: Dict[str, Any] = None) -> str:
        """Generate a single connection line between parent and child with ownership styling"""
        parent_level = company_positions[parent_id]
        child_level = company_positions[child_id]
        
        # Calculate positions
        parent_companies_in_level = level_companies[parent_level]
        child_companies_in_level = level_companies[child_level]
        
        parent_index = parent_companies_in_level.index(parent_id)
        child_index = child_companies_in_level.index(child_id)
        
        # Calculate box positions
        parent_pos = self._calculate_box_position(parent_level, parent_index, parent_companies_in_level)
        child_pos = self._calculate_box_position(child_level, child_index, child_companies_in_level)
        
        # Sanitize ownership percentage: treat missing or negative as None; parse strings like "60%"
        sanitized_percentage: Optional[float] = None
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
                    sanitized_percentage = parsed
            except Exception:
                sanitized_percentage = None

        # Determine connection style based on sanitized ownership percentage
        connection_style = self._get_connection_style(sanitized_percentage)
        
        # Get entity types to determine correct connection points
        parent_entity_type = companies_data.get(parent_id, {}).get('type', 'company')
        child_entity_type = companies_data.get(child_id, {}).get('type', 'company')
        
        parent_radius = self._get_entity_radius(parent_entity_type)
        child_radius = self._get_entity_radius(child_entity_type)
        
        # Draw connection line from bottom of parent to top of child
        svg_content = f'    <line x1="{parent_pos["x"]}" y1="{parent_pos["y"] + parent_radius}" x2="{child_pos["x"]}" y2="{child_pos["y"] - child_radius}" '
        svg_content += f'stroke="{connection_style["stroke_color"]}" stroke-width="{connection_style["stroke_width"]}" '
        if connection_style["stroke_dasharray"] != "none":
            svg_content += f'stroke-dasharray="{connection_style["stroke_dasharray"]}" '
        svg_content += f'marker-end="url(#{self._get_arrow_marker(sanitized_percentage)})"/>\n'
        
        # Add ownership percentage label if available
        if sanitized_percentage is not None:
            label_x = (parent_pos["x"] + child_pos["x"]) / 2
            label_y = (parent_pos["y"] + child_pos["y"]) / 2
            svg_content += f'    <text x="{label_x}" y="{label_y - 5}" class="percentage-text" fill="#000000">{sanitized_percentage}%</text>\n'
        
        return svg_content
    
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
    
    def _get_arrow_marker(self, ownership_percentage: Optional[float]) -> str:
        """Get arrow marker based on ownership percentage"""
        if ownership_percentage is None:
            return "arrowhead"
        
        if ownership_percentage >= OWNERSHIP_THRESHOLDS["majority"]:
            return "majority-arrow"
        elif ownership_percentage >= OWNERSHIP_THRESHOLDS["minority"]:
            return "minority-arrow"
        else:
            return "arrowhead"
    
    def _calculate_box_position(self, level: int, index: int, companies_in_level: list) -> Dict[str, int]:
        """Calculate the position of a box in the diagram"""
        level_width = len(companies_in_level) * (BOX_WIDTH + BOX_MARGIN) - BOX_MARGIN
        start_x = (SVG_WIDTH - level_width) // 2
        
        x = start_x + index * (BOX_WIDTH + BOX_MARGIN) + BOX_WIDTH // 2
        y = 80 + level * SVG_HEIGHT_PER_LEVEL + BOX_HEIGHT // 2
        
        return {"x": x, "y": y}
    
    def _generate_company_boxes(self, companies_data: Dict[str, Any], level_companies: Dict[int, list], entity_styles: Dict[str, Any], focus_company: str = "") -> str:
        """Generate company boxes for the diagram with different shapes and colors"""
        svg_content = ""
        
        for level in sorted(level_companies.keys()):
            companies_in_level = level_companies[level]
            level_width = len(companies_in_level) * (BOX_WIDTH + BOX_MARGIN) - BOX_MARGIN
            start_x = (SVG_WIDTH - level_width) // 2
            
            for i, company_id in enumerate(companies_in_level):
                company_data = companies_data[company_id]
                company_name = company_data.get('name', company_id)
                entity_type = company_data.get('type', 'company')
                ownership_percentage = company_data.get('ownership_percentage', None)
                
                x = start_x + i * (BOX_WIDTH + BOX_MARGIN)
                y = 80 + level * SVG_HEIGHT_PER_LEVEL
                
                # Check if this is the focus company
                if focus_company and company_id == focus_company:
                    # Use focus company style
                    entity_style = entity_styles.get("focus_company", entity_styles["company"])
                else:
                    # Get entity style from the provided color category
                    entity_style = entity_styles.get(entity_type, entity_styles["company"])
                
                # Generate shape based on entity type
                shape_svg = self._generate_entity_shape(
                    x, y, entity_style, company_name, entity_type, ownership_percentage
                )
                svg_content += shape_svg
        
        return svg_content
    
    def _generate_entity_shape(self, x: int, y: int, entity_style: Dict[str, Any], 
                              company_name: str, entity_type: str, ownership_percentage: Optional[float] = None) -> str:
        """Generate SVG for entity shape - all shapes are now rectangles"""
        fill_color = entity_style["fill_color"]
        stroke_color = entity_style["stroke_color"]
        text_color = entity_style["text_color"]
        
        # Show complete names without truncation
        display_name = company_name
        
        svg_content = ""
        
        # Determine fill style - use gradient for filled shapes, solid color for minimal
        if fill_color == "none":
            fill_style = fill_color  # "none" for transparent
        else:
            fill_style = f'url(#{self._get_gradient_id(entity_style, entity_type)})'
        
        # All shapes are now rectangles
        stroke_width = entity_style.get("stroke_width", 2)  # Default stroke width is 2, focus company uses 4
        svg_content += f'    <rect x="{x}" y="{y}" width="{BOX_WIDTH}" height="{BOX_HEIGHT}" '
        svg_content += f'fill="{fill_style}" stroke="{stroke_color}" stroke-width="{stroke_width}" rx="8" ry="8"/>\n'
        
        # Add name (centered)
        svg_content += f'    <text x="{x + BOX_WIDTH//2}" y="{y + BOX_HEIGHT//2 + 4}" class="entity-text" fill="{text_color}">{display_name}</text>\n'
        
        return svg_content
    
    def _get_gradient_id(self, entity_style: Dict[str, Any], entity_type: str) -> str:
        """Get gradient ID based on entity type"""
        return f"{entity_type}Gradient"
    
    def _get_entity_radius(self, entity_type: str) -> int:
        """Get the radius/height offset for connection lines - all shapes are now rectangles"""
        # For all rectangles, use half the box height
        return BOX_HEIGHT // 2
    
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
    <rect width="400" height="200" fill="#f8f9fa"/>
    <text x='200' y='100' text-anchor='middle' font-family='Segoe UI, Arial' font-size='14' fill='#e74c3c'>
        Error generating diagram: {error_message}
    </text>
</svg>'''
