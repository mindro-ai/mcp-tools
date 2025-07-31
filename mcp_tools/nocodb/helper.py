from typing import Dict, List, Optional, Union, Any
from pydantic import BaseModel, Field, validator



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


