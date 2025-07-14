from fastapi import FastAPI, Request, HTTPException
from pydantic import BaseModel
import sqlite3
import pandas as pd
from typing import List, Dict, Any
import logging

app = FastAPI(
    title="SQLite Utils REST API",
    description="A REST API for querying JSON data using SQL",
    version="1.0.0",
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class QueryRequest(BaseModel):
    data: List[Dict[str, Any]]
    sql: str


@app.get("/health")
async def health_check():
    return {"status": "healthy"}


@app.post("/query")
async def query_json(request: QueryRequest):
    try:
        # Validate inputs
        if not request.data:
            raise HTTPException(status_code=400, detail="Data cannot be empty")
        if not request.sql.strip():
            raise HTTPException(status_code=400, detail="SQL query cannot be empty")

        # Create DataFrame and load into SQLite
        df = pd.DataFrame(request.data)
        conn = sqlite3.connect(":memory:")
        df.to_sql("data", conn, index=False, if_exists="replace")

        # Execute query
        result = pd.read_sql_query(request.sql, conn)
        conn.close()

        logger.info(f"Query executed successfully. Returned {len(result)} rows.")
        return result.to_dict(orient="records")

    except pd.errors.DatabaseError as e:
        logger.error(f"Database error: {str(e)}")
        raise HTTPException(status_code=400, detail=f"SQL execution error: {str(e)}")
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")
