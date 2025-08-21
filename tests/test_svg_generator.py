"""Tests for the SVG generator functionality"""

import pytest
import sys
import os

# Add the project root to the path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

# Mock the MCP dependencies to avoid import errors
import unittest.mock as mock
with mock.patch.dict('sys.modules', {
    'mcp': mock.Mock(),
    'mcp.server': mock.Mock(),
    'mcp.server.fastmcp': mock.Mock(),
}):
    # Now we can import the SVG generator
    from mcp_tools.drawings.svg_generator import SVGGenerator


@pytest.fixture
def svg_generator():
    return SVGGenerator()


@pytest.fixture
def sample_companies_data():
    """Sample companies data for testing"""
    return {
        "mindro": {
            "name": "Mindro BV",
            "type": "company",
            "parents": []
        },
        "subsidiary1": {
            "name": "Mindro Subsidiary 1",
            "type": "company", 
            "parents": ["mindro"]
        },
        "subsidiary2": {
            "name": "Mindro Subsidiary 2",
            "type": "company",
            "parents": ["mindro"]
        }
    }


def test_svg_generator_creation(svg_generator):
    """Test that SVG generator can be created"""
    assert svg_generator is not None
    assert hasattr(svg_generator, 'generate_company_diagram')


def test_basic_svg_generation(svg_generator, sample_companies_data):
    """Test basic SVG generation"""
    svg_content = svg_generator.generate_company_diagram(sample_companies_data)
    
    assert svg_content is not None
    assert isinstance(svg_content, str)
    assert len(svg_content) > 0
    assert svg_content.startswith('<?xml version="1.0" encoding="UTF-8"?>')
    assert '<svg' in svg_content
    assert '</svg>' in svg_content


def test_svg_with_focus_company(svg_generator, sample_companies_data):
    """Test SVG generation with focus company"""
    svg_content = svg_generator.generate_company_diagram(
        sample_companies_data,
        focus_company="mindro"
    )
    
    assert svg_content is not None
    assert isinstance(svg_content, str)
    assert len(svg_content) > 0
    assert svg_content.startswith('<?xml version="1.0" encoding="UTF-8"?>')


def test_svg_with_different_color_categories(svg_generator, sample_companies_data):
    """Test SVG generation with different color categories"""
    color_categories = ["professional", "vibrant", "pastel", "monochrome", "minimal"]
    
    for category in color_categories:
        svg_content = svg_generator.generate_company_diagram(
            sample_companies_data,
            color_category=category
        )
        
        assert svg_content is not None
        assert isinstance(svg_content, str)
        assert len(svg_content) > 0
        assert svg_content.startswith('<?xml version="1.0" encoding="UTF-8"?>')


def test_svg_with_custom_colors(svg_generator, sample_companies_data):
    """Test SVG generation with custom colors"""
    custom_colors = {
        "company_color": "#FF6B6B",
        "person_color": "#4ECDC4",
        "focus_company_color": "#FFD93D",
        "focus_company_border": "#FF0000"
    }
    
    svg_content = svg_generator.generate_company_diagram(
        sample_companies_data,
        color_category="custom",
        custom_colors=custom_colors,
        focus_company="mindro"
    )
    
    assert svg_content is not None
    assert isinstance(svg_content, str)
    assert len(svg_content) > 0
    assert svg_content.startswith('<?xml version="1.0" encoding="UTF-8"?>')


def test_svg_with_ownership_percentages(svg_generator):
    """Test SVG generation with ownership percentages"""
    companies_data = {
        "child": {
            "name": "Child Ltd",
            "type": "company",
            "parents": [
                {"id": "parent1", "percentage": 60},
                {"id": "parent2", "percentage": "40%"}
            ]
        },
        "parent1": {
            "name": "Parent 1",
            "type": "company",
            "parents": []
        },
        "parent2": {
            "name": "Parent 2",
            "type": "company",
            "parents": []
        }
    }
    
    svg_content = svg_generator.generate_company_diagram(companies_data)
    
    assert svg_content is not None
    assert isinstance(svg_content, str)
    assert len(svg_content) > 0
    assert svg_content.startswith('<?xml version="1.0" encoding="UTF-8"?>')


def test_svg_error_handling(svg_generator):
    """Test error handling with invalid data"""
    # Test with empty data
    svg_content = svg_generator.generate_company_diagram({})
    assert svg_content is not None
    assert isinstance(svg_content, str)
    assert len(svg_content) > 0
    
    # Test with None data
    svg_content = svg_generator.generate_company_diagram(None)
    assert svg_content is not None
    assert isinstance(svg_content, str)
    assert len(svg_content) > 0


def test_svg_with_different_entity_types(svg_generator):
    """Test SVG generation with different entity types"""
    companies_data = {
        "company": {
            "name": "Test Company",
            "type": "company",
            "parents": []
        },
        "person": {
            "name": "John Doe",
            "type": "person",
            "parents": []
        },
        "investor": {
            "name": "Investor Corp",
            "type": "investor",
            "parents": []
        },
        "trust": {
            "name": "Family Trust",
            "type": "trust",
            "parents": []
        },
        "foundation": {
            "name": "Charity Foundation",
            "type": "foundation",
            "parents": []
        }
    }
    
    svg_content = svg_generator.generate_company_diagram(companies_data)
    
    assert svg_content is not None
    assert isinstance(svg_content, str)
    assert len(svg_content) > 0
    assert svg_content.startswith('<?xml version="1.0" encoding="UTF-8"?>')
