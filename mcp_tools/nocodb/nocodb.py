""" Nocodb MCP Server """

import os
import json
import httpx
import logging
from typing import Dict, List, Optional, Union, Any
from pydantic import BaseModel, Field
from mcp.server.fastmcp import FastMCP, Context
import sys
import re

logger = logging.getLogger("nocodb-mcp")


class NocoDBMCPServer:
    """NocoDB MCP Server implementation"""
    
    def __init__(self, nocodb_url: str, api_token: str):
        """
        Initialize the NocoDB MCP Server
        
        Args:
            nocodb_url: The base URL of your Nocodb instance
            api_token: The API token for authentication
        """
        self.nocodb_url = nocodb_url.rstrip('/')
        self.api_token = api_token
    
    def register_tools(self, mcp: FastMCP):
        """Register all NocoDB tools with the MCP server"""
        mcp.tool()(self.retrieve_records)
        mcp.tool()(self.create_records)
        mcp.tool()(self.update_records)
        mcp.tool()(self.delete_records)
        mcp.tool()(self.get_schema)
        mcp.tool()(self.list_tables)
    
    async def get_nocodb_client(self, ctx: Context = None) -> httpx.AsyncClient:
        """Create and return an authenticated httpx client for Nocodb API requests"""
        # Create httpx client with authentication headers - using xc-token as required by Nocodb v2 API
        headers = {
            "xc-token": self.api_token,
            "Content-Type": "application/json"
        }
        
        if logger.isEnabledFor(logging.DEBUG):
            logger.debug("Creating client for Nocodb API at %s", self.nocodb_url)
        return httpx.AsyncClient(base_url=self.nocodb_url, headers=headers, timeout=30.0)

    async def get_table_id(self, client: httpx.AsyncClient, base_id: str, table_name: str) -> str:
        """Get the table ID from the table name using the provided base ID"""
        logger.info("Looking up table ID for '%s' in base '%s'", table_name, base_id)
        
        # Get the list of tables in the base
        try:
            response = await client.get(f"/api/v2/meta/bases/{base_id}/tables")
            response.raise_for_status()
        except httpx.HTTPStatusError as e:
            error_msg = f"Failed to get tables list: HTTP {e.response.status_code}"
            logger.error(error_msg)
            if logger.isEnabledFor(logging.DEBUG):
                logger.debug("Response body: %s", e.response.text)
            raise ValueError(error_msg) from e
        
        tables = response.json().get("list", [])
        if logger.isEnabledFor(logging.DEBUG):
            logger.debug("Found %d tables in base", len(tables))
        
        # Find the table with the matching name
        for table in tables:
            if table.get("title") == table_name:
                table_id = table.get("id")
                logger.info("Found table ID for '%s': %s", table_name, table_id)
                return table_id
        
        error_msg = f"Table '{table_name}' not found in base '{base_id}'"
        logger.error(error_msg)
        if logger.isEnabledFor(logging.DEBUG):
            available_tables = [t.get('title') for t in tables]
            logger.debug("Available tables: %s", available_tables)
        raise ValueError(error_msg)

    async def retrieve_records(
        self,
        base_id: str,
        table_name: str,
        row_id: Optional[str] = None,
        filters: Optional[str] = None,
        limit: Optional[int] = 10,
        offset: Optional[int] = 0,
        sort: Optional[str] = None,
        fields: Optional[str] = None,
        ctx: Context = None
    ) -> Dict[str, Any]:
        """
        Retrieve one or multiple records from a Nocodb table.
        
        This tool allows you to query data from your Nocodb database tables with various options
        for filtering, sorting, and pagination. It supports both single record retrieval by ID
        and multi-record retrieval with conditions.
        
        Parameters:
        - base_id: The ID of the Nocodb base to use
        - table_name: Name of the table to query
        - row_id: (Optional) Specific row ID to retrieve a single record
        - filters: (Optional) Filter conditions in Nocodb format, e.g. "(column,eq,value)"
                    See Nocodb docs for comparison operators like eq, neq, gt, lt, etc.
        - limit: (Optional) Maximum number of records to return (default: 10)
        - offset: (Optional) Number of records to skip for pagination (default: 0)
        - sort: (Optional) Column to sort by, use "-" prefix for descending order
        - fields: (Optional) Comma-separated list of fields to include in the response
        
        Returns:
        - Dictionary containing the retrieved record(s) or error information
        
        Examples:
        1. Get all records from a table (limited to 10):
           retrieve_records(base_id="base123", table_name="customers")
           
        2. Get a specific record by ID:
           retrieve_records(base_id="base123", table_name="customers", row_id="123")
           
        3. Filter records with conditions:
           retrieve_records(
               base_id="base123",
               table_name="customers", 
               filters="(age,gt,30)~and(status,eq,active)"
           )
           
        4. Paginate results:
           retrieve_records(base_id="base123", table_name="customers", limit=20, offset=40)
           
        5. Sort results:
           retrieve_records(base_id="base123", table_name="customers", sort="-created_at")
           
        6. Select specific fields:
           retrieve_records(base_id="base123", table_name="customers", fields="id,name,email")
        """
        logger.info("Retrieve records request for table '%s' in base '%s'", table_name, base_id)
        
        # Parameter validation
        if not base_id:
            error_msg = "Base ID is required"
            logger.error(error_msg)
            return {"error": True, "message": error_msg}
        if not table_name:
            error_msg = "Table name is required"
            logger.error(error_msg)
            return {"error": True, "message": error_msg}
        
        # normalize table name so first letter of each word is uppercase
        table_name = ' '.join(word.capitalize() for word in table_name.split(' '))
        
        # Log query parameters for debugging
        if logger.isEnabledFor(logging.DEBUG):
            params_info = {
                "row_id": row_id,
                "filters": filters,
                "limit": limit,
                "offset": offset,
                "sort": sort,
                "fields": fields
            }
            logger.debug("Query parameters: %s", params_info)
        
        try:
            client = await self.get_nocodb_client(ctx)
            
            # Get the table ID from the table name
            table_id = await self.get_table_id(client, base_id, table_name)
            
            # Determine the endpoint based on whether we're fetching a single record or multiple
            if row_id:
                # Single record endpoint
                url = f"/api/v2/tables/{table_id}/records/{row_id}"
                logger.info("Retrieving single record with ID: %s", row_id)
                response = await client.get(url)
            else:
                # Multiple records endpoint
                url = f"/api/v2/tables/{table_id}/records"
                
                # Build query parameters
                params = {}
                if limit is not None:
                    params["limit"] = limit
                if offset is not None:
                    params["offset"] = offset
                if sort:
                    params["sort"] = sort
                if fields:
                    params["fields"] = fields
                if filters:
                    params["where"] = filters
                
                logger.info("Retrieving records with params: %s", params)    
                response = await client.get(url, params=params)
            
            # Handle response
            response.raise_for_status()
            result = response.json()
            
            # Print the number of records retrieved
            if row_id:
                # For single record retrieval
                record_count = 1 if result and not result.get("error") else 0
                logger.info("Retrieved %d record from table '%s'", record_count, table_name)
            else:
                # For multiple records retrieval
                records = result.get("list", [])
                record_count = len(records)
                logger.info("Retrieved %d records from table '%s'", record_count, table_name)
                
                # Log pagination info if available
                if "pageInfo" in result and logger.isEnabledFor(logging.DEBUG):
                    page_info = result.get("pageInfo", {})
                    logger.debug("Page info: %s", page_info)
            
            return result
            
        except httpx.HTTPStatusError as e:
            error_msg = f"HTTP error {e.response.status_code} retrieving records from '{table_name}'"
            logger.error(error_msg)
            if logger.isEnabledFor(logging.DEBUG):
                logger.debug("Response body: %s", e.response.text)
            return {
                "error": True,
                "status_code": e.response.status_code,
                "message": f"HTTP error: {e.response.text}"
            }
        except Exception as e:
            error_msg = f"Error retrieving records from '{table_name}': {str(e)}"
            logger.error(error_msg)
            if logger.isEnabledFor(logging.DEBUG):
                import traceback
                logger.debug(traceback.format_exc())
            return {
                "error": True,
                "message": f"Error: {str(e)}"
            }
        finally:
            if 'client' in locals():
                await client.aclose()

    async def create_records(
        self,
        base_id: str,
        table_name: str,
        data: Dict[str, Any],
        bulk: bool = False,
        ctx: Context = None
    ) -> Dict[str, Any]:
        """
        Create one or multiple records in a Nocodb table.
        
        This tool allows you to insert new data into your Nocodb database tables.
        It supports both single record creation and bulk operations for inserting
        multiple records at once.
        
        Parameters:
        - base_id: The ID of the Nocodb base to use
        - table_name: Name of the table to insert into
        - data: For single record: Dict with column:value pairs
                For bulk creation: List of dicts with column:value pairs
        - bulk: (Optional) Set to True for bulk creation with multiple records
        
        Returns:
        - Dictionary containing the created record(s) or error information
        
        Examples:
        1. Create a single record:
           create_records(
               base_id="base123",
               table_name="customers",
               data={"name": "John Doe", "email": "john@example.com", "age": 35}
           )
           
        2. Create multiple records in bulk:
           create_records(
               base_id="base123",
               table_name="customers",
               data=[
                   {"name": "John Doe", "email": "john@example.com", "age": 35},
                   {"name": "Jane Smith", "email": "jane@example.com", "age": 28}
               ],
               bulk=True
           )
        """
        logger.info("Create records request for table '%s' in base '%s'", table_name, base_id)
        
        # Parameter validation
        if not base_id:
            error_msg = "Base ID is required"
            logger.error(error_msg)
            return {"error": True, "message": error_msg}
        if not table_name:
            error_msg = "Table name is required"
            logger.error(error_msg)
            return {"error": True, "message": error_msg}
        if not data:
            error_msg = "Data is required for record creation"
            logger.error(error_msg)
            return {"error": True, "message": error_msg}
        
        # Ensure data is a list for bulk, or single dict otherwise
        original_data = data # Keep a reference before potential modification
        if bulk:
            if not isinstance(data, list):
                logger.warning("Bulk creation requested but data is not a list, converting single record to list")
                data = [data]
            elif not data: # Handle empty list for bulk
                 error_msg = "Data list cannot be empty for bulk creation"
                 logger.error(error_msg)
                 return {"error": True, "message": error_msg}
        elif isinstance(data, list):
            logger.warning("Single record creation requested but data is a list, using first item only")
            data = data[0] if data else {}
            if not data:
                error_msg = "Data dictionary cannot be empty for single record creation"
                logger.error(error_msg)
                return {"error": True, "message": error_msg}
                
        # Log operation details
        operation_type = "bulk" if bulk else "single record"
        # Use original_data for accurate count if it was modified
        record_count = len(data) if isinstance(data, list) else 1 
        if logger.isEnabledFor(logging.DEBUG):
            logger.debug("Creating %d records (%s)", record_count, operation_type)
        
        try:
            logger.info("Creating %d records (%s)", record_count, operation_type)
            client = await self.get_nocodb_client(ctx)
            
            # Get the table ID from the table name
            table_id = await self.get_table_id(client, base_id, table_name)
            
            # Determine the endpoint based on whether we're doing bulk creation or single record
            if bulk:
                # Bulk creation endpoint
                url = f"/api/v2/tables/{table_id}/records/bulk"
                logger.info("Performing bulk creation of %d records", len(data))
            else:
                # Single record creation endpoint
                url = f"/api/v2/tables/{table_id}/records"
                logger.info("Creating single record")
            
            logger.info("Sending data to %s", url)
            # Make the request - Pass the Python dictionary/list directly to the json parameter
            response = await client.post(url, json=data) 
            
            logger.info("Response Status: %d", response.status_code)
            if logger.isEnabledFor(logging.DEBUG):
                logger.debug("Response Body: %s", response.text)
            # Handle response
            response.raise_for_status()
            result = response.json()
            
            logger.info("Successfully created record(s) in table '%s'", table_name)
            return result
            
        except httpx.HTTPStatusError as e:
            error_msg = f"HTTP error {e.response.status_code} creating records in '{table_name}'"
            logger.error(error_msg)
            logger.error("Request Data: %s", data) # Log data on error
            if logger.isEnabledFor(logging.DEBUG):
                logger.debug("Response body: %s", e.response.text)
            return {
                "error": True,
                "status_code": e.response.status_code,
                "message": f"HTTP error: {e.response.text}"
            }
        except ValueError as e: # Catch errors from get_table_id or data validation
            error_msg = f"Error creating records in '{table_name}': {str(e)}"
            logger.error(error_msg)
            return {
                "error": True,
                "message": error_msg
            }
        except Exception as e:
            error_msg = f"Error creating records in '{table_name}': {str(e)}"
            logger.error(error_msg)
            if logger.isEnabledFor(logging.DEBUG):
                import traceback
                logger.debug(traceback.format_exc())
            return {
                "error": True,
                "message": f"Error: {str(e)}"
            }
        finally:
            if 'client' in locals():
                await client.aclose()

    async def update_records(
        self,
        base_id: str,
        table_name: str,
        row_id: Optional[str] = None,
        data: Dict[str, Any] = None,
        bulk: bool = False,
        bulk_ids: Optional[List[str]] = None,
        ctx: Context = None
    ) -> Dict[str, Any]:
        """
        Update one or multiple records in a Nocodb table.
        
        This tool allows you to modify existing data in your Nocodb database tables.
        It supports both single record updates by ID and bulk updates for multiple records.
        
        Parameters:
        - base_id: The ID of the Nocodb base to use
        - table_name: Name of the table to update
        - row_id: ID of the record to update (required for single record update)
        - data: Dictionary with column:value pairs to update
        - bulk: (Optional) Set to True for bulk updates
        - bulk_ids: (Optional) List of record IDs to update when bulk=True
        
        Returns:
        - Dictionary containing the updated record(s) or error information
        
        Examples:
        1. Update a single record by ID:
           update_records(
               base_id="base123",
               table_name="customers",
               row_id="123",
               data={"name": "John Smith", "status": "inactive"}
           )
           
        2. Update multiple records in bulk by IDs:
           update_records(
               base_id="base123",
               table_name="customers",
               data={"status": "inactive"},  # Same update applied to all records
               bulk=True,
               bulk_ids=["123", "456", "789"]
           )
        """
        logger.info("Update records request for table '%s' in base '%s'", table_name, base_id)
        
        # Parameter validation
        if not base_id:
            error_msg = "Base ID is required"
            logger.error(error_msg)
            return {"error": True, "message": error_msg}
        if not table_name:
            error_msg = "Table name is required"
            logger.error(error_msg)
            return {"error": True, "message": error_msg}
        if not data:
            error_msg = "Data parameter is required for updates"
            logger.error(error_msg)
            return {"error": True, "message": error_msg}
        
        # Validate update operation parameters
        if bulk and not bulk_ids:
            error_msg = "Bulk IDs are required for bulk updates"
            logger.error(error_msg)
            return {"error": True, "message": error_msg}
        elif not bulk and not row_id:
            error_msg = "Row ID is required for single record update"
            logger.error(error_msg)
            return {"error": True, "message": error_msg}
        
        # Log operation details
        operation_type = "bulk" if bulk else "single record"
        if bulk:
            if logger.isEnabledFor(logging.DEBUG):
                logger.debug("Updating %d records in bulk", len(bulk_ids))
        else:
            if logger.isEnabledFor(logging.DEBUG):
                logger.debug("Updating single record with ID: %s", row_id)
        
        try:
            client = await self.get_nocodb_client(ctx)
            
            # Get the table ID from the table name
            table_id = await self.get_table_id(client, base_id, table_name)
            
            # Determine the endpoint based on whether we're doing bulk update or single record
            if bulk and bulk_ids:
                # Bulk update by IDs endpoint
                url = f"/api/v2/tables/{table_id}/records/bulk"
                # For bulk updates with IDs, we need to include both ids and data
                payload = {"ids": bulk_ids, "data": data}
                logger.info("Performing bulk update of %d records", len(bulk_ids))
                response = await client.patch(url, json=payload)
            elif row_id:
                # Single record update endpoint
                url = f"/api/v2/tables/{table_id}/records/{row_id}"
                logger.info("Updating record with ID: %s", row_id)
                response = await client.patch(url, json=data)
            else:
                error_msg = "Either row_id (for single update) or bulk=True with bulk_ids (for bulk update) must be provided"
                logger.error(error_msg)
                return {
                    "error": True,
                    "message": error_msg
                }
            
            # Handle response
            response.raise_for_status()
            result = response.json()
            
            logger.info("Successfully updated record(s) in table '%s'", table_name)
            return result
            
        except httpx.HTTPStatusError as e:
            error_msg = f"HTTP error {e.response.status_code} updating records in '{table_name}'"
            logger.error(error_msg)
            if logger.isEnabledFor(logging.DEBUG):
                logger.debug("Response body: %s", e.response.text)
            return {
                "error": True,
                "status_code": e.response.status_code,
                "message": f"HTTP error: {e.response.text}"
            }
        except Exception as e:
            error_msg = f"Error updating records in '{table_name}': {str(e)}"
            logger.error(error_msg)
            if logger.isEnabledFor(logging.DEBUG):
                import traceback
                logger.debug(traceback.format_exc())
            return {
                "error": True,
                "message": f"Error: {str(e)}"
            }
        finally:
            if 'client' in locals():
                await client.aclose()

    async def delete_records(
        self,
        base_id: str,
        table_name: str,
        row_id: Optional[str] = None,
        bulk: bool = False,
        bulk_ids: Optional[List[str]] = None,
        ctx: Context = None
    ) -> Dict[str, Any]:
        """
        Delete one or multiple records from a Nocodb table.
        
        This tool allows you to remove data from your Nocodb database tables.
        It supports both single record deletion by ID and bulk deletions for multiple records.
        
        Parameters:
        - base_id: The ID of the Nocodb base to use
        - table_name: Name of the table to delete from
        - row_id: ID of the record to delete (required for single record deletion)
        - bulk: (Optional) Set to True for bulk deletion
        - bulk_ids: (Optional) List of record IDs to delete when bulk=True
        
        Returns:
        - Dictionary containing the operation result or error information
        
        Examples:
        1. Delete a single record by ID:
           delete_records(
               base_id="base123",
               table_name="customers",
               row_id="123"
           )
           
        2. Delete multiple records in bulk by IDs:
           delete_records(
               base_id="base123",
               table_name="customers",
               bulk=True,
               bulk_ids=["123", "456", "789"]
           )
        """
        logger.info("Delete records request for table '%s' in base '%s'", table_name, base_id)
        
        # Parameter validation
        if not base_id:
            error_msg = "Base ID is required"
            logger.error(error_msg)
            return {"error": True, "message": error_msg}
        if not table_name:
            error_msg = "Table name is required"
            logger.error(error_msg)
            return {"error": True, "message": error_msg}
        
        # normalize table name so first letter of each word is uppercase
        table_name = ' '.join(word.capitalize() for word in table_name.split(' '))

        # Validate delete operation parameters
        if bulk and not bulk_ids:
            error_msg = "Bulk IDs are required for bulk deletion"
            logger.error(error_msg)
            return {"error": True, "message": error_msg}
        elif not bulk and not row_id:
            error_msg = "Row ID is required for single record deletion"
            logger.error(error_msg)
            return {"error": True, "message": error_msg}
        
        # Log operation details
        operation_type = "bulk" if bulk else "single record"
        if bulk:
            if logger.isEnabledFor(logging.DEBUG):
                logger.debug("Deleting %d records in bulk", len(bulk_ids))
        else:
            if logger.isEnabledFor(logging.DEBUG):
                logger.debug("Deleting single record with ID: %s", row_id)
        
        try:
            client = await self.get_nocodb_client(ctx)
            
            # Get the table ID from the table name
            table_id = await self.get_table_id(client, base_id, table_name)
            
            # Determine the endpoint based on whether we're doing bulk deletion or single record
            if bulk and bulk_ids:
                # Bulk deletion endpoint
                url = f"/api/v2/tables/{table_id}/records/bulk"
                # For bulk deletions with IDs, we need to send the ids in the request body
                logger.info("Performing bulk deletion of %d records", len(bulk_ids))
                response = await client.request("DELETE", url, json={"ids": bulk_ids}) # Use explicit DELETE with body
            elif row_id:
                # Single record deletion endpoint
                url = f"/api/v2/tables/{table_id}/records/{row_id}"
                logger.info("Deleting record with ID: %s", row_id)
                response = await client.delete(url)
            else:
                error_msg = "Either row_id (for single deletion) or bulk=True with bulk_ids (for bulk deletion) must be provided"
                logger.error(error_msg)
                return {
                    "error": True,
                    "message": error_msg
                }
            
            # Handle response
            response.raise_for_status()
            
            # Delete operations may return 200 or 204 with different body content
            if response.status_code == 204: # No content
                 result = {"success": True, "message": "Record(s) deleted successfully"}
            else:
                try:
                    result = response.json()
                    # NocoDB bulk delete might return a number (count) or an object
                    if isinstance(result, (int, float)):
                        result = {"success": True, "message": f"{result} record(s) deleted successfully"}
                    elif not isinstance(result, dict): # Handle unexpected formats
                         result = {"success": True, "message": "Record(s) deleted successfully", "response_data": result}

                except json.JSONDecodeError:
                    logger.warning("Delete operation returned non-empty, non-JSON response body")
                    result = {"success": True, "message": "Record(s) deleted successfully (non-JSON response)"}

            logger.info("Successfully deleted record(s) from table '%s'", table_name)
            return result
            
        except httpx.HTTPStatusError as e:
            error_msg = f"HTTP error {e.response.status_code} deleting records from '{table_name}'"
            logger.error(error_msg)
            if logger.isEnabledFor(logging.DEBUG):
                logger.debug("Response body: %s", e.response.text)
            return {
                "error": True,
                "status_code": e.response.status_code,
                "message": f"HTTP error: {e.response.text}"
            }
        except Exception as e:
            error_msg = f"Error deleting records from '{table_name}': {str(e)}"
            logger.error(error_msg)
            if logger.isEnabledFor(logging.DEBUG):
                import traceback
                logger.debug(traceback.format_exc())
            return {
                "error": True,
                "message": f"Error: {str(e)}"
            }
        finally:
            if 'client' in locals():
                await client.aclose()

    async def get_schema(
        self,
        base_id: str,
        table_name: str,
        ctx: Context = None
    ) -> Dict[str, Any]:
        """
        Retrieve the schema (columns) of a Nocodb table.
        
        This tool fetches the metadata for a specific table, including details about its columns.
        
        Parameters:
        - base_id: The ID of the Nocodb base to use
        - table_name: Name of the table to get the schema for
        
        Returns:
        - Dictionary containing the table schema or error information. 
          The schema details, including the list of columns, are typically nested within the response.
        
        Example:
        Get the schema for the "products" table:
           get_schema(base_id="base123", table_name="products")
        """
        logger.info("Get schema request for table '%s' in base '%s'", table_name, base_id)

        # Parameter validation
        if not base_id:
            error_msg = "Base ID is required"
            logger.error(error_msg)
            return {"error": True, "message": error_msg}
        if not table_name:
            error_msg = "Table name is required"
            logger.error(error_msg)
            return {"error": True, "message": error_msg}
        
        try:
            client = await self.get_nocodb_client(ctx)
            
            # Get the table ID from the table name
            table_id = await self.get_table_id(client, base_id, table_name)
            
            # Fetch table metadata using the table ID
            # The endpoint /api/v2/meta/tables/{tableId} provides table details including columns
            url = f"/api/v2/meta/tables/{table_id}"
            logger.info("Retrieving schema for table ID: %s using url %s", table_id, url)
            
            response = await client.get(url)
            response.raise_for_status()
            
            result = response.json()
            
            # Log success and potentially the number of columns found
            columns = result.get("columns", [])
            logger.info("Successfully retrieved schema for table '%s'. Found %d columns.", table_name, len(columns))
            if logger.isEnabledFor(logging.DEBUG):
                logger.debug("Schema details: %s", result) # Log full schema for debugging if needed
            
            return result # Return the full table metadata which includes the columns

        except httpx.HTTPStatusError as e:
            error_msg = f"HTTP error {e.response.status_code} retrieving schema for '{table_name}'"
            logger.error(error_msg)
            if logger.isEnabledFor(logging.DEBUG):
                logger.debug("Response body: %s", e.response.text)
            return {
                "error": True,
                "status_code": e.response.status_code,
                "message": f"HTTP error: {e.response.text}"
            }
        except ValueError as e: # Catch errors from get_table_id
            error_msg = f"Error retrieving schema for '{table_name}': {str(e)}"
            logger.error(error_msg)
            return {
                "error": True,
                "message": error_msg
            }
        except Exception as e:
            error_msg = f"Error retrieving schema for '{table_name}': {str(e)}"
            logger.error(error_msg)
            if logger.isEnabledFor(logging.DEBUG):
                import traceback
                logger.debug(traceback.format_exc())
            return {
                "error": True,
                "message": f"Error: {str(e)}"
            }
        finally:
            if 'client' in locals():
                await client.aclose()

    async def list_tables(
        self,
        base_id: str,
        ctx: Context = None
    ) -> Dict[str, Any]:
        """
        List all tables in the Nocodb base.
        
        This tool retrieves a list of all tables available in the provided Nocodb base,
        including their IDs, names, and other metadata.
        
        Parameters:
        - base_id: The ID of the Nocodb base to use
        
        Returns:
        - Dictionary containing the list of tables or error information
        
        Example:
        Get all tables in the base:
           list_tables(base_id="base123")
        """
        logger.info("List tables request for base '%s'", base_id)
        
        if not base_id:
            error_msg = "Base ID is required"
            logger.error(error_msg)
            return {"error": True, "message": error_msg}
        try:
            client = await self.get_nocodb_client(ctx)
            
            # Get the list of tables in the base
            url = f"/api/v2/meta/bases/{base_id}/tables"
            logger.info("Retrieving tables from base '%s'", base_id)
            
            response = await client.get(url)
            response.raise_for_status()
            
            result = response.json()
            tables = result.get("list", [])
            
            logger.info("Successfully retrieved %d tables from base '%s'", len(tables), base_id)
            if logger.isEnabledFor(logging.DEBUG):
                table_names = [t.get('title') for t in tables]
                logger.debug("Tables: %s", table_names)
            
            return result
            
        except httpx.HTTPStatusError as e:
            error_msg = f"HTTP error {e.response.status_code} retrieving tables from base '{base_id}'"
            logger.error(error_msg)
            if logger.isEnabledFor(logging.DEBUG):
                logger.debug("Response body: %s", e.response.text)
            return {
                "error": True,
                "status_code": e.response.status_code,
                "message": f"HTTP error: {e.response.text}"
            }
        except Exception as e:
            error_msg = f"Error retrieving tables from base '{base_id}': {str(e)}"
            logger.error(error_msg)
            if logger.isEnabledFor(logging.DEBUG):
                import traceback
                logger.debug(traceback.format_exc())
            return {
                "error": True,
                "message": f"Error: {str(e)}"
            }
        finally:
            if 'client' in locals():
                await client.aclose()
