# Drawing Tool - MCP Endpoint

This module provides a Model Context Protocol (MCP) endpoint for generating company structure diagrams as SVG files.

## Overview

The Drawing Tool endpoint allows you to create professional company structure diagrams with:
- **Company hierarchies** with parent-child relationships
- **Ownership percentages** displayed on connections
- **Custom color schemes** for different entity types
- **Focus company highlighting** for emphasis
- **Multiple entity types**: companies, investors, persons, foundations

## Features

✅ **SVG Generation**: Produces high-quality SVG diagrams  
✅ **Plotly Integration**: Uses Plotly for professional visualization  
✅ **Custom Colors**: Fully customizable color schemes  
✅ **Entity Types**: Support for companies, investors, persons, foundations  
✅ **Ownership Display**: Shows ownership percentages on connections  
✅ **Focus Highlighting**: Special styling for selected companies  
✅ **MCP Protocol**: Full MCP endpoint integration  

## Quick Start

### 1. Test the Endpoint Directly

```python
import asyncio
from mcp_tools.drawings.drawings import DrawingsMCPServer

# Create server instance
server = DrawingsMCPServer()

# Sample company data
companies = {
    "mindro": {
        "name": "Mindro BV",
        "type": "company",
        "parents": []
    },
    "subsidiary": {
        "name": "Mindro Subsidiary",
        "type": "company",
        "parents": [{"id": "mindro", "percentage": 100}]
    },
    "investor": {
        "name": "Tech Investor",
        "type": "investor",
        "parents": []
    }
}

# Custom colors
colors = {
    "company_color": "#4A90E2",
    "investor_color": "#F8BBD9",
    "focus_company_color": "#FFD93D"
}

# Generate SVG
result = await server.company_structure(
    companies=companies,
    custom_colors=colors,
    focus_company="mindro"
)

print(f"SVG generated: {len(result)} bytes")
```

### 2. Run the Full MCP Server

```bash
# Start the complete MCP server with all endpoints
poetry run python -m mcp_tools
```

This starts the server on `http://localhost:8080` with endpoints:
- `/health/sse` - Health monitoring
- `/drawings/sse` - Drawing tool endpoint

### 3. Quick Command Line Test

```bash
# Test the endpoint inline
poetry run python -c "
import asyncio
from mcp_tools.drawings.drawings import DrawingsMCPServer
server = DrawingsMCPServer()
companies = {'mindro': {'name': 'Mindro BV', 'type': 'company', 'parents': []}}
colors = {'company_color': '#4A90E2'}
result = asyncio.run(server.company_structure(companies, colors))
print(f'Success! Size: {len(result)} bytes')
"
```

## Input Format

### Company Data Structure

```python
companies = {
    "company_id": {
        "name": "Display Name",
        "type": "company|investor|person|foundation",
        "parents": [
            {
                "id": "parent_company_id",
                "percentage": 100  # Ownership percentage
            }
        ]
    }
}
```

### Color Configuration

```python
custom_colors = {
    "company_color": "#4A90E2",        # Blue for companies
    "person_color": "#FF6B6B",         # Red for persons
    "investor_color": "#F8BBD9",       # Pink for investors
    "foundation_color": "#96CEB4",     # Green for foundations
    "focus_company_color": "#FFD93D",  # Yellow for focus company
    "custom_font_color": "#333333"     # Dark gray for text
}
```

## Examples

### Simple Company Structure

```python
companies = {
    "parent": {
        "name": "Parent Company",
        "type": "company",
        "parents": []
    },
    "child": {
        "name": "Child Company",
        "type": "company",
        "parents": [{"id": "parent", "percentage": 100}]
    }
}
```

### Complex Structure with Multiple Entity Types

```python
companies = {
    "mindro": {
        "name": "Mindro BV",
        "type": "company",
        "parents": []
    },
    "subsidiary1": {
        "name": "Mindro Subsidiary 1",
        "type": "company",
        "parents": [{"id": "mindro", "percentage": 100}]
    },
    "subsidiary2": {
        "name": "Mindro Subsidiary 2",
        "type": "company",
        "parents": [{"id": "mindro", "percentage": 80}]
    },
    "investor": {
        "name": "Tech Investor Corp",
        "type": "investor",
        "parents": []
    },
    "person": {
        "name": "John Doe",
        "type": "person",
        "parents": []
    },
    "foundation": {
        "name": "Mindro Foundation",
        "type": "foundation",
        "parents": []
    }
}
```

