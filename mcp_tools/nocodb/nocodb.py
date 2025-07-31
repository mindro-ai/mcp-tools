import os
import json
import httpx
import logging
from typing import Dict, List, Optional, Union, Any
from pydantic import BaseModel, Field, validator
from mcp.server.fastmcp import FastMCP, Context
import sys
import re
from collections import defaultdict

logger = logging.getLogger("nocodb-mcp")


class NocoDBAPIError(Exception):
    """Base exception for NocoDB API errors"""

    pass


class TableNotFoundError(NocoDBAPIError):
    """Table not found in the base"""

    pass


class ColumnNotFoundError(NocoDBAPIError):
    """Column not found in the table"""

    pass


class InvalidSchemaError(NocoDBAPIError):
    """Invalid table/column schema provided"""

    pass


class BaseNotFoundError(NocoDBAPIError):
    """Base not found"""

    pass


class ColumnSchema(BaseModel):
    """Schema definition for a table column"""

    title: str
    column_name: str
    uidt: str  # UI Data Type
    dt: Optional[str] = None  # Database type
    np: Optional[str] = None  # Nullable/Not null
    pk: Optional[bool] = False  # Primary key
    ai: Optional[bool] = False  # Auto increment

    @validator("uidt")
    def validate_uidt(cls, v):
        valid_types = [
            "SingleLineText",
            "LongText",
            "Number",
            "Decimal",
            "Currency",
            "Percent",
            "Duration",
            "Rating",
            "Checkbox",
            "MultiSelect",
            "SingleSelect",
            "Date",
            "DateTime",
            "Time",
            "Year",
            "PhoneNumber",
            "Email",
            "URL",
            "Attachment",
            "JSON",
            "SpecificDBType",
        ]
        if v not in valid_types:
            raise ValueError(f"Invalid UI data type. Must be one of: {valid_types}")
        return v


class TableSchema(BaseModel):
    """Schema definition for a table"""

    title: str
    table_name: str
    columns: List[ColumnSchema]


