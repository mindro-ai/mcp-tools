# MCP Tools Project

A modular Model Context Protocol (MCP) server that supports multiple endpoints, starting with NocoDB integration.

## Features

- **Modular Architecture**: Support for multiple MCP endpoints in a single server
- **NocoDB Integration**: Full CRUD operations for NocoDB databases
- **Extensible Design**: Easy to add new endpoints
- **Environment-based Configuration**: Flexible configuration through environment variables

## Architecture

The project uses a modular design with the following components:

- **BaseMCPServer**: Main server that can handle multiple endpoints
- **NocoDBMCPServer**: NocoDB-specific endpoint implementation
- **ExampleMCPServer**: Example endpoint to demonstrate extensibility

## Installation

1. Install dependencies:
```bash
poetry install
```

2. Set up environment variables for NocoDB and MCP server:
```bash
export NOCODB_URL="https://your-nocodb-instance.com"
export NOCODB_API_TOKEN="your-api-token"
export MCP_TRANSPORT="sse"
export MCP_PORT="8080"
```

## Usage

### Running the Server

```bash
# Using poetry
poetry run mcp-server

# Or directly
python -m mcp_tools
```

### Default Endpoint

By default, the server will be available at:

    http://localhost:8080/sse

**Note**: The SSE endpoint is always available at `/sse` regardless of configuration.

### MCP Client Configuration Example

```json
{
  "endpoint": "http://localhost:8080/sse",
  "transport": "sse"
}
```

or, if your client uses environment variables:

```
MCP_ENDPOINT=http://localhost:8080/sse
MCP_TRANSPORT=sse
```

### Available Tools

#### NocoDB Tools (prefixed with `nocodb_`)

All NocoDB tools require a `base_id` parameter to specify which NocoDB base to work with:

- `nocodb_retrieve_records`: Query records from NocoDB tables
  - Parameters: `base_id`, `table_name`, `row_id` (optional), `filters` (optional), etc.
- `nocodb_create_records`: Create new records
  - Parameters: `base_id`, `table_name`, `data`, `bulk` (optional)
- `nocodb_update_records`: Update existing records
  - Parameters: `base_id`, `table_name`, `data`, `row_id` or `bulk_ids`
- `nocodb_delete_records`: Delete records
  - Parameters: `base_id`, `table_name`, `row_id` or `bulk_ids`
- `nocodb_get_schema`: Get table schema
  - Parameters: `base_id`, `table_name`
- `nocodb_list_tables`: List all tables in the base
  - Parameters: `base_id`

#### Example Tools (prefixed with `example_`)

- `example_hello_world`: Simple greeting tool
- `example_get_config`: Get endpoint configuration

## Adding New Endpoints

To add a new MCP endpoint:

1. Create a new endpoint class that implements the required interface:

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
def create_my_endpoint_server(config: dict):
    return MyEndpointMCPServer(config)

# In main():
my_server = create_my_endpoint_server(config)
if my_server:
    main_server.register_endpoint("my_endpoint", my_server)
```

## Configuration

The server supports environment-based configuration:

- `NOCODB_URL`: NocoDB instance URL
- `NOCODB_API_TOKEN`: NocoDB API token
- `MCP_TRANSPORT`: MCP server transport protocol (default: `sse`)
- `MCP_PORT`: MCP server port (default: `8080`)

**Note**: `base_id` is no longer a global configuration. It must be provided as a parameter to each NocoDB tool call to specify which base to work with.

## Development

### Project Structure

```
mcp_tools/
├── __init__.py
├── __main__.py          # Main entry point
├── base_server.py       # Base MCP server class
├── nocodb.py           # NocoDB endpoint implementation
├── example_endpoint.py # Example endpoint
└── old_server.py       # Legacy implementation
```

### Dependencies

- `httpx`: HTTP client for API requests
- `pydantic`: Data validation
- `mcp`: Model Context Protocol server framework
- `uvicorn`: ASGI server for SSE/HTTP transport

## License

This project is licensed under the MIT License.
