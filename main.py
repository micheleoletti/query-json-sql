from fastapi import FastAPI, Request, HTTPException
from pydantic import BaseModel
import sqlite3
import pandas as pd
from typing import List, Dict, Any, Union
import logging

app = FastAPI(
    title="Query JSON by SQL",
    description="A REST API for querying JSON data using SQL.",
    version="1.0.0",
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class QueryRequest(BaseModel):
    data: List[Dict[str, Any]]
    sql: str
    flatten_columns: bool = False


class SchemaRequest(BaseModel):
    data: List[Dict[str, Any]]


def unflatten_data(
    flattened_rows: List[Dict[str, Any]], column_mapping: Dict[str, str]
) -> List[Dict[str, Any]]:
    """
    Convert flattened column names back to nested structure using the column mapping.

    Args:
        flattened_rows: List of dictionaries with flattened column names
        column_mapping: Mapping from flattened column names to original column names

    Returns:
        List of dictionaries with original nested structure
    """
    result = []

    for row in flattened_rows:
        nested_row = {}

        for flattened_key, value in row.items():
            # Get the original column name from mapping
            original_key = column_mapping.get(flattened_key, flattened_key)

            # Split by dots to get nested path
            parts = original_key.split(".")

            # Build nested structure
            current = nested_row
            for part in parts[:-1]:
                if part not in current:
                    current[part] = {}
                current = current[part]

            # Set the final value
            current[parts[-1]] = value

        result.append(nested_row)

    return result


def validate_no_arrays(obj: Union[Dict, List, Any], path: str = "root") -> None:
    """
    Recursively validate that the object contains no arrays.
    Only allows objects (dicts) and primitive values (str, int, float, bool, None).

    Args:
        obj: The object to validate
        path: Current path in the object (for error messages)

    Raises:
        HTTPException: If arrays are found in the structure
    """
    if isinstance(obj, list):
        raise HTTPException(
            status_code=400,
            detail=f"Arrays are not supported. Found array at '{path}'. "
            f"Please use object nesting only (no arrays of objects).",
        )
    elif isinstance(obj, dict):
        for key, value in obj.items():
            new_path = f"{path}.{key}" if path != "root" else key
            validate_no_arrays(value, new_path)
    # Primitive values (str, int, float, bool, None) are allowed


def validate_data_structure(data: List[Dict[str, Any]]) -> None:
    """
    Validate that the entire data structure contains no arrays.

    Args:
        data: List of dictionaries to validate

    Raises:
        HTTPException: If validation fails
    """
    if not isinstance(data, list):
        raise HTTPException(status_code=400, detail="Data must be a list of objects")

    for i, item in enumerate(data):
        if not isinstance(item, dict):
            raise HTTPException(
                status_code=400,
                detail=f"Item at index {i} must be an object, got {type(item).__name__}",
            )
        validate_no_arrays(item, f"data[{i}]")


@app.get("/")
async def root():
    return {"message": "Query JSON SQL API", "status": "healthy"}


@app.get("/health")
async def health_check():
    return {"status": "healthy"}


@app.post("/get-schema")
async def get_flattened_table_columns(request: SchemaRequest):
    """
    Get the flattened schema information for the provided JSON data.
    This helps MCP tools understand the column structure before writing SQL queries.
    Only supports object nesting - no arrays allowed.
    """
    try:
        # Validate inputs
        if not request.data:
            raise HTTPException(status_code=400, detail="Data cannot be empty")

        # Validate no arrays in the structure
        validate_data_structure(request.data)

        # Flatten the data using pandas json_normalize
        df = pd.json_normalize(request.data)

        # Clean up column names to be more SQL-friendly
        original_columns = df.columns.tolist()
        df.columns = [
            col.replace(".", "_").replace("[", "").replace("]", "")
            for col in df.columns
        ]
        cleaned_columns = df.columns.tolist()

        # Create column mapping for reference
        column_mapping = dict(zip(original_columns, cleaned_columns))

        schema_info = {
            "columns": cleaned_columns,
            "column_mapping": column_mapping,
        }

        logger.info(
            f"Schema generated successfully for {len(df)} rows with {len(df.columns)} columns."
        )
        return schema_info

    except HTTPException:
        # Re-raise validation errors as-is
        raise
    except Exception as e:
        logger.error(f"Schema generation error: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"Schema generation error: {str(e)}"
        )


@app.post("/query")
async def query_json(request: QueryRequest):
    try:
        # Validate inputs
        if not request.data:
            raise HTTPException(status_code=400, detail="Data cannot be empty")
        if not request.sql.strip():
            raise HTTPException(status_code=400, detail="SQL query cannot be empty")

        # Validate no arrays in the structure
        validate_data_structure(request.data)

        # Flatten the data using pandas json_normalize (same as schema endpoint)
        df = pd.json_normalize(request.data)

        # Store original column names for potential unflattering
        original_columns = df.columns.tolist()

        # Clean up column names to match schema endpoint
        df.columns = [
            col.replace(".", "_").replace("[", "").replace("]", "")
            for col in df.columns
        ]

        # Create column mapping for unflattering
        column_mapping = dict(zip(df.columns.tolist(), original_columns))

        # Create DataFrame and load into SQLite
        conn = sqlite3.connect(":memory:")
        df.to_sql("data", conn, index=False, if_exists="replace")

        # Execute query
        result = pd.read_sql_query(request.sql, conn)
        conn.close()

        # Convert to list of dictionaries
        result_data = result.to_dict(orient="records")

        # If flatten_columns is False, restore original nested structure
        if not request.flatten_columns:
            result_data = unflatten_data(result_data, column_mapping)

        logger.info(f"Query executed successfully. Returned {len(result_data)} rows.")
        return result_data

    except HTTPException:
        # Re-raise validation errors as-is
        raise
    except pd.errors.DatabaseError as e:
        logger.error(f"Database error: {str(e)}")
        raise HTTPException(status_code=400, detail=f"SQL execution error: {str(e)}")
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")
