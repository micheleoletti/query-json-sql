# SQLite Utils REST API

A simple FastAPI service that allows you to query JSON data using SQL. The service loads data into an in-memory SQLite database and executes SQL queries against it, returning results as JSON.

## Features

- 🚀 **Zero State**: All operations use in-memory SQLite databases per request
- 🔄 **One-Shot**: No persistent database management required
- 🎯 **Total Control**: Full control over data structure, schema, and queries
- 🤖 **LLM-Friendly**: Simple REST API that can be easily integrated with AI workflows

## Quick Start

### Using Docker Compose (Recommended)

```bash
# Clone and start the service
git clone <your-repo-url>
cd sqlite-utils-rest
docker-compose up --build
```

The service will be available at `http://localhost:8000`

### Using Docker

```bash
# Build the image
docker build -t sqlite-utils-rest .

# Run the container
docker run -p 8000:8000 sqlite-utils-rest
```

### Local Development

```bash
# Install dependencies
pip install -r requirements.txt

# Run the development server
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

## API Documentation

Once the service is running, visit:

- **Interactive API Docs**: `http://localhost:8000/docs`
- **ReDoc Documentation**: `http://localhost:8000/redoc`

## Endpoints

### POST `/query`

Execute SQL queries against JSON data.

**Request Body:**

```json
{
  "data": [
    { "column1": "value1", "column2": "value2" },
    { "column1": "value3", "column2": "value4" }
  ],
  "sql": "SELECT * FROM data WHERE column1 = 'value1'"
}
```

**Response:**

```json
[{ "column1": "value1", "column2": "value2" }]
```

### GET `/health`

Health check endpoint.

**Response:**

```json
{ "status": "healthy" }
```

## Usage Examples

### Basic Query

```bash
curl -X POST "http://localhost:8000/query" \
     -H "Content-Type: application/json" \
     -d '{
       "data": [
         {"timestamp": "2024-01-01", "content": "Ate apple pie"},
         {"timestamp": "2024-01-02", "content": "Ate banana"}
       ],
       "sql": "SELECT * FROM data WHERE content LIKE '%apple%' ORDER BY timestamp DESC"
     }'
```

### Aggregation Query

```bash
curl -X POST "http://localhost:8000/query" \
     -H "Content-Type: application/json" \
     -d '{
       "data": [
         {"category": "food", "amount": 25.50},
         {"category": "food", "amount": 12.30},
         {"category": "transport", "amount": 15.00}
       ],
       "sql": "SELECT category, SUM(amount) as total FROM data GROUP BY category"
     }'
```

### Complex Filtering

```bash
curl -X POST "http://localhost:8000/query" \
     -H "Content-Type: application/json" \
     -d '{
       "data": [
         {"name": "Alice", "age": 30, "city": "New York"},
         {"name": "Bob", "age": 25, "city": "San Francisco"},
         {"name": "Charlie", "age": 35, "city": "New York"}
       ],
       "sql": "SELECT name, age FROM data WHERE city = \"New York\" AND age > 28"
     }'
```

## Error Handling

The API provides clear error messages for common issues:

- **400 Bad Request**: Invalid SQL syntax, empty data, or missing required fields
- **500 Internal Server Error**: Unexpected server errors

Example error response:

```json
{
  "detail": "SQL execution error: no such column: invalid_column"
}
```

## Technical Details

- **Framework**: FastAPI with Pydantic validation
- **Database**: In-memory SQLite (per request)
- **Data Processing**: Pandas DataFrames
- **Table Name**: Data is always loaded into a table called `data`
- **Port**: 8000 (configurable via environment variables)

## Why This Approach?

✅ **Better than database hacks because:**

- Zero state management - each request is isolated
- No persistent database setup or maintenance
- Complete control over data structure and validation
- Perfect for AI/LLM integration workflows
- Lightweight and fast for ad-hoc data analysis

## Development

### Project Structure

```
sqlite-utils-rest/
├── main.py              # FastAPI application
├── requirements.txt     # Python dependencies
├── Dockerfile          # Container configuration
├── docker-compose.yml  # Docker Compose setup
├── .gitignore          # Git ignore patterns
└── README.md           # This file
```

### Adding Features

The service is designed to be easily extensible. You can:

1. Add new endpoints in `main.py`
2. Enhance data validation with Pydantic models
3. Add custom SQL functions or data transformations
4. Implement authentication/authorization
5. Add support for multiple table operations

## License

[Add your license here]

## Contributing

[Add contribution guidelines here]
# query-json-sql
