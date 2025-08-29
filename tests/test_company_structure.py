"""Tests for the company structure generator functionality"""

import pytest
import sys
import os

# Add the project root to the path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)


def test_import_works():
    """Test that the module can be imported"""
    try:
        # Mock the heavy dependencies
        import unittest.mock as mock
        
        with mock.patch.dict('sys.modules', {
            'mcp': mock.Mock(),
            'mcp.server': mock.Mock(),
            'mcp.server.fastmcp': mock.Mock(),
            'plotly': mock.Mock(),
            'plotly.graph_objects': mock.Mock(),
            'plotly.subplots': mock.Mock(),
        }):
            from mcp_tools.drawings.company_structure import CompanyStructureGenerator
            assert CompanyStructureGenerator is not None
            print("✓ Import successful")
    except Exception as e:
        pytest.fail(f"Import failed: {e}")


def test_class_creation():
    """Test that the class can be instantiated"""
    try:
        import unittest.mock as mock
        
        with mock.patch.dict('sys.modules', {
            'mcp': mock.Mock(),
            'mcp.server': mock.Mock(),
            'mcp.server.fastmcp': mock.Mock(),
            'plotly': mock.Mock(),
            'plotly.graph_objects': mock.Mock(),
            'plotly.subplots': mock.Mock(),
        }):
            from mcp_tools.drawings.company_structure import CompanyStructureGenerator
            generator = CompanyStructureGenerator()
            assert generator is not None
            assert hasattr(generator, 'generate_company_diagram')
            print("✓ Class creation successful")
    except Exception as e:
        pytest.fail(f"Class creation failed: {e}")


def test_method_exists():
    """Test that the main method exists"""
    try:
        import unittest.mock as mock
        
        with mock.patch.dict('sys.modules', {
            'mcp': mock.Mock(),
            'mcp.server': mock.Mock(),
            'mcp.server.fastmcp': mock.Mock(),
            'plotly': mock.Mock(),
            'plotly.graph_objects': mock.Mock(),
            'plotly.subplots': mock.Mock(),
        }):
            from mcp_tools.drawings.company_structure import CompanyStructureGenerator
            generator = CompanyStructureGenerator()
            
            # Check that the main method exists
            assert hasattr(generator, 'generate_company_diagram')
            assert callable(getattr(generator, 'generate_company_diagram'))
            print("✓ Method exists")
    except Exception as e:
        pytest.fail(f"Method check failed: {e}")


def test_constants_import():
    """Test that constants can be imported"""
    try:
        from mcp_tools.drawings.constants import (
            SVG_WIDTH, SVG_HEIGHT_BASE, SVG_HEIGHT_PER_LEVEL,
            BOX_WIDTH, BOX_HEIGHT, BOX_MARGIN, DEFAULT_COLORS
        )
        assert SVG_WIDTH > 0
        assert SVG_HEIGHT_BASE > 0
        assert BOX_WIDTH > 0
        assert BOX_HEIGHT > 0
        assert isinstance(DEFAULT_COLORS, dict)
        assert len(DEFAULT_COLORS) > 0
        print("✓ Constants import successful")
    except Exception as e:
        pytest.fail(f"Constants import failed: {e}")


def test_file_structure():
    """Test that the file structure is correct"""
    import os
    
    # Get the absolute path to the project root
    current_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(current_dir)
    
    # Check that the main file exists
    company_structure_file = os.path.join(project_root, 'mcp_tools', 'drawings', 'company_structure.py')
    assert os.path.exists(company_structure_file), f"File not found: {company_structure_file}"
    
    # Check that constants file exists
    constants_file = os.path.join(project_root, 'mcp_tools', 'drawings', 'constants.py')
    assert os.path.exists(constants_file), f"File not found: {constants_file}"
    
    print("✓ File structure correct")


def test_renaming_complete():
    """Test that the renaming was completed correctly"""
    import os
    
    # Get the absolute path to the project root
    current_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(current_dir)
    
    # Check that old file doesn't exist
    old_file = os.path.join(project_root, 'mcp_tools', 'drawings', 'svg_generator.py')
    assert not os.path.exists(old_file), f"Old file still exists: {old_file}"
    
    # Check that new file exists
    new_file = os.path.join(project_root, 'mcp_tools', 'drawings', 'company_structure.py')
    assert os.path.exists(new_file), f"New file not found: {new_file}"
    
    print("✓ Renaming completed successfully")
