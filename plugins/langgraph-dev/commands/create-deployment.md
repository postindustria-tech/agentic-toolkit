---
name: create-deployment
description: Generate FastAPI deployment code for LangGraph workflow with async execution
argument-hint: graph_file [--include-monitoring]
allowed-tools:
  - Read
  - Write
  - Grep
  - AskUserQuestion
---

# Create FastAPI Deployment

Generate production-ready FastAPI deployment code for LangGraph workflows with async execution, health checks, and optional monitoring.

## Instructions for Claude

### 1. Analyze Graph

Read the graph file to understand:
- State schema
- Entry points
- Expected inputs/outputs

### 2. Gather Requirements

Ask user:
- Port to run on (default: 8000)
- Whether to include Prometheus monitoring (default: yes)
- Whether to include streaming endpoint (default: yes)
- CORS configuration (if needed)

### 3. Generate Deployment Structure

Create:
```
deployment/
├── api.py              # FastAPI application
├── models.py           # Pydantic request/response models
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
├── .env.example
└── README.md
```

### 4. Generate models.py

```python
from pydantic import BaseModel, Field

class QueryRequest(BaseModel):
    input: str = Field(description="User input")
    config: dict = Field(default_factory=dict, description="Optional configuration")

class QueryResponse(BaseModel):
    output: str = Field(description="Generated output")
    metadata: dict = Field(default_factory=dict, description="Execution metadata")
```

### 5. Generate api.py

```python
from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse
from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST
import asyncio

from src.graph import create_graph
from .models import QueryRequest, QueryResponse

app = FastAPI(title="LangGraph API")
graph = create_graph()

# Metrics
REQUEST_COUNT = Counter('requests_total', 'Total requests')
REQUEST_LATENCY = Histogram('request_latency_seconds', 'Request latency')

@app.post("/process", response_model=QueryResponse)
@REQUEST_LATENCY.time()
async def process_query(request: QueryRequest):
    \"\"\"Process query through workflow.\"\"\"
    REQUEST_COUNT.inc()

    try:
        result = await graph.ainvoke({
            "messages": [{"role": "user", "content": request.input}]
        })

        return QueryResponse(
            output=result["messages"][-1]["content"],
            metadata={"steps": result.get("current_step")}
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/stream")
async def stream_process(request: QueryRequest):
    \"\"\"Stream workflow execution.\"\"\"
    async def event_generator():
        async for event in graph.astream({"messages": [request.input]}):
            yield f"data: {json.dumps(event)}\\n\\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

@app.get("/metrics")
async def metrics():
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)
```

### 6. Generate Dockerfile

```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["uvicorn", "deployment.api:app", "--host", "0.0.0.0", "--port", "8000"]
```

### 7. Generate docker-compose.yml

```yaml
version: '3.8'

services:
  api:
    build: .
    ports:
      - "8000:8000"
    env_file:
      - .env
    restart: unless-stopped
```

### 8. Generate requirements.txt

Include:
```
fastapi>=0.104.0
uvicorn[standard]>=0.24.0
prometheus-client>=0.19.0
python-dotenv
# Add graph-specific requirements
```

### 9. Generate README.md

Include:
- Deployment instructions
- Environment variables
- API endpoints documentation
- Docker usage
- Monitoring setup

### 10. Output Summary

Show:
- Files created
- How to run locally
- How to build Docker image
- API documentation URL

## Example Invocation

```
/langgraph-dev:create-deployment src/graph.py --include-monitoring
```

Refer to **deployment-patterns** skill for best practices.