class NocoDBMCPServer:
    """Enhanced NocoDB MCP Server implementation"""

    def __init__(self, nocodb_url: str, api_token: str):
        """
        Initialize the NocoDB MCP Server

        Args:
            nocodb_url: The base URL of your Nocodb instance
            api_token: The API token for authentication
        """
        self.nocodb_url = nocodb_url.rstrip("/")
        self.api_token = api_token
        self._schema_cache = {}  # Cache for table schemas

    def register_tools(self, mcp: FastMCP):
        """Register all NocoDB tools with the MCP server"""
        


        # Existing CRUD operations
        mcp.tool()(self.retrieve_records)
        mcp.tool()(self.create_records)
        mcp.tool()(self.update_records)
        mcp.tool()(self.delete_records)
        mcp.tool()(self.get_schema)
        mcp.tool()(self.list_tables)

        # New DDL operations
        mcp.tool()(self.create_table)
        mcp.tool()(self.drop_table)
        mcp.tool()(self.add_column)
        mcp.tool()(self.drop_column)
        mcp.tool()(self.alter_table)
        mcp.tool()(self.rename_table)
        mcp.tool()(self.rename_column)
        mcp.tool()(self.alter_column)
        mcp.tool()(self.truncate_table)
        mcp.tool()(self.add_table_comment)
        mcp.tool()(self.add_column_comment)

        # Enhanced DML operations
        mcp.tool()(self.upsert_records)
        mcp.tool()(self.bulk_operations)
        mcp.tool()(self.aggregate_data)


        # mcp.tool()(self.retrieve_records)
        # mcp.tool()(self.create_records)
        # mcp.tool()(self.update_records)
        # mcp.tool()(self.delete_records)
        # mcp.tool()(self.get_schema)
        # mcp.tool()(self.list_tables)

    async def get_nocodb_client(self, ctx: Context = None) -> httpx.AsyncClient:
        """Create and return an authenticated httpx client for Nocodb API requests"""
        headers = {"xc-token": self.api_token, "Content-Type": "application/json"}

        if logger.isEnabledFor(logging.DEBUG):
            logger.debug("Creating client for Nocodb API at %s", self.nocodb_url)

        return httpx.AsyncClient(
            base_url=self.nocodb_url, headers=headers, timeout=30.0
        )

    async def _handle_api_error(self, response: httpx.Response, operation: str):
        """Handle API errors with specific exception types"""
        if response.status_code == 404:
            error_text = response.text
            if "table" in error_text.lower():
                raise TableNotFoundError(f"Table not found during {operation}")
            elif "base" in error_text.lower():
                raise BaseNotFoundError(f"Base not found during {operation}")
            else:
                raise NocoDBAPIError(
                    f"Resource not found during {operation}: {error_text}"
                )
        elif response.status_code == 400:
            raise InvalidSchemaError(
                f"Invalid request during {operation}: {response.text}"
            )
        else:
            raise NocoDBAPIError(
                f"API error during {operation}: HTTP {response.status_code} - {response.text}"
            )

    async def get_table_id(
        self, client: httpx.AsyncClient, base_id: str, table_name: str
    ) -> str:
        """Get the table ID from the table name using the provided base ID"""
        logger.info("Looking up table ID for '%s' in base '%s'", table_name, base_id)

        # Check cache first
        cache_key = f"{base_id}:{table_name}"
        if cache_key in self._schema_cache:
            return self._schema_cache[cache_key]["table_id"]

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

        # Normalize table name
        table_name_normalized = " ".join(
            word.capitalize() for word in table_name.split(" ")
        )

        for table in tables:
            if table.get("title") == table_name_normalized:
                table_id = table.get("id")
                logger.info("Found table ID for '%s': %s", table_name, table_id)

                # Cache the result
                self._schema_cache[cache_key] = {"table_id": table_id}
                return table_id

        error_msg = f"Table '{table_name}' not found in base '{base_id}'"
        logger.error(error_msg)
        if logger.isEnabledFor(logging.DEBUG):
            available_tables = [t.get("title") for t in tables]
            logger.debug("Available tables: %s", available_tables)
        raise ValueError(error_msg)

    # DDL Operations
    async def create_table(
        self, base_id: str, table_schema: Dict[str, Any], ctx: Context = None
    ) -> Dict[str, Any]:
        """
        Create a new table in the NocoDB base.

        Parameters:
        - base_id: The ID of the NocoDB base
        - table_schema: Dictionary containing table schema with title, table_name, and columns

        Returns:
        - Dictionary containing the created table information

        Example:
        create_table(
            base_id="base123",
            table_schema={
                "title": "Customers",
                "table_name": "customers",
                "columns": [
                    {
                        "title": "Name",
                        "column_name": "name",
                        "uidt": "SingleLineText"
                    },
                    {
                        "title": "Email",
                        "column_name": "email",
                        "uidt": "Email"
                    }
                ]
            }
        )
        """
        logger.info("Create table request for base '%s'", base_id)

        if not base_id or not table_schema:
            return {"error": True, "message": "Base ID and table schema are required"}

        try:
            # Validate schema
            validated_schema = TableSchema(**table_schema)

            client = await self.get_nocodb_client(ctx)
            url = f"/api/v2/meta/bases/{base_id}/tables"

            # Prepare the payload for NocoDB API
            payload = {
                "title": validated_schema.title,
                "table_name": validated_schema.table_name,
                "columns": [col.dict() for col in validated_schema.columns],
            }

            logger.info(
                "Creating table '%s' in base '%s'", validated_schema.title, base_id
            )
            response = await client.post(url, json=payload)

            if not response.is_success:
                await self._handle_api_error(response, "table creation")

            result = response.json()

            # Clear schema cache
            self._schema_cache.pop(base_id, None)

            logger.info("Successfully created table '%s'", validated_schema.title)
            return result

        except Exception as e:
            error_msg = f"Error creating table: {str(e)}"
            logger.error(error_msg)
            return {"error": True, "message": error_msg}
        finally:
            if "client" in locals():
                await client.aclose()

    async def drop_table(
        self, base_id: str, table_id: str, ctx: Context = None
    ) -> Dict[str, Any]:
        """
        Drop (delete) a table from the NocoDB base.

        Parameters:
        - base_id: The ID of the NocoDB base
        - table_id: The ID of the table to drop

        Returns:
        - Dictionary containing the operation result

        Example:
        drop_table(base_id="base123", table_id="tbl_xyz")
        """
        logger.info("Drop table request for table '%s' in base '%s'", table_id, base_id)

        if not base_id or not table_id:
            return {"error": True, "message": "Base ID and table ID are required"}

        try:
            client = await self.get_nocodb_client(ctx)
            url = f"/api/v2/meta/tables/{table_id}"

            logger.info("Dropping table '%s'", table_id)
            response = await client.delete(url)

            if not response.is_success:
                await self._handle_api_error(response, "table deletion")

            # Clear schema cache
            self._schema_cache.pop(base_id, None)

            logger.info("Successfully dropped table '%s'", table_id)
            return {
                "success": True,
                "message": f"Table {table_id} dropped successfully",
            }

        except Exception as e:
            error_msg = f"Error dropping table: {str(e)}"
            logger.error(error_msg)
            return {"error": True, "message": error_msg}
        finally:
            if "client" in locals():
                await client.aclose()

    async def add_column(
        self,
        base_id: str,
        table_id: str,
        column_schema: Dict[str, Any],
        ctx: Context = None,
    ) -> Dict[str, Any]:
        """
        Add a new column to an existing table.

        Parameters:
        - base_id: The ID of the NocoDB base
        - table_id: The ID of the table
        - column_schema: Dictionary containing column specification

        Returns:
        - Dictionary containing the created column information

        Example:
        add_column(
            base_id="base123",
            table_id="tbl_xyz",
            column_schema={
                "title": "Phone",
                "column_name": "phone",
                "uidt": "PhoneNumber"
            }
        )
        """
        logger.info("Add column request for table '%s'", table_id)

        if not all([base_id, table_id, column_schema]):
            return {
                "error": True,
                "message": "Base ID, table ID, and column schema are required",
            }

        try:
            # Validate column schema
            validated_column = ColumnSchema(**column_schema)

            client = await self.get_nocodb_client(ctx)
            url = f"/api/v2/meta/tables/{table_id}/columns"

            payload = validated_column.dict()

            logger.info(
                "Adding column '%s' to table '%s'", validated_column.title, table_id
            )
            response = await client.post(url, json=payload)

            if not response.is_success:
                await self._handle_api_error(response, "column addition")

            result = response.json()

            # Clear schema cache
            self._schema_cache.pop(base_id, None)

            logger.info("Successfully added column '%s'", validated_column.title)
            return result

        except Exception as e:
            error_msg = f"Error adding column: {str(e)}"
            logger.error(error_msg)
            return {"error": True, "message": error_msg}
        finally:
            if "client" in locals():
                await client.aclose()

    async def drop_column(
        self, base_id: str, column_id: str, ctx: Context = None
    ) -> Dict[str, Any]:
        """
        Drop (delete) a column from a table.

        Parameters:
        - base_id: The ID of the NocoDB base
        - column_id: The ID of the column to drop

        Returns:
        - Dictionary containing the operation result

        Example:
        drop_column(base_id="base123", column_id="col_xyz")
        """
        logger.info("Drop column request for column '%s'", column_id)

        if not base_id or not column_id:
            return {"error": True, "message": "Base ID and column ID are required"}

        try:
            client = await self.get_nocodb_client(ctx)
            url = f"/api/v2/meta/columns/{column_id}"

            logger.info("Dropping column '%s'", column_id)
            response = await client.delete(url)

            if not response.is_success:
                await self._handle_api_error(response, "column deletion")

            # Clear schema cache
            self._schema_cache.pop(base_id, None)

            logger.info("Successfully dropped column '%s'", column_id)
            return {
                "success": True,
                "message": f"Column {column_id} dropped successfully",
            }

        except Exception as e:
            error_msg = f"Error dropping column: {str(e)}"
            logger.error(error_msg)
            return {"error": True, "message": error_msg}
        finally:
            if "client" in locals():
                await client.aclose()

    # Enhanced DML Operations
    async def upsert_records(
        self,
        base_id: str,
        table_name: str,
        data: List[Dict[str, Any]],
        unique_keys: List[str],
        ctx: Context = None,
    ) -> Dict[str, Any]:
        """
        Upsert records (INSERT or UPDATE based on unique key match).

        Parameters:
        - base_id: The ID of the NocoDB base
        - table_name: Name of the table
        - data: List of records to upsert
        - unique_keys: List of column names that form the unique key

        Returns:
        - Dictionary containing upsert results

        Example:
        upsert_records(
            base_id="base123",
            table_name="customers",
            data=[
                {"email": "john@example.com", "name": "John Doe", "age": 30},
                {"email": "jane@example.com", "name": "Jane Smith", "age": 25}
            ],
            unique_keys=["email"]
        )
        """
        logger.info("Upsert records request for table '%s'", table_name)

        if not all([base_id, table_name, data, unique_keys]):
            return {
                "error": True,
                "message": "All parameters are required for upsert operation",
            }

        try:
            client = await self.get_nocodb_client(ctx)
            table_id = await self.get_table_id(client, base_id, table_name)

            created_count = 0
            updated_count = 0
            errors = []

            for record in data:
                try:
                    # Build filter for unique key lookup
                    filters = []
                    for key in unique_keys:
                        if key in record:
                            filters.append(f"({key},eq,{record[key]})")

                    filter_string = "~and".join(filters) if filters else None

                    # Check if record exists
                    existing_url = f"/api/v2/tables/{table_id}/records"
                    existing_params = (
                        {"where": filter_string, "limit": 1}
                        if filter_string
                        else {"limit": 0}
                    )

                    existing_response = await client.get(
                        existing_url, params=existing_params
                    )
                    existing_response.raise_for_status()
                    existing_data = existing_response.json()

                    if existing_data.get("list") and len(existing_data["list"]) > 0:
                        # Update existing record
                        existing_record = existing_data["list"][0]
                        record_id = existing_record.get("Id") or existing_record.get(
                            "id"
                        )

                        update_url = f"/api/v2/tables/{table_id}/records/{record_id}"
                        update_response = await client.patch(update_url, json=record)
                        update_response.raise_for_status()
                        updated_count += 1
                    else:
                        # Create new record
                        create_url = f"/api/v2/tables/{table_id}/records"
                        create_response = await client.post(create_url, json=record)
                        create_response.raise_for_status()
                        created_count += 1

                except Exception as e:
                    error_msg = f"Error processing record {record}: {str(e)}"
                    errors.append(error_msg)
                    logger.warning("Error processing record during upsert: %s", str(e))

            result = {
                "success": True,
                "created": created_count,
                "updated": updated_count,
                "total_processed": len(data),
                "errors": errors,
            }

            logger.info(
                "Upsert completed: %d created, %d updated, %d errors",
                created_count,
                updated_count,
                len(errors),
            )
            return result

        except Exception as e:
            error_msg = f"Error during upsert operation: {str(e)}"
            logger.error(error_msg)
            return {"error": True, "message": error_msg}
        finally:
            if "client" in locals():
                await client.aclose()

    async def aggregate_data(
        self,
        base_id: str,
        table_name: str,
        aggregations: List[Dict[str, str]],
        filters: Optional[str] = None,
        group_by: Optional[List[str]] = None,
        ctx: Context = None,
    ) -> Dict[str, Any]:
        """
        Perform aggregation operations on table data.

        Parameters:
        - base_id: The ID of the NocoDB base
        - table_name: Name of the table
        - aggregations: List of aggregation specs
                    [{"function": "COUNT|SUM|AVG|MIN|MAX", "column": "column_name"}]
        - filters: Optional filter conditions
        - group_by: Optional list of columns to group by

        Returns:
        - Dictionary containing aggregation results

        Example:
        aggregate_data(
            base_id="base123",
            table_name="orders",
            aggregations=[
                {"function": "COUNT", "column": "*"},
                {"function": "SUM", "column": "amount"},
                {"function": "AVG", "column": "amount"}
            ],
            filters="(status,eq,completed)",
            group_by=["customer_id"]
        )
        """
        logger.info("Aggregate data request for table '%s'", table_name)

        if not all([base_id, table_name, aggregations]):
            return {
                "error": True,
                "message": "Base ID, table name, and aggregations are required",
            }

        try:
            client = await self.get_nocodb_client(ctx)
            table_id = await self.get_table_id(client, base_id, table_name)

            # Retrieve all records that match the filter
            all_records = await self._fetch_all_records(client, table_id, filters)

            # Perform aggregations
            if group_by:
                result = self._group_by_aggregation(all_records, aggregations, group_by)
            else:
                result = self._simple_aggregation(all_records, aggregations)

            result["total_records"] = len(all_records)
            return result

        except Exception as e:
            error_msg = f"Error during aggregation: {str(e)}"
            logger.error(error_msg)
            return {"error": True, "message": error_msg}
        finally:
            if "client" in locals():
                await client.aclose()

    async def bulk_operations(
        self,
        base_id: str,
        table_name: str,
        operations: List[Dict[str, Any]],
        ctx: Context = None,
    ) -> Dict[str, Any]:
        """
        Perform multiple operations in batch.

        Parameters:
        - base_id: The ID of the NocoDB base
        - table_name: Name of the table
        - operations: List of operation specs
                    [{"type": "create|update|delete", "data": {...}, "record_id": "..."}]

        Returns:
        - Dictionary containing bulk operation results

        Example:
        bulk_operations(
            base_id="base123",
            table_name="customers",
            operations=[
                {"type": "create", "data": {"name": "John", "email": "john@example.com"}},
                {"type": "update", "record_id": "rec_123", "data": {"name": "Jane"}},
                {"type": "delete", "record_id": "rec_456"}
            ]
        )
        """
        logger.info("Bulk operations request for table '%s'", table_name)

        if not all([base_id, table_name, operations]):
            return {
                "error": True,
                "message": "Base ID, table name, and operations are required",
            }

        try:
            client = await self.get_nocodb_client(ctx)
            table_id = await self.get_table_id(client, base_id, table_name)

            results = {
                "success": True,
                "created": 0,
                "updated": 0,
                "deleted": 0,
                "errors": [],
            }

            for operation in operations:
                try:
                    op_type = operation.get("type", "").lower()

                    if op_type == "create":
                        url = f"/api/v2/tables/{table_id}/records"
                        response = await client.post(url, json=operation["data"])
                        response.raise_for_status()
                        results["created"] += 1

                    elif op_type == "update":
                        record_id = operation["record_id"]
                        url = f"/api/v2/tables/{table_id}/records/{record_id}"
                        response = await client.patch(url, json=operation["data"])
                        response.raise_for_status()
                        results["updated"] += 1

                    elif op_type == "delete":
                        record_id = operation["record_id"]
                        url = f"/api/v2/tables/{table_id}/records/{record_id}"
                        response = await client.delete(url)
                        response.raise_for_status()
                        results["deleted"] += 1

                    else:
                        results["errors"].append(f"Unknown operation type: {op_type}")

                except Exception as e:
                    error_msg = f"Error in operation {operation}: {str(e)}"
                    results["errors"].append(error_msg)
                    logger.warning("Error in bulk operation: %s", str(e))

            logger.info(
                "Bulk operations completed: %d created, %d updated, %d deleted, %d errors",
                results["created"],
                results["updated"],
                results["deleted"],
                len(results["errors"]),
            )
            return results

        except Exception as e:
            error_msg = f"Error during bulk operations: {str(e)}"
            logger.error(error_msg)
            return {"error": True, "message": error_msg}
        finally:
            if "client" in locals():
                await client.aclose()

    # Helper methods
    async def _fetch_all_records(
        self, client: httpx.AsyncClient, table_id: str, filters: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Fetch all records from a table with optional filtering"""
        url = f"/api/v2/tables/{table_id}/records"
        params = {}
        if filters:
            params["where"] = filters

        all_records = []
        offset = 0
        limit = 1000

        while True:
            params.update({"limit": limit, "offset": offset})
            response = await client.get(url, params=params)
            response.raise_for_status()
            data = response.json()

            records = data.get("list", [])
            if not records:
                break

            all_records.extend(records)

            if len(records) < limit:
                break

            offset += limit

        return all_records

    def _simple_aggregation(
        self, records: List[Dict[str, Any]], aggregations: List[Dict[str, str]]
    ) -> Dict[str, Any]:
        """Perform simple aggregation without grouping"""
        result = {"success": True}

        for agg in aggregations:
            func = agg["function"].upper()
            col = agg["column"]

            if func == "COUNT":
                result[f"{func}_{col}"] = len(records)
            elif col != "*":
                values = self._extract_numeric_values(records, col)

                if values:
                    if func == "SUM":
                        result[f"{func}_{col}"] = sum(values)
                    elif func == "AVG":
                        result[f"{func}_{col}"] = sum(values) / len(values)
                    elif func == "MIN":
                        result[f"{func}_{col}"] = min(values)
                    elif func == "MAX":
                        result[f"{func}_{col}"] = max(values)

        return result

    def _group_by_aggregation(
        self,
        records: List[Dict[str, Any]],
        aggregations: List[Dict[str, str]],
        group_by: List[str],
    ) -> Dict[str, Any]:
        """Perform aggregation with grouping"""
        groups = defaultdict(list)

        for record in records:
            group_key = tuple(str(record.get(col, "")) for col in group_by)
            groups[group_key].append(record)

        results = []
        for group_key, group_records in groups.items():
            group_result = dict(zip(group_by, group_key))

            for agg in aggregations:
                func = agg["function"].upper()
                col = agg["column"]

                if func == "COUNT":
                    group_result[f"{func}_{col}"] = len(group_records)
                elif col != "*":
                    values = self._extract_numeric_values(group_records, col)

                    if values:
                        if func == "SUM":
                            group_result[f"{func}_{col}"] = sum(values)
                        elif func == "AVG":
                            group_result[f"{func}_{col}"] = sum(values) / len(values)
                        elif func == "MIN":
                            group_result[f"{func}_{col}"] = min(values)
                        elif func == "MAX":
                            group_result[f"{func}_{col}"] = max(values)

            results.append(group_result)

        return {"success": True, "grouped_results": results}

    def _extract_numeric_values(
        self, records: List[Dict[str, Any]], column: str
    ) -> List[float]:
        """Extract numeric values from records for a specific column"""
        values = []
        for record in records:
            value = record.get(column)
            if value is not None:
                try:
                    # Try to convert to float
                    if isinstance(value, (int, float)):
                        values.append(float(value))
                    elif (
                        isinstance(value, str)
                        and value.replace(".", "").replace("-", "").isdigit()
                    ):
                        values.append(float(value))
                except (ValueError, TypeError):
                    continue  # Skip non-numeric values
        return values

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
        ctx: Context = None,
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
        logger.info(
            "Retrieve records request for table '%s' in base '%s'", table_name, base_id
        )

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
        table_name = " ".join(word.capitalize() for word in table_name.split(" "))

        # Log query parameters for debugging
        if logger.isEnabledFor(logging.DEBUG):
            params_info = {
                "row_id": row_id,
                "filters": filters,
                "limit": limit,
                "offset": offset,
                "sort": sort,
                "fields": fields,
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
                logger.info(
                    "Retrieved %d record from table '%s'", record_count, table_name
                )
            else:
                # For multiple records retrieval
                records = result.get("list", [])
                record_count = len(records)
                logger.info(
                    "Retrieved %d records from table '%s'", record_count, table_name
                )

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
                "message": f"HTTP error: {e.response.text}",
            }
        except Exception as e:
            error_msg = f"Error retrieving records from '{table_name}': {str(e)}"
            logger.error(error_msg)
            if logger.isEnabledFor(logging.DEBUG):
                import traceback

                logger.debug(traceback.format_exc())
            return {"error": True, "message": f"Error: {str(e)}"}
        finally:
            if "client" in locals():
                await client.aclose()

    async def create_records(
        self,
        base_id: str,
        table_name: str,
        data: Dict[str, Any],
        bulk: bool = False,
        ctx: Context = None,
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
        logger.info(
            "Create records request for table '%s' in base '%s'", table_name, base_id
        )

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
        original_data = data  # Keep a reference before potential modification
        if bulk:
            if not isinstance(data, list):
                logger.warning(
                    "Bulk creation requested but data is not a list, converting single record to list"
                )
                data = [data]
            elif not data:  # Handle empty list for bulk
                error_msg = "Data list cannot be empty for bulk creation"
                logger.error(error_msg)
                return {"error": True, "message": error_msg}
        elif isinstance(data, list):
            logger.warning(
                "Single record creation requested but data is a list, using first item only"
            )
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
            logger.error("Request Data: %s", data)  # Log data on error
            if logger.isEnabledFor(logging.DEBUG):
                logger.debug("Response body: %s", e.response.text)
            return {
                "error": True,
                "status_code": e.response.status_code,
                "message": f"HTTP error: {e.response.text}",
            }
        except ValueError as e:  # Catch errors from get_table_id or data validation
            error_msg = f"Error creating records in '{table_name}': {str(e)}"
            logger.error(error_msg)
            return {"error": True, "message": error_msg}
        except Exception as e:
            error_msg = f"Error creating records in '{table_name}': {str(e)}"
            logger.error(error_msg)
            if logger.isEnabledFor(logging.DEBUG):
                import traceback

                logger.debug(traceback.format_exc())
            return {"error": True, "message": f"Error: {str(e)}"}
        finally:
            if "client" in locals():
                await client.aclose()

    async def update_records(
        self,
        base_id: str,
        table_name: str,
        row_id: Optional[str] = None,
        data: Dict[str, Any] = None,
        bulk: bool = False,
        bulk_ids: Optional[List[str]] = None,
        ctx: Context = None,
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
        logger.info(
            "Update records request for table '%s' in base '%s'", table_name, base_id
        )

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
                return {"error": True, "message": error_msg}

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
                "message": f"HTTP error: {e.response.text}",
            }
        except Exception as e:
            error_msg = f"Error updating records in '{table_name}': {str(e)}"
            logger.error(error_msg)
            if logger.isEnabledFor(logging.DEBUG):
                import traceback

                logger.debug(traceback.format_exc())
            return {"error": True, "message": f"Error: {str(e)}"}
        finally:
            if "client" in locals():
                await client.aclose()

    async def delete_records(
        self,
        base_id: str,
        table_name: str,
        row_id: Optional[str] = None,
        bulk: bool = False,
        bulk_ids: Optional[List[str]] = None,
        ctx: Context = None,
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
        logger.info(
            "Delete records request for table '%s' in base '%s'", table_name, base_id
        )

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
        table_name = " ".join(word.capitalize() for word in table_name.split(" "))

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
                response = await client.request(
                    "DELETE", url, json={"ids": bulk_ids}
                )  # Use explicit DELETE with body
            elif row_id:
                # Single record deletion endpoint
                url = f"/api/v2/tables/{table_id}/records/{row_id}"
                logger.info("Deleting record with ID: %s", row_id)
                response = await client.delete(url)
            else:
                error_msg = "Either row_id (for single deletion) or bulk=True with bulk_ids (for bulk deletion) must be provided"
                logger.error(error_msg)
                return {"error": True, "message": error_msg}

            # Handle response
            response.raise_for_status()

            # Delete operations may return 200 or 204 with different body content
            if response.status_code == 204:  # No content
                result = {"success": True, "message": "Record(s) deleted successfully"}
            else:
                try:
                    result = response.json()
                    # NocoDB bulk delete might return a number (count) or an object
                    if isinstance(result, (int, float)):
                        result = {
                            "success": True,
                            "message": f"{result} record(s) deleted successfully",
                        }
                    elif not isinstance(result, dict):  # Handle unexpected formats
                        result = {
                            "success": True,
                            "message": "Record(s) deleted successfully",
                            "response_data": result,
                        }

                except json.JSONDecodeError:
                    logger.warning(
                        "Delete operation returned non-empty, non-JSON response body"
                    )
                    result = {
                        "success": True,
                        "message": "Record(s) deleted successfully (non-JSON response)",
                    }

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
                "message": f"HTTP error: {e.response.text}",
            }
        except Exception as e:
            error_msg = f"Error deleting records from '{table_name}': {str(e)}"
            logger.error(error_msg)
            if logger.isEnabledFor(logging.DEBUG):
                import traceback

                logger.debug(traceback.format_exc())
            return {"error": True, "message": f"Error: {str(e)}"}
        finally:
            if "client" in locals():
                await client.aclose()

    async def get_schema(
        self, base_id: str, table_name: str, ctx: Context = None
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
        logger.info(
            "Get schema request for table '%s' in base '%s'", table_name, base_id
        )

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
            logger.info(
                "Retrieving schema for table ID: %s using url %s", table_id, url
            )

            response = await client.get(url)
            response.raise_for_status()

            result = response.json()

            # Log success and potentially the number of columns found
            columns = result.get("columns", [])
            logger.info(
                "Successfully retrieved schema for table '%s'. Found %d columns.",
                table_name,
                len(columns),
            )
            if logger.isEnabledFor(logging.DEBUG):
                logger.debug(
                    "Schema details: %s", result
                )  # Log full schema for debugging if needed

            return result  # Return the full table metadata which includes the columns

        except httpx.HTTPStatusError as e:
            error_msg = f"HTTP error {e.response.status_code} retrieving schema for '{table_name}'"
            logger.error(error_msg)
            if logger.isEnabledFor(logging.DEBUG):
                logger.debug("Response body: %s", e.response.text)
            return {
                "error": True,
                "status_code": e.response.status_code,
                "message": f"HTTP error: {e.response.text}",
            }
        except ValueError as e:  # Catch errors from get_table_id
            error_msg = f"Error retrieving schema for '{table_name}': {str(e)}"
            logger.error(error_msg)
            return {"error": True, "message": error_msg}
        except Exception as e:
            error_msg = f"Error retrieving schema for '{table_name}': {str(e)}"
            logger.error(error_msg)
            if logger.isEnabledFor(logging.DEBUG):
                import traceback

                logger.debug(traceback.format_exc())
            return {"error": True, "message": f"Error: {str(e)}"}
        finally:
            if "client" in locals():
                await client.aclose()

    async def list_tables(self, base_id: str, ctx: Context = None) -> Dict[str, Any]:
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

            logger.info(
                "Successfully retrieved %d tables from base '%s'", len(tables), base_id
            )
            if logger.isEnabledFor(logging.DEBUG):
                table_names = [t.get("title") for t in tables]
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
                "message": f"HTTP error: {e.response.text}",
            }
        except Exception as e:
            error_msg = f"Error retrieving tables from base '{base_id}': {str(e)}"
            logger.error(error_msg)
            if logger.isEnabledFor(logging.DEBUG):
                import traceback

                logger.debug(traceback.format_exc())
            return {"error": True, "message": f"Error: {str(e)}"}
        finally:
            if "client" in locals():
                await client.aclose()

    async def alter_table(
        self,
        base_id: str,
        table_id: str,
        alterations: Dict[str, Any],
        ctx: Context = None,
    ) -> Dict[str, Any]:
        """
        ALTER: Modify the structure of existing database objects.
        Parameters:
        - base_id: The ID of the NocoDB base
        - table_id: The ID of the table to alter
        - alterations: Dictionary containing the alterations to apply
                    {"title": "New Table Name", "description": "New description"}

        Returns:
        - Dictionary containing the operation result

        Example:
        alter_table(
            base_id="base123",
            table_id="tbl_xyz",
            alterations={
                "title": "Updated Customers",
                "description": "Customer information table - updated"
            }
        )
        """
        logger.info("Alter table request for table '%s'", table_id)

        if not all([base_id, table_id, alterations]):
            return {
                "error": True,
                "message": "Base ID, table ID, and alterations are required",
            }

        try:
            client = await self.get_nocodb_client(ctx)
            url = f"/api/v2/meta/tables/{table_id}"

            logger.info("Altering table '%s' with changes: %s", table_id, alterations)
            response = await client.patch(url, json=alterations)

            if not response.is_success:
                await self._handle_api_error(response, "table alteration")

            result = response.json()

            # Clear schema cache
            self._schema_cache.pop(base_id, None)

            logger.info("Successfully altered table '%s'", table_id)
            return result

        except Exception as e:
            error_msg = f"Error altering table: {str(e)}"
            logger.error(error_msg)
            return {"error": True, "message": error_msg}
        finally:
            if "client" in locals():
                await client.aclose()

    async def rename_table(
        self, base_id: str, table_id: str, new_name: str, ctx: Context = None
    ) -> Dict[str, Any]:
        """
        RENAME: Rename database objects (table).
        Parameters:
        - base_id: The ID of the NocoDB base
        - table_id: The ID of the table to rename
        - new_name: The new name for the table

        Returns:
        - Dictionary containing the operation result

        Example:
        rename_table(base_id="base123", table_id="tbl_xyz", new_name="Updated Customers")
        """
        logger.info("Rename table request for table '%s' to '%s'", table_id, new_name)

        if not all([base_id, table_id, new_name]):
            return {
                "error": True,
                "message": "Base ID, table ID, and new name are required",
            }

        try:
            client = await self.get_nocodb_client(ctx)
            url = f"/api/v2/meta/tables/{table_id}"

            payload = {"title": new_name}

            logger.info("Renaming table '%s' to '%s'", table_id, new_name)
            response = await client.patch(url, json=payload)

            if not response.is_success:
                await self._handle_api_error(response, "table rename")

            result = response.json()

            # Clear schema cache
            self._schema_cache.pop(base_id, None)

            logger.info("Successfully renamed table '%s' to '%s'", table_id, new_name)
            return result

        except Exception as e:
            error_msg = f"Error renaming table: {str(e)}"
            logger.error(error_msg)
            return {"error": True, "message": error_msg}
        finally:
            if "client" in locals():
                await client.aclose()

    async def rename_column(
        self, base_id: str, column_id: str, new_name: str, ctx: Context = None
    ) -> Dict[str, Any]:
        """
        RENAME: Rename database objects (column).
        Parameters:
        - base_id: The ID of the NocoDB base
        - column_id: The ID of the column to rename
        - new_name: The new name for the column

        Returns:
        - Dictionary containing the operation result

        Example:
        rename_column(base_id="base123", column_id="col_xyz", new_name="Customer Name")
        """
        logger.info(
            "Rename column request for column '%s' to '%s'", column_id, new_name
        )

        if not all([base_id, column_id, new_name]):
            return {
                "error": True,
                "message": "Base ID, column ID, and new name are required",
            }

        try:
            client = await self.get_nocodb_client(ctx)
            url = f"/api/v2/meta/columns/{column_id}"

            payload = {"title": new_name}

            logger.info("Renaming column '%s' to '%s'", column_id, new_name)
            response = await client.patch(url, json=payload)

            if not response.is_success:
                await self._handle_api_error(response, "column rename")

            result = response.json()

            # Clear schema cache
            self._schema_cache.pop(base_id, None)

            logger.info("Successfully renamed column '%s' to '%s'", column_id, new_name)
            return result

        except Exception as e:
            error_msg = f"Error renaming column: {str(e)}"
            logger.error(error_msg)
            return {"error": True, "message": error_msg}
        finally:
            if "client" in locals():
                await client.aclose()

    async def alter_column(
        self,
        base_id: str,
        column_id: str,
        column_changes: Dict[str, Any],
        ctx: Context = None,
    ) -> Dict[str, Any]:
        """
        ALTER: Modify the structure of existing database objects (column).
        Parameters:
        - base_id: The ID of the NocoDB base
        - column_id: The ID of the column to alter
        - column_changes: Dictionary containing the changes to apply
                        {"title": "New Name", "uidt": "Email", "meta": {...}}

        Returns:
        - Dictionary containing the operation result

        Example:
        alter_column(
            base_id="base123",
            column_id="col_xyz",
            column_changes={
                "title": "Email Address",
                "uidt": "Email",
                "meta": {"validate": True}
            }
        )
        """
        logger.info("Alter column request for column '%s'", column_id)

        if not all([base_id, column_id, column_changes]):
            return {
                "error": True,
                "message": "Base ID, column ID, and changes are required",
            }

        try:
            client = await self.get_nocodb_client(ctx)
            url = f"/api/v2/meta/columns/{column_id}"

            logger.info(
                "Altering column '%s' with changes: %s", column_id, column_changes
            )
            response = await client.patch(url, json=column_changes)

            if not response.is_success:
                await self._handle_api_error(response, "column alteration")

            result = response.json()

            # Clear schema cache
            self._schema_cache.pop(base_id, None)

            logger.info("Successfully altered column '%s'", column_id)
            return result

        except Exception as e:
            error_msg = f"Error altering column: {str(e)}"
            logger.error(error_msg)
            return {"error": True, "message": error_msg}
        finally:
            if "client" in locals():
                await client.aclose()

    async def truncate_table(
        self, base_id: str, table_name: str, ctx: Context = None
    ) -> Dict[str, Any]:
        """
        TRUNCATE: Remove all records from a table, but keep the table structure.
        Parameters:
        - base_id: The ID of the NocoDB base
        - table_name: Name of the table to truncate

        Returns:
        - Dictionary containing the operation result

        Example:
        truncate_table(base_id="base123", table_name="customers")
        """
        logger.info("Truncate table request for table '%s'", table_name)

        if not all([base_id, table_name]):
            return {"error": True, "message": "Base ID and table name are required"}

        try:
            client = await self.get_nocodb_client(ctx)
            table_id = await self.get_table_id(client, base_id, table_name)

            # Get all records first to delete them
            all_records = await self._fetch_all_records(client, table_id)

            if not all_records:
                logger.info("Table '%s' is already empty", table_name)
                return {
                    "success": True,
                    "message": f"Table {table_name} was already empty",
                    "records_deleted": 0,
                }

            # Extract record IDs
            record_ids = []
            for record in all_records:
                record_id = record.get("Id") or record.get("id")
                if record_id:
                    record_ids.append(str(record_id))

            if not record_ids:
                return {
                    "success": True,
                    "message": f"No records found to delete in table {table_name}",
                    "records_deleted": 0,
                }

            # Delete all records in bulk
            url = f"/api/v2/tables/{table_id}/records/bulk"
            logger.info(
                "Truncating table '%s' - deleting %d records",
                table_name,
                len(record_ids),
            )

            response = await client.request("DELETE", url, json={"ids": record_ids})

            if not response.is_success:
                await self._handle_api_error(response, "table truncation")

            logger.info(
                "Successfully truncated table '%s' - deleted %d records",
                table_name,
                len(record_ids),
            )
            return {
                "success": True,
                "message": f"Table {table_name} truncated successfully",
                "records_deleted": len(record_ids),
            }

        except Exception as e:
            error_msg = f"Error truncating table: {str(e)}"
            logger.error(error_msg)
            return {"error": True, "message": error_msg}
        finally:
            if "client" in locals():
                await client.aclose()

    async def add_table_comment(
        self, base_id: str, table_id: str, comment: str, ctx: Context = None
    ) -> Dict[str, Any]:
        """
        COMMENT: Add comments to data dictionary (table).
        Parameters:
        - base_id: The ID of the NocoDB base
        - table_id: The ID of the table
        - comment: The comment/description to add

        Returns:
        - Dictionary containing the operation result

        Example:
        add_table_comment(
            base_id="base123",
            table_id="tbl_xyz",
            comment="This table stores customer information including contact details"
        )
        """
        logger.info("Add table comment request for table '%s'", table_id)

        if not all([base_id, table_id, comment]):
            return {
                "error": True,
                "message": "Base ID, table ID, and comment are required",
            }

        try:
            client = await self.get_nocodb_client(ctx)
            url = f"/api/v2/meta/tables/{table_id}"

            payload = {"description": comment}

            logger.info("Adding comment to table '%s': %s", table_id, comment)
            response = await client.patch(url, json=payload)

            if not response.is_success:
                await self._handle_api_error(response, "table comment addition")

            result = response.json()

            # Clear schema cache
            self._schema_cache.pop(base_id, None)

            logger.info("Successfully added comment to table '%s'", table_id)
            return result

        except Exception as e:
            error_msg = f"Error adding table comment: {str(e)}"
            logger.error(error_msg)
            return {"error": True, "message": error_msg}
        finally:
            if "client" in locals():
                await client.aclose()

    async def add_column_comment(
        self, base_id: str, column_id: str, comment: str, ctx: Context = None
    ) -> Dict[str, Any]:
        """
        COMMENT: Add comments to data dictionary (column).
        Parameters:
        - base_id: The ID of the NocoDB base
        - column_id: The ID of the column
        - comment: The comment/description to add

        Returns:
        - Dictionary containing the operation result

        Example:
        add_column_comment(
            base_id="base123",
            column_id="col_xyz",
            comment="Customer email address - must be unique and valid format"
        )
        """
        logger.info("Add column comment request for column '%s'", column_id)

        if not all([base_id, column_id, comment]):
            return {
                "error": True,
                "message": "Base ID, column ID, and comment are required",
            }

        try:
            client = await self.get_nocodb_client(ctx)
            url = f"/api/v2/meta/columns/{column_id}"

            # In NocoDB, column comments are typically stored in meta.description
            payload = {"meta": {"description": comment}}

            logger.info("Adding comment to column '%s': %s", column_id, comment)
            response = await client.patch(url, json=payload)

            if not response.is_success:
                await self._handle_api_error(response, "column comment addition")

            result = response.json()

            # Clear schema cache
            self._schema_cache.pop(base_id, None)

            logger.info("Successfully added comment to column '%s'", column_id)
            return result

        except Exception as e:
            error_msg = f"Error adding column comment: {str(e)}"
            logger.error(error_msg)
            return {"error": True, "message": error_msg}
        finally:
            if "client" in locals():
                await client.aclose()