## Testing

### Unit Tests

Run the test suite:

```bash
# Run all tests
poetry run pytest tests/

# Run drawing tool tests specifically
poetry run pytest tests/test_company_structure.py
```

### Manual Testing

1. **Test Import**:
   ```bash
   poetry run python -c "from mcp_tools.drawings.drawings import DrawingsMCPServer; print('Import successful')"
   ```

2. **Test Generator**:
   ```bash
   poetry run python -c "from mcp_tools.drawings.company_structure import CompanyStructureGenerator; gen = CompanyStructureGenerator(); print('Generator created')"
   ```

3. **Test Constants**:
   ```bash
   poetry run python -c "from mcp_tools.drawings.constants import DEFAULT_COLORS; print('Colors:', len(DEFAULT_COLORS))"
   ```

### Integration Testing

Test the complete endpoint:

```python
import asyncio
from mcp_tools.drawings.drawings import DrawingsMCPServer

async def test_endpoint():
    server = DrawingsMCPServer()
    
    # Test data
    companies = {
        "mindro": {"name": "Mindro BV", "type": "company", "parents": []},
        "subsidiary": {"name": "Subsidiary", "type": "company", "parents": [{"id": "mindro", "percentage": 100}]}
    }
    colors = {"company_color": "#4A90E2", "focus_company_color": "#FFD93D"}
    
    # Generate SVG
    result = await server.company_structure(companies, colors, "mindro")
    
    # Verify output
    assert len(result) > 0
    assert result.startswith(b'<svg')
    print("✅ Integration test passed!")

# Run test
asyncio.run(test_endpoint())
```

## Output Format

The endpoint returns **SVG binary data** (`bytes`) that can be:

- **Saved to file**: `open('diagram.svg', 'wb').write(result)`
- **Displayed in browser**: Convert to string and embed in HTML
- **Transmitted via MCP**: Sent as binary data through the protocol

### SVG Features

- **Responsive**: Scalable vector graphics
- **Professional**: Clean, modern styling
- **Accessible**: Proper text labels and structure
- **Compatible**: Works with all SVG viewers

## Configuration

### Default Colors

Default colors are defined in `constants.py`:

```python
DEFAULT_COLORS = {
    "person_color": "#FF6B6B",
    "investor_color": "#F8BBD9",
    "trust_color": "#F8BBD9",
    "foundation_color": "#96CEB4",
    "company_color": "#4A90E2",
    "custom_font_color": "#333333",
    "focus_company_color": "#FFD93D",
    # ... more colors
}
```

### Environment Variables

The MCP server uses these environment variables:

- `MCP_PORT`: Server port (default: 8080)
- `NOCODB_URL`: NocoDB instance URL (optional)
- `NOCODB_API_TOKEN`: NocoDB API token (optional)

## Troubleshooting

### Common Issues

1. **Import Errors**: Ensure all dependencies are installed
   ```bash
   poetry install
   ```

2. **SVG Generation Fails**: Check Plotly and Kaleido installation
   ```bash
   poetry add plotly kaleido
   ```

3. **MCP Server Won't Start**: Check port availability and environment variables

4. **Test Failures**: Ensure you're in the correct directory and using the right Python version

### Debug Mode

Enable debug logging:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## Architecture

The drawing tool consists of:

- **`drawings.py`**: MCP endpoint implementation
- **`company_structure.py`**: SVG generation logic using Plotly
- **`constants.py`**: Default colors and configuration
- **`tests/`**: Unit tests and integration tests

## Dependencies

- **Plotly**: For SVG generation and visualization
- **Kaleido**: For Plotly figure export to SVG
- **FastMCP**: For MCP protocol implementation
- **FastAPI**: For web server functionality

## Contributing

When adding new features:

1. Update the test suite
2. Add documentation
3. Follow the existing code style
4. Test with various input scenarios
