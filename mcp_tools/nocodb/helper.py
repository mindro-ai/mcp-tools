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
    dtxp: Optional[str] = None  # Data type extra parameters (length, precision)
    np: Optional[str] = None  # Nullable/Not null
    pk: Optional[bool] = False  # Primary key
    ai: Optional[bool] = False  # Auto increment

    def __init__(self, **data):
        # Auto-populate dt and dtxp if not provided
        if 'dt' not in data or data['dt'] is None:
            uidt = data.get('uidt', '')
            dt_mapping = {
                'SingleLineText': 'varchar',
                'LongText': 'text',
                'Number': 'int',
                'Decimal': 'decimal',
                'Currency': 'decimal',
                'Percent': 'decimal',
                'Duration': 'int',
                'Rating': 'int',
                'Checkbox': 'boolean',
                'MultiSelect': 'text',
                'SingleSelect': 'varchar',
                'Date': 'date',
                'DateTime': 'datetime',
                'Time': 'time',
                'Year': 'year',
                'PhoneNumber': 'varchar',
                'Email': 'varchar',
                'URL': 'varchar',
                'Attachment': 'text',
                'JSON': 'json',
                'SpecificDBType': 'varchar',
            }
            data['dt'] = dt_mapping.get(uidt, 'varchar')

        # Auto-populate dtxp if not provided
        if 'dtxp' not in data or data['dtxp'] is None:
            dt = data.get('dt', '')
            uidt = data.get('uidt', '')
            
            if dt == 'varchar':
                data['dtxp'] = '255'
            elif dt == 'decimal':
                data['dtxp'] = '10,2'
            elif dt == 'int':
                data['dtxp'] = '11'
            elif dt == 'text':
                data['dtxp'] = ''
            else:
                data['dtxp'] = ''

        super().__init__(**data)

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

    def __init__(self, **data):
        # Auto-generate table_name from title if not provided
        if 'table_name' not in data and 'title' in data:
            data['table_name'] = data['title'].lower().replace(' ', '_').replace('-', '_')
        
        # Auto-generate column_name from title for each column if not provided
        if 'columns' in data:
            for col in data['columns']:
                if 'column_name' not in col and 'title' in col:
                    col['column_name'] = col['title'].lower().replace(' ', '_').replace('-', '_')
        
        super().__init__(**data)