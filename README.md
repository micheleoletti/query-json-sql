# SQLite Utils REST API

A simple FastAPI service that allows you to query JSON data using SQL. The service loads data into an in-memory SQLite database and executes SQL queries against it, returning results as JSON.

## Why

Currently experimenting with N8N MPC servers, and I didn't really find a way to let an LLM make smart queries to data.

One of the automations that I'm building is tracking my workout sets in the gym, and currently I can't ask `"what is my bench press PR"`, because the MCP tool would just **fetch all the records from the Google Sheet and feed that into the LLM context**.

There I basically need to pray that:

- the JSON payload does not break the selected model context window
- the selected model is smart enough to somehow give me the right answer while reasoning over that stringified JSON data

This is suboptimal and definitely not scalable.

A simple option would be custom tool like `get_exercise_pr(exercise_name)`, but that would require me to think ahead of time all the possible use cases and limit the expressiveness of the LLM.

Instead we could provide a way to:

- fetch the data that it needs (MCP tool)
- **write itself an query to manipulate the data**

Considering that LLMs speak SQL quite decently, I thought that this would be quite cheap and fast to test out.

## Quick Start

### Using Docker Compose (Recommended)

```bash
# Clone and start the service
git clone https://github.com/micheleoletti/c
cd query-json-sql
docker-compose up --build
```

The service will be available at `http://localhost:8000`

### Using Docker

```bash
# Build the image
docker build -t query-json-sql .

# Run the container
docker run -p 8000:8000 query-json-sql
```

### Local Development

```bash
# Create and activate virtual environment
python3 -m venv venv
source venv/bin/activate

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

### GET `/health`

Health check endpoint for monitoring and load balancers.

**Response:**

```json
{
  "status": "healthy"
}
```

### POST `/query`

Execute SQL queries against JSON data with full input validation.

**Request Body (Pydantic validated):**

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

**Validation:**

- `data`: Must be a non-empty list of dictionaries
- `sql`: Must be a non-empty string

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
       "sql": "SELECT * FROM data WHERE content LIKE '\''%apple%'\'' ORDER BY timestamp DESC"
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
       "sql": "SELECT name, age FROM data WHERE city = '\''New York'\'' AND age > 28"
     }'
```
