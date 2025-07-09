"""This is the main entry point for the MCP tools project."""

import os
import sys
import logging
from typing import Optional
from dotenv import load_dotenv

# Import our modules
from . import (
    DEFAULT_NAME, DEFAULT_LOG_LEVEL,
    DEFAULT_TRANSPORT, DEFAULT_PORT
)
from .base_server import BaseMCPServer
from .nocodb import NocoDBMCPServer
from .example_endpoint import ExampleMCPServer

load_dotenv()

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger("mcp-tools-main")


def get_environment_config() -> dict:
    """Get configuration from environment variables"""
    config = {
        "nocodb_url": os.environ.get("NOCODB_URL"),
        "nocodb_api_token": os.environ.get("NOCODB_API_TOKEN"),
        "transport": os.environ.get("MCP_TRANSPORT", DEFAULT_TRANSPORT),
        "port": int(os.environ.get("MCP_PORT", DEFAULT_PORT)),
    }
    
    # Log configuration status
    for key, value in config.items():
        status = "SET" if value else "MISSING"
        logger.info("Environment variable %s: %s", key, status)
    
    return config


def create_nocodb_server(config: dict) -> Optional[NocoDBMCPServer]:
    """Create and return a NocoDB MCP server if configuration is available"""
    if not all([config["nocodb_url"], config["nocodb_api_token"]]):
        logger.warning("NocoDB configuration incomplete - skipping NocoDB endpoint")
        return None
    
    try:
        server = NocoDBMCPServer(
            nocodb_url=config["nocodb_url"],
            api_token=config["nocodb_api_token"]
        )
        logger.info("NocoDB MCP server created successfully")
        return server
    except Exception as e:
        logger.error("Failed to create NocoDB MCP server: %s", str(e))
        return None


def create_example_server() -> ExampleMCPServer:
    """Create and return an Example MCP server"""
    try:
        config = {"version": "1.0.0", "description": "Example endpoint"}
        server = ExampleMCPServer(config)
        logger.info("Example MCP server created successfully")
        return server
    except Exception as e:
        logger.error("Failed to create Example MCP server: %s", str(e))
        raise


def main() -> None:
    """
    This is the main entry point for the MCP tools project.
    It creates and runs a multi-endpoint MCP server.
    """
    logger.info("Starting MCP Tools Project")
    
    # Get configuration
    config = get_environment_config()
    
    # Create the main MCP server
    main_server = BaseMCPServer(name=DEFAULT_NAME, log_level=DEFAULT_LOG_LEVEL, port=config["port"])
    
    # Register NocoDB endpoint if configuration is available
    nocodb_server = create_nocodb_server(config)
    if nocodb_server:
        main_server.register_endpoint("nocodb", nocodb_server)
    
    # Register Example endpoint (always available for demonstration)
    try:
        example_server = create_example_server()
        main_server.register_endpoint("example", example_server)
    except Exception as e:
        logger.warning("Could not register example endpoint: %s", str(e))
    
    # Check if we have any endpoints registered
    if not main_server.endpoints:
        logger.error("No endpoints configured. Please set the required environment variables.")
        logger.error("For NocoDB: NOCODB_URL, NOCODB_API_TOKEN")
        sys.exit(1)
    
    # Run the server
    try:
        logger.info("Starting MCP server...")
        
        # Handle asyncio event loop for SSE transport
        if config["transport"] in ["sse", "streamable-http"]:
            import asyncio
            try:
                # Check if there's already an event loop running
                loop = asyncio.get_running_loop()
                logger.info("Event loop already running, using existing loop")
            except RuntimeError:
                # No event loop running, create a new one
                logger.info("Creating new event loop")
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
        
        main_server.run(
            transport=config["transport"],
            port=config["port"]
        )
    except KeyboardInterrupt:
        logger.info("MCP server stopped by user")
    except Exception as e:
        logger.error("Error running MCP server: %s", str(e))
        sys.exit(1)


if __name__ == "__main__":
    main()
