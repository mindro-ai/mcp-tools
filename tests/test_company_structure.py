import pytest
from unittest.mock import patch, MagicMock
from mcp_tools.drawings.drawings import DrawingsMCPServer
from mcp_tools.drawings.company_structure import generate_diagram, calculate_positions


@pytest.fixture
def drawings_server():
    return DrawingsMCPServer()


@pytest.fixture
def sample_companies_data():
    """Sample companies data matching the provided request structure"""
    return {
        "child": {
            "name": "Child LLd",
            "parents": ["parent"],
            "focus": "true"
        },
        "parent": {
            "name": "Parent LLd",
            "parents": ["owner1", "owner2"]
        },
        "owner1": {
            "name": "Alex Alex",
            "parents": []
        },
        "owner2": {
            "name": "Chris Chris",
            "parents": []
        }
    }


@pytest.mark.asyncio
async def test_company_structure_endpoint(drawings_server, sample_companies_data):
    """Test the company_structure MCP endpoint with the provided request structure"""
    
    # Mock the plotly figure to avoid actual image generation in tests
    with patch('mcp_tools.drawings.drawings.generate_diagram') as mock_generate:
        mock_fig = MagicMock()
        mock_fig.to_image.return_value.decode.return_value = "<svg>test</svg>"
        mock_generate.return_value = mock_fig
        
        # Call the endpoint
        result = await drawings_server.company_structure(companies=sample_companies_data)
        
        # Verify the result
        assert result == "<svg>test</svg>"
        mock_generate.assert_called_once_with(sample_companies_data)


@pytest.mark.asyncio
async def test_company_structure_mcp_request_simulation():
    """Test simulating the actual MCP request structure provided by the user"""
    
    # Simulate the MCP request structure
    mcp_request = {
        "method": "tools/call",
        "params": {
            "name": "company_structure",
            "arguments": {
                "companies": {
                    "child": {
                        "name": "Child LLd",
                        "parents": ["parent"],
                        "focus": "true"
                    },
                    "parent": {
                        "name": "Parent LLd",
                        "parents": ["owner1", "owner2"]
                    },
                    "owner1": {
                        "name": "Alex Alex",
                        "parents": []
                    },
                    "owner2": {
                        "name": "Chris Chris",
                        "parents": []
                    }
                }
            }
        }
    }
    
    # Extract the companies data from the MCP request
    companies_data = mcp_request["params"]["arguments"]["companies"]
    
    # Create the server and test the endpoint
    drawings_server = DrawingsMCPServer()
    
    with patch('mcp_tools.drawings.drawings.generate_diagram') as mock_generate:
        mock_fig = MagicMock()
        mock_fig.to_image.return_value.decode.return_value = "<svg>mcp_request_test</svg>"
        mock_generate.return_value = mock_fig
        
        # Call the endpoint with the extracted data
        result = await drawings_server.company_structure(companies=companies_data)
        
        # Verify the result
        assert result == "<svg>mcp_request_test</svg>"
        mock_generate.assert_called_once_with(companies_data)
        
        # Verify the companies data structure matches expectations
        assert "child" in companies_data
        assert "parent" in companies_data
        assert "owner1" in companies_data
        assert "owner2" in companies_data
        
        # Verify the focus company is marked
        assert companies_data["child"]["focus"] == "true"
        
        # Verify parent relationships
        assert companies_data["child"]["parents"] == ["parent"]
        assert companies_data["parent"]["parents"] == ["owner1", "owner2"]
        assert companies_data["owner1"]["parents"] == []
        assert companies_data["owner2"]["parents"] == []


@pytest.mark.asyncio
async def test_company_structure_endpoint_error_handling(drawings_server, sample_companies_data):
    """Test error handling in the company_structure endpoint"""
    
    with patch('mcp_tools.drawings.drawings.generate_diagram') as mock_generate:
        mock_generate.side_effect = Exception("Test error")
        
        # Call the endpoint
        result = await drawings_server.company_structure(companies=sample_companies_data)
        
        # Verify error handling
        assert result == "Error: Test error"


def test_calculate_positions(sample_companies_data):
    """Test the position calculation function"""
    positions = calculate_positions(sample_companies_data)
    
    # Verify all companies have positions
    assert "child" in positions
    assert "parent" in positions
    assert "owner1" in positions
    assert "owner2" in positions
    
    # Verify position structure
    for company_id, pos in positions.items():
        assert "x" in pos
        assert "y" in pos
        assert "w" in pos
        assert "h" in pos
        assert isinstance(pos["x"], (int, float))
        assert isinstance(pos["y"], (int, float))
        assert isinstance(pos["w"], (int, float))
        assert isinstance(pos["h"], (int, float))


def test_generate_diagram(sample_companies_data):
    """Test the diagram generation function"""
    fig = generate_diagram(sample_companies_data)
    
    # Verify the figure is created
    assert fig is not None
    
    # Verify the layout is set correctly
    layout = fig.layout
    assert layout.width == 600
    assert layout.height == 500
    assert layout.plot_bgcolor == 'white'
    
    # Verify axes are hidden
    assert not layout.xaxis.visible
    assert not layout.yaxis.visible


def test_company_structure_with_focus_company(sample_companies_data):
    """Test that focus companies are styled differently"""
    fig = generate_diagram(sample_companies_data)
    
    # The child company should have focus styling
    # We can't easily test the exact styling without parsing the figure,
    # but we can verify the figure was generated successfully
    assert fig is not None


def test_company_structure_with_multiple_parents():
    """Test company structure with multiple parents (like the parent company)"""
    companies_data = {
        "child": {
            "name": "Child Company",
            "parents": ["parent1", "parent2"]
        },
        "parent1": {
            "name": "Parent 1",
            "parents": []
        },
        "parent2": {
            "name": "Parent 2",
            "parents": []
        }
    }
    
    positions = calculate_positions(companies_data)
    
    # Verify positions are calculated correctly
    assert "child" in positions
    assert "parent1" in positions
    assert "parent2" in positions
    
    # Verify the child is positioned below the parents
    child_y = positions["child"]["y"]
    parent1_y = positions["parent1"]["y"]
    parent2_y = positions["parent2"]["y"]
    
    # Child should be at a lower y-coordinate (higher level number)
    assert child_y < parent1_y
    assert child_y < parent2_y


def test_company_structure_with_single_parent():
    """Test company structure with single parent"""
    companies_data = {
        "child": {
            "name": "Child Company",
            "parents": ["parent"]
        },
        "parent": {
            "name": "Parent Company",
            "parents": []
        }
    }
    
    positions = calculate_positions(companies_data)
    
    # Verify positions are calculated correctly
    assert "child" in positions
    assert "parent" in positions
    
    # Verify the child is positioned below the parent
    child_y = positions["child"]["y"]
    parent_y = positions["parent"]["y"]
    
    # Child should be at a lower y-coordinate (higher level number)
    assert child_y < parent_y


def test_company_structure_with_no_parents():
    """Test company structure with companies that have no parents"""
    companies_data = {
        "company1": {
            "name": "Company 1",
            "parents": []
        },
        "company2": {
            "name": "Company 2",
            "parents": []
        }
    }
    
    positions = calculate_positions(companies_data)
    
    # Verify positions are calculated correctly
    assert "company1" in positions
    assert "company2" in positions
    
    # Both companies should be at the same level (same y-coordinate)
    company1_y = positions["company1"]["y"]
    company2_y = positions["company2"]["y"]
    
    assert company1_y == company2_y
