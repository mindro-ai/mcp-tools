"""Constants and configuration for MCP Drawing Client"""

# SVG generation constants
SVG_WIDTH = 900
SVG_HEIGHT_BASE = 200
SVG_HEIGHT_PER_LEVEL = 120
BOX_WIDTH = 180
BOX_HEIGHT = 70
BOX_MARGIN = 20

# Positioning constants
Y_OFFSET_BASE = 80

# Font sizes
FONT_SIZE_NORMAL = 12
FONT_SIZE_ERROR = 14

# Error SVG dimensions
ERROR_SVG_WIDTH = 400
ERROR_SVG_HEIGHT = 200

# Color manipulation
COLOR_DARKENING_FACTOR = 0.8

# Line widths
FOCUS_COMPANY_LINE_WIDTH = 4
REGULAR_COMPANY_LINE_WIDTH = 2

# Default color constants (to avoid magic numbers)
DEFAULT_COLORS = {
    "person_color": "#FF6B6B",
    "investor_color": "#F8BBD9", 
    "trust_color": "#F8BBD9",
    "foundation_color": "#96CEB4",
    "company_color": "#4A90E2",
    "custom_font_color": "#333333",
    "focus_company_color": "#FFD93D",
    "focus_company_stroke": "#FF0000",
    "error_background": "#f8f9fa",
    "error_text": "#e74c3c",
    "person_stroke": "#CC5555",
    "investor_stroke": "#E1BEE7",
    "foundation_stroke": "#7AB894",
    "company_stroke": "#2E5C8A",
    "connection_stroke": "#999999"
}

# Entity types for styling
ENTITY_TYPES = {
    "person": "person-box",
    "investor": "investor-box", 
    "trust": "trust-box",
    "foundation": "foundation-box",
    "company": "company-box"
}

# Default entity styles (will be overridden by custom colors)
ENTITY_STYLES = {
    "person": {
        "shape": "rectangle",
        "fill_color": DEFAULT_COLORS["person_color"],
        "stroke_color": DEFAULT_COLORS["person_stroke"],
        "text_color": DEFAULT_COLORS["custom_font_color"],
        "icon": ""
    },
    "investor": {
        "shape": "rectangle",
        "fill_color": DEFAULT_COLORS["investor_color"],
        "stroke_color": DEFAULT_COLORS["investor_stroke"],
        "text_color": DEFAULT_COLORS["custom_font_color"],
        "icon": ""
    },
    "trust": {
        "shape": "rectangle",
        "fill_color": DEFAULT_COLORS["trust_color"],
        "stroke_color": DEFAULT_COLORS["investor_stroke"],
        "text_color": DEFAULT_COLORS["custom_font_color"],
        "icon": ""
    },
    "foundation": {
        "shape": "rectangle",
        "fill_color": DEFAULT_COLORS["foundation_color"],
        "stroke_color": DEFAULT_COLORS["foundation_stroke"],
        "text_color": DEFAULT_COLORS["custom_font_color"],
        "icon": ""
    },
    "company": {
        "shape": "rectangle",
        "fill_color": DEFAULT_COLORS["company_color"],
        "stroke_color": DEFAULT_COLORS["company_stroke"],
        "text_color": DEFAULT_COLORS["custom_font_color"],
        "icon": ""
    },
    "focus_company": {
        "shape": "rectangle",
        "fill_color": DEFAULT_COLORS["focus_company_color"],
        "stroke_color": DEFAULT_COLORS["focus_company_stroke"],
        "stroke_width": 4,
        "text_color": DEFAULT_COLORS["custom_font_color"],
        "icon": ""
    }
}

# Connection line styles
CONNECTION_STYLES = {
    "default": {
        "stroke_color": DEFAULT_COLORS["connection_stroke"],  # Lighter gray
        "stroke_width": 2,
        "stroke_dasharray": "none"
    },
    "majority_ownership": {
        "stroke_color": DEFAULT_COLORS["connection_stroke"],  # Lighter gray
        "stroke_width": 3,
        "stroke_dasharray": "none"
    },
    "minority_ownership": {
        "stroke_color": DEFAULT_COLORS["connection_stroke"],  # Lighter gray
        "stroke_width": 2,
        "stroke_dasharray": "5,5"
    },
    "joint_venture": {
        "stroke_color": DEFAULT_COLORS["connection_stroke"],  # Lighter gray
        "stroke_width": 2,
        "stroke_dasharray": "10,5"
    }
}

# Ownership percentage thresholds
OWNERSHIP_THRESHOLDS = {
    "majority": 50.0,  # 50% or more
    "minority": 25.0,  # 25% or more but less than 50%
    "small": 10.0      # 10% or more but less than 25%
}
