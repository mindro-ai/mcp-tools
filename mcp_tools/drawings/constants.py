"""Constants and configuration for MCP Drawing Client"""

# SVG generation constants
SVG_WIDTH = 900
SVG_HEIGHT_BASE = 200
SVG_HEIGHT_PER_LEVEL = 120
BOX_WIDTH = 180
BOX_HEIGHT = 70
BOX_MARGIN = 20

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
        "fill_color": "#FF6B6B",
        "stroke_color": "#CC5555",
        "text_color": "#333333",
        "icon": ""
    },
    "investor": {
        "shape": "rectangle",
        "fill_color": "#F8BBD9",
        "stroke_color": "#E1BEE7",
        "text_color": "#333333",
        "icon": ""
    },
    "trust": {
        "shape": "rectangle",
        "fill_color": "#F8BBD9",
        "stroke_color": "#E1BEE7",
        "text_color": "#333333",
        "icon": ""
    },
    "foundation": {
        "shape": "rectangle",
        "fill_color": "#96CEB4",
        "stroke_color": "#7AB894",
        "text_color": "#333333",
        "icon": ""
    },
    "company": {
        "shape": "rectangle",
        "fill_color": "#4A90E2",
        "stroke_color": "#2E5C8A",
        "text_color": "#333333",
        "icon": ""
    },
    "focus_company": {
        "shape": "rectangle",
        "fill_color": "#FFD93D",
        "stroke_color": "#FF0000",
        "stroke_width": 4,
        "text_color": "#333333",
        "icon": ""
    }
}

# Connection line styles
CONNECTION_STYLES = {
    "default": {
        "stroke_color": "#999999",  # Lighter gray
        "stroke_width": 2,
        "stroke_dasharray": "none"
    },
    "majority_ownership": {
        "stroke_color": "#999999",  # Lighter gray
        "stroke_width": 3,
        "stroke_dasharray": "none"
    },
    "minority_ownership": {
        "stroke_color": "#999999",  # Lighter gray
        "stroke_width": 2,
        "stroke_dasharray": "5,5"
    },
    "joint_venture": {
        "stroke_color": "#999999",  # Lighter gray
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
