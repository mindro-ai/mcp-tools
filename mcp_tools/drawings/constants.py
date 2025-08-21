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

# Color categories for different diagram styles
COLOR_CATEGORIES = {
    "vibrant": {
        "person": {
            "shape": "rectangle",
            "fill_color": "#FF6B6B",  # Bright coral red
            "stroke_color": "#CC5555",
            "text_color": "white",
            "icon": ""
        },
        "investor": {
            "shape": "rectangle",
            "fill_color": "#4ECDC4",  # Bright turquoise
            "stroke_color": "#3DA89A",
            "text_color": "white",
            "icon": ""
        },
        "trust": {
            "shape": "rectangle",
            "fill_color": "#45B7D1",  # Bright sky blue
            "stroke_color": "#3699B5",
            "text_color": "white",
            "icon": ""
        },
        "foundation": {
            "shape": "rectangle",
            "fill_color": "#96CEB4",  # Bright mint green
            "stroke_color": "#7AB894",
            "text_color": "white",
            "icon": ""
        },
        "company": {
            "shape": "rectangle",
            "fill_color": "#4A90E2",  # Bright blue
            "stroke_color": "#2E5C8A",
            "text_color": "white",
            "icon": ""
        },
        "focus_company": {
            "shape": "rectangle",
            "fill_color": "#FFD93D",  # Bright yellow for focus
            "stroke_color": "#FF0000",  # Red border (will be overridden by config)
            "stroke_width": 4,  # Thicker border for focus company
            "text_color": "#333333",  # Dark text for contrast
            "icon": ""
        }
    },
    "professional": {
        "person": {
            "shape": "rectangle",
            "fill_color": "#34495E",  # Dark blue-gray
            "stroke_color": "#2C3E50",
            "text_color": "white",
            "icon": ""
        },
        "investor": {
            "shape": "rectangle",
            "fill_color": "#3498DB",  # Professional blue
            "stroke_color": "#2980B9",
            "text_color": "white",
            "icon": ""
        },
        "trust": {
            "shape": "rectangle",
            "fill_color": "#5D6D7E",  # Steel gray
            "stroke_color": "#4A5568",
            "text_color": "white",
            "icon": ""
        },
        "foundation": {
            "shape": "rectangle",
            "fill_color": "#85929E",  # Light gray
            "stroke_color": "#6C7B7F",
            "text_color": "white",
            "icon": ""
        },
        "company": {
            "shape": "rectangle",
            "fill_color": "#2E86AB",  # Corporate blue
            "stroke_color": "#1B4F72",
            "text_color": "white",
            "icon": ""
        },
        "focus_company": {
            "shape": "rectangle",
            "fill_color": "#E67E22",  # Orange for focus
            "stroke_color": "#FF0000",  # Red border (will be overridden by config)
            "stroke_width": 4,  # Thicker border for focus company
            "text_color": "white",
            "icon": ""
        }
    },
    "pastel": {
        "person": {
            "shape": "rectangle",
            "fill_color": "#FFF9C4",  # Soft yellow
            "stroke_color": "#FFF59D",
            "text_color": "#333333",
            "icon": ""
        },
        "investor": {
            "shape": "rectangle",
            "fill_color": "#BBDEFB",  # Soft blue
            "stroke_color": "#90CAF9",
            "text_color": "#333333",
            "icon": ""
        },
        "trust": {
            "shape": "rectangle",
            "fill_color": "#C8E6C9",  # Soft green
            "stroke_color": "#A5D6A7",
            "text_color": "#333333",
            "icon": ""
        },
        "foundation": {
            "shape": "rectangle",
            "fill_color": "#F8BBD9",  # Soft pink
            "stroke_color": "#E1BEE7",
            "text_color": "#333333",
            "icon": ""
        },
        "company": {
            "shape": "rectangle",
            "fill_color": "#E1BEE7",  # Soft purple
            "stroke_color": "#CE93D8",
            "text_color": "#333333",
            "icon": ""
        },
        "focus_company": {
            "shape": "rectangle",
            "fill_color": "#FFCCBC",  # Soft coral for focus
            "stroke_color": "#FF0000",  # Red border (will be overridden by config)
            "stroke_width": 4,  # Thicker border for focus company
            "text_color": "#333333",
            "icon": ""
        }
    },
    "monochrome": {
        "person": {
            "shape": "rectangle",
            "fill_color": "#2C3E50",  # Dark gray
            "stroke_color": "#1A252F",
            "text_color": "white",
            "icon": ""
        },
        "investor": {
            "shape": "rectangle",
            "fill_color": "#34495E",  # Medium dark gray
            "stroke_color": "#2C3E50",
            "text_color": "white",
            "icon": ""
        },
        "trust": {
            "shape": "rectangle",
            "fill_color": "#5D6D7E",  # Medium gray
            "stroke_color": "#4A5568",
            "text_color": "white",
            "icon": ""
        },
        "foundation": {
            "shape": "rectangle",
            "fill_color": "#85929E",  # Light gray
            "stroke_color": "#6C7B7F",
            "text_color": "white",
            "icon": ""
        },
        "company": {
            "shape": "rectangle",
            "fill_color": "#95A5A6",  # Lighter gray
            "stroke_color": "#7F8C8D",
            "text_color": "white",
            "icon": ""
        },
        "focus_company": {
            "shape": "rectangle",
            "fill_color": "#E74C3C",  # Red for focus in monochrome
            "stroke_color": "#FF0000",  # Red border (will be overridden by config)
            "stroke_width": 4,  # Thicker border for focus company
            "text_color": "white",
            "icon": ""
        }
    },
    "minimal": {
        "person": {
            "shape": "rectangle",
            "fill_color": "none",  # No fill
            "stroke_color": "#000000",  # Black stroke
            "text_color": "#000000",  # Black text
            "icon": ""
        },
        "investor": {
            "shape": "rectangle",
            "fill_color": "none",  # No fill
            "stroke_color": "#000000",  # Black stroke
            "text_color": "#000000",  # Black text
            "icon": ""
        },
        "trust": {
            "shape": "rectangle",
            "fill_color": "none",  # No fill
            "stroke_color": "#000000",  # Black stroke
            "text_color": "#000000",  # Black text
            "icon": ""
        },
        "foundation": {
            "shape": "rectangle",
            "fill_color": "none",  # No fill
            "stroke_color": "#000000",  # Black stroke
            "text_color": "#000000",  # Black text
            "icon": ""
        },
        "company": {
            "shape": "rectangle",
            "fill_color": "none",  # No fill
            "stroke_color": "#000000",  # Black stroke
            "text_color": "#000000",  # Black text
            "icon": ""
        },
        "focus_company": {
            "shape": "rectangle",
            "fill_color": "none",  # No fill
            "stroke_color": "#FF0000",  # Red stroke for focus (will be overridden by config)
            "stroke_width": 4,  # Thicker stroke for focus company
            "text_color": "#000000",  # Black text
            "icon": ""
        }
    },
    "custom": {
        "person": {
            "shape": "rectangle",
            "fill_color": "#FF6B6B",  # Custom color 2
            "stroke_color": "#CC5555",
            "text_color": "#333333",  # Custom font color
            "icon": ""
        },
        "investor": {
            "shape": "rectangle",
            "fill_color": "#F8BBD9",  # Custom color 4
            "stroke_color": "#E1BEE7",
            "text_color": "#333333",  # Custom font color
            "icon": ""
        },
        "trust": {
            "shape": "rectangle",
            "fill_color": "#F8BBD9",  # Custom color 4
            "stroke_color": "#E1BEE7",
            "text_color": "#333333",  # Custom font color
            "icon": ""
        },
        "foundation": {
            "shape": "rectangle",
            "fill_color": "#96CEB4",  # Custom color 3
            "stroke_color": "#7AB894",
            "text_color": "#333333",  # Custom font color
            "icon": ""
        },
        "company": {
            "shape": "rectangle",
            "fill_color": "#4A90E2",  # Custom color 1
            "stroke_color": "#2E5C8A",
            "text_color": "#333333",  # Custom font color
            "icon": ""
        },
        "focus_company": {
            "shape": "rectangle",
            "fill_color": "#FFD93D",  # Yellow for focus
            "stroke_color": "#FF0000",  # Red border (will be overridden by config)
            "stroke_width": 4,  # Thicker border for focus company
            "text_color": "#333333",  # Dark text for contrast
            "icon": ""
        }
    }
}

# Enhanced styling configuration for different entity types (default - professional)
ENTITY_STYLES = COLOR_CATEGORIES["professional"]

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
