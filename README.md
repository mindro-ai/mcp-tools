# MCP Tools

A collection of tools for the Model Context Protocol (MCP).

## Architecture Decisions

### SVG Generator Implementation

The drawing tools use Plotly to generate company structure diagrams and convert them to SVG format for compatibility with the MCP protocol. This approach provides:

1. **MCP Protocol Compatibility**: Converts Plotly figures to SVG binary data as required by the MCP protocol
2. **Rich Visualization Features**: Leverages Plotly's powerful visualization capabilities
3. **Custom Business Logic**: Implements specific requirements for company hierarchy visualization with ownership percentages
4. **Interactive Development**: Plotly provides excellent debugging and development tools
5. **Extensibility**: Easy to add new visualization features using Plotly's extensive API

The implementation uses Plotly's `to_image()` method with Kaleido for SVG export, ensuring compatibility with the MCP protocol while maintaining the flexibility of Plotly's visualization engine.

## Features

- **Modular Architecture**: Support for multiple MCP endpoints in a single server
- **Extensible Design**: Easy to add new endpoints
- **Environment-based Configuration**: Flexible configuration through environment variables

- **NocoDB Integration**: Full CRUD operations for NocoDB databases

## Architecture

The project uses a modular design with the following components:

- `BaseMCPServer`: Main server that can handle multiple endpoints. It uses FastAPI to mount each endpoint on a separate path.
- `HealthMCPServer`: Health-specific endpoint implementation.
- `NocoDBMCPServer`: NocoDB-specific endpoint implementation.

## Installation

1. Install dependencies:
```bash
poetry install
```

2. Set up environment variables for NocoDB and MCP server:
```bash
export MCP_PORT="8080"
export NOCODB_URL="https://your-nocodb-instance.com"
export NOCODB_API_TOKEN="your-api-token"
```

## Usage

### Running the Server

```bash
# Using poetry
poetry run mcp-server

# Or directly
python -m mcp_tools
```

### Endpoints

The server exposes different MCP endpoints on different paths. For example:
- **Health Endpoint**: `http://localhost:8080/health/sse`
- **NocoDB Endpoint**: `http://localhost:8080/nocodb/sse`

Accessing the base path for an endpoint (e.g., `http://localhost:8080/health`) will redirect to the SSE endpoint.

### MCP Client Configuration Example

To connect to the **health** endpoint, use the full SSE path:
```json
{
  "endpoint": "http://localhost:8080/health/sse",
  "transport": "sse"
}
```

or, if your client uses environment variables:
```
MCP_ENDPOINT=http://localhost:8080/health/sse
MCP_TRANSPORT=sse
```

To connect to the **nocodb** endpoint, use the full SSE path:
```json
{
  "endpoint": "http://localhost:8080/nocodb/sse",
  "transport": "sse"
}
```

### Available Tools

#### Health Tools (available at `/health/sse`)

- `get_health_status`: Get the current health status of the system.

#### NocoDB Tools (available at `/nocodb/sse`)

All NocoDB tools require a `base_id` parameter to specify which NocoDB base to work with:

- `retrieve_records`: Query records from NocoDB tables
- `create_records`: Create new records
- `update_records`: Update existing records
- `delete_records`: Delete records
- `get_schema`: Get table schema
- `list_tables`: List all tables in the base


## Adding New Endpoints

To add a new MCP endpoint:

1. Create a new endpoint class that implements the required interface (it must have a `get_mcp_server` method that returns a `FastMCP` instance):

```python
from mcp.server.fastmcp import FastMCP, Context

class MyEndpointMCPServer:
    def __init__(self, config):
        self.mcp = FastMCP("My Endpoint", log_level="ERROR")
        self._register_tools()
    
    def _register_tools(self):
        # Register your tools here
        self.mcp.tool()(self.my_tool)
    
    async def my_tool(self, ctx: Context = None):
        # Your tool implementation
        pass
    
    def get_mcp_server(self) -> FastMCP:
        return self.mcp
```

2. Register the endpoint in `__main__.py`:

```python
# In main():
my_server = create_my_endpoint_server(config)
if my_server:
    main_server.register_endpoint("my_endpoint", my_server)
```

## Configuration

The server supports environment-based configuration:
- `MCP_PORT`: MCP server port (default: `8080`)

### NocoDB specific configuration
- `NOCODB_URL`: NocoDB instance URL
- `NOCODB_API_TOKEN`: NocoDB API token


## Development

### Project Structure

```
mcp_tools/
├── __init__.py
├── __main__.py          # Main entry point
├── base_server.py       # Base MCP server class
├── health/              # Health endpoint module
│   ├── __init__.py
│   └── health.py
├── nocodb/              # NocoDB endpoint module
│   ├── __init__.py
│   └── nocodb.py
└── old_server.py       # Legacy implementation
```

### Dependencies

- `fastapi`: For building the web server application.
- `uvicorn`: ASGI server for SSE/HTTP transport.
- `httpx`: HTTP client for API requests.
- `pydantic`: Data validation.
- `mcp`: Model Context Protocol server framework.
