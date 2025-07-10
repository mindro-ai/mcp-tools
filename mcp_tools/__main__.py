"""This is the main entry point for the MCP tools project."""

import os
import sys
import logging
from typing import Optional
from dotenv import load_dotenv

# Import our modules
from . import (
    DEFAULT_NAME, DEFAULT_LOG_LEVEL, DEFAULT_PORT
)
from .base_server import BaseMCPServer
from .nocodb import NocoDBMCPServer
from .health import HealthMCPServer

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
        "port": int(os.environ.get("MCP_PORT", DEFAULT_PORT)),
        "nocodb_url": os.environ.get("NOCODB_URL"),
        "nocodb_api_token": os.environ.get("NOCODB_API_TOKEN"),
    }
    
    # Log configuration status
    for key, value in config.items():
        status = "SET" if value else "MISSING"
        logger.info("Environment variable %s: %s", key, status)
    
    return config


def create_health_server() -> HealthMCPServer:
    """Create and return a Health MCP server"""
    try:
        config = {"version": "1.0.0", "description": "Health endpoint"}
        server = HealthMCPServer(config)
        logger.info("Health MCP server created successfully")
        return server
    except Exception as e:
        logger.error("Failed to create Health MCP server: %s", str(e))
        raise


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
    
    # Register Health endpoint (always available for system monitoring)
    try:
        health_server = create_health_server()
        main_server.register_endpoint("health", health_server)
    except Exception as e:
        logger.warning("Could not register health endpoint: %s", str(e))
    
    # Register NocoDB endpoint if configuration is available
    nocodb_server = create_nocodb_server(config)
    if nocodb_server:
        main_server.register_endpoint("nocodb", nocodb_server)
    
    # Check if we have any endpoints registered
    if not main_server.endpoints:
        logger.error("No endpoints configured. Please set the required environment variables.")
        logger.error("For NocoDB: NOCODB_URL, NOCODB_API_TOKEN")
        sys.exit(1)
    
    # Run the server
    try:
        logger.info("Starting MCP server...")
        main_server.run()
    except KeyboardInterrupt:
        logger.info("MCP server stopped by user")
    except Exception as e:
        logger.error("Error running MCP server: %s", str(e))
        sys.exit(1)


if __name__ == "__main__":
    main()
