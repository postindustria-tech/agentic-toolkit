---
name: deployment-patterns-for-langgraph
description: This skill should be used when the user asks about "deploy LangGraph", "LangGraph Platform", "RemoteGraph client", "LangGraph Studio", "assistants", "cron jobs", "webhooks", "background runs", "task queues", "self-hosted deployment", "FastAPI", "production deployment", "checkpointing", "Docker deployment", or needs guidance on deploying and managing LangGraph applications.
version: 1.0.0
---

# Deployment Patterns for LangGraph

Deploy LangGraph workflows as production APIs with managed platforms, FastAPI, async execution, persistence, and observability.

## LangGraph Platform (Recommended)

LangGraph Platform offers managed deployment for production applications with built-in persistence, scaling, and monitoring.

### Deployment Options

| Option | Description | Plan |
|--------|-------------|------|
| **Cloud (SaaS)** | Fully managed by LangChain, deploy from GitHub | Plus, Enterprise |
| **Hybrid (BYOC)** | LangChain control plane + your data plane | Enterprise |
| **Self-Hosted Lite** | Free tier, up to 1M nodes/month | Developer |
| **Self-Hosted Enterprise** | Full platform in your infrastructure | Enterprise |

### Quick Start

```bash
pip install "langgraph-cli[inmem]"  # Requires Python 3.11+
langgraph new my-agent --template new-langgraph-project-python
cd my-agent
langgraph dev  # Runs on http://localhost:2024
```

See [LangGraph Platform Deployment Options](https://docs.langchain.com/langgraph-platform/deployment-options).

## RemoteGraph Client

`RemoteGraph` provides API parity with `CompiledGraph`, allowing interaction with deployed graphs using the same methods (`invoke()`, `stream()`, `get_state()`) in both development and production.

**Key Benefits**:
- Separation of concerns: Build/test locally, deploy to Platform, call with RemoteGraph
- Thread-level persistence for stateful conversations
- Subgraph embedding for modular multi-agent workflows

**Basic Usage**:

```python
from langgraph.pregel.remote import RemoteGraph

# Connect to deployed graph
remote_graph = RemoteGraph("agent", url="<DEPLOYMENT_URL>")

# Stateful conversation with thread persistence
config = {"configurable": {"thread_id": "user-123"}}
result = await remote_graph.ainvoke(
    {"messages": [{"role": "user", "content": "Hello"}]},
    config=config
)

# Use as subgraph in local composition
from langgraph.graph import StateGraph, START

builder = StateGraph(MessagesState)
builder.add_node("remote_specialist", remote_graph)
builder.add_edge(START, "remote_specialist")
graph = builder.compile()
```

**Reference**: See **`references/remotegraph-client.md`** for initialization patterns, thread persistence, state management, subgraph composition, SDK methods, authentication, error handling, and best practices.

## LangGraph Studio

LangGraph Studio is a specialized agent IDE for visualization, interaction, and debugging of deployed and local LangGraph applications.

**Access Patterns**:
- **Platform Deployments**: Open from LangSmith UI → LangGraph Platform Deployments → Studio button
- **Local Development**: `langgraph dev` → Auto-opens Studio on http://localhost:2024
- **Debugger Integration**: `langgraph dev --debug-port 5678` → Attach VS Code debugger

**Key Features**:
- **Time Travel Debugging**: Replay and fork executions from checkpoints
- **State Inspection**: View full state at every checkpoint with granularity control
- **Thread Management**: Create, view, edit, and fork conversation threads
- **Dataset Experimentation**: Run batch evaluations over test datasets
- **Two Modes**: Graph mode (detailed debugging) and Chat mode (behavior testing)

**Quick Start**:

```bash
# Start local dev server
pip install -U "langgraph-cli[inmem]"
langgraph dev

# With debugger support
pip install debugpy
langgraph dev --debug-port 5678
```

**Reference**: See **`references/studio-debugging.md`** for studio modes, access patterns, time travel debugging, state inspection, breakpoints, trace cloning, and production debugging workflows.

## Assistants and Versioning

Assistants are instances of a graph with specific configurations, allowing multiple specialized versions of the same graph architecture optimized for different use cases through configuration variations rather than structural changes.

**Concept**: Same graph logic, different configurations (prompts, models, tools, parameters)

**Example**: One writing graph, three assistants:
- Blog Assistant: GPT-4, formal tone, long-form prompts
- Tweet Assistant: GPT-3.5, casual tone, concise prompts
- Email Assistant: Claude, professional tone, structured prompts

**Usage**:

```python
from langgraph_sdk import get_client

client = get_client(url="<DEPLOYMENT_URL>")

# Create assistant with specific configuration
assistant = await client.assistants.create(
    "agent",
    context={
        "model_name": "openai",
        "system_prompt": "You are a helpful assistant",
        "temperature": 0.7
    },
    name="OpenAI Assistant"
)

# Use in runs
await client.runs.create(
    thread["thread_id"],
    assistant["assistant_id"],
    input={"messages": [...]}
)

# Update creates new version (versioning automatic)
updated = await client.assistants.update(
    assistant["assistant_id"],
    context={...}  # Must pass ENTIRE context
)

# Rollback to previous version
await client.assistants.set_latest(assistant["assistant_id"], version=1)
```

**Reference**: See **`references/assistants-versioning.md`** for context schema foundation, creating assistants, versioning, rollback strategies, common patterns (multi-model, A/B testing, gradual rollout), and migration strategies.

## Cron Jobs and Webhooks

LangGraph Platform supports scheduled execution (cron jobs) and event-driven invocation (webhooks) for automated workflows.

### Cron Jobs

**Use Cases**: Daily email summaries, weekly reports, nightly data sync, periodic health checks

**Patterns**:
- **Thread-Based (Stateful)**: Same thread for every execution, context accumulates
- **Stateless**: New thread per execution, independent runs

```python
from langgraph_sdk import get_client

client = get_client(url="<DEPLOYMENT_URL>")

# Stateless cron with auto-cleanup
cron_job = await client.crons.create(
    "agent",
    schedule="0 9 * * *",  # Every day at 9:00 AM
    input={"messages": [{"role": "user", "content": "Generate daily report"}]},
    on_run_completed="delete"  # Auto-delete thread after run
)

# Thread-based cron (stateful)
thread = await client.threads.create()
cron_job = await client.crons.create_for_thread(
    thread["thread_id"],
    "agent",
    schedule="27 15 * * *",  # Every day at 3:27 PM
    input={"messages": [{"role": "user", "content": "Daily status update"}]}
)
```

**CRITICAL**: Always delete cron jobs when no longer needed to avoid unwanted LLM API charges!

### Webhooks

**Use Cases**: Notify external systems of completion, trigger downstream workflows, log results

**Usage**:

```python
# Webhook called on run completion
async for chunk in client.runs.stream(
    thread_id=thread["thread_id"],
    assistant_id="agent",
    input=input_data,
    webhook="https://my-server.app/webhook-endpoint"
):
    pass

# With cron jobs
cron_job = await client.crons.create(
    "agent",
    schedule="0 9 * * *",
    input={...},
    webhook="https://my-server.app/daily-report-complete"
)
```

**Security**: Use query parameter tokens, static headers (langgraph.json), or HMAC signatures

**Reference**: See **`references/cron-webhooks.md`** for cron expression syntax, thread cleanup strategies, webhook payload format, security patterns, URL restrictions, and production checklists.

## Task Queues and Background Processing

LangGraph Platform provides robust infrastructure for background task processing with horizontal scaling and resilience.

**Key Features**:
- Background runs (async execution without blocking HTTP requests)
- Multitask strategies (enqueue, reject, interrupt)
- Horizontal scaling (stateless instances scale linearly)
- Exactly-once execution semantics
- Automatic failover and crash resilience

**Background Runs**:

```python
# Start background run (non-blocking)
run = await client.runs.create(
    thread["thread_id"],
    "agent",
    input={"messages": [{"role": "user", "content": "Process this long task"}]}
)

# Returns immediately with status="pending"
print(run["status"])  # "pending"

# Wait for completion (blocking)
await client.runs.join(thread["thread_id"], run["run_id"])

# Get final result
final_result = await client.threads.get_state(thread["thread_id"])
```

**Multitask Strategies** (for concurrent runs on same thread):

```python
# Enqueue (default): Queue runs, execute in order
run2 = await client.runs.create(
    thread["thread_id"],
    "agent",
    input={...},
    multitask_strategy="enqueue"
)

# Reject: Fail if run already active
run2 = await client.runs.create(
    thread["thread_id"],
    "agent",
    input={...},
    multitask_strategy="reject"  # Returns HTTP 409 if run active
)

# Interrupt: Cancel running run, start new one
run2 = await client.runs.create(
    thread["thread_id"],
    "agent",
    input={...},
    multitask_strategy="interrupt"  # Cancels existing run
)
```

**Horizontal Scaling**:

```json
{
  "queue": {
    "enabled": true,
    "max_concurrent_runs": 10
  }
}
```

**Throughput Formula**: `Total Throughput = Instances × max_concurrent_runs`

Example: 5 instances × 10 runs = 50 concurrent background runs

**Reference**: See **`references/task-queues.md`** for background runs, polling strategies, multitask strategies, horizontal scaling, resilience (exactly-once semantics, graceful shutdown, crash recovery), and best practices.

## Self-Hosted Deployment

Deploy LangGraph Platform entirely within your own cloud environment with two deployment models:

### Deployment Models

**1. Standalone Server** (Data Plane Only):
- LangGraph Servers, PostgreSQL, Redis
- No control plane UI
- Maximum flexibility
- Kubernetes (production) or Docker/Docker Compose (development)

**2. Full Platform** (Control Plane + Data Plane):
- Control plane UI/APIs for deployment management
- Data plane infrastructure
- Requires Kubernetes + KEDA
- Requires self-hosted LangSmith instance

**Quick Start** (Docker Compose for Development):

```yaml
# docker-compose.yml
services:
  langgraph-redis:
    image: redis:6

  langgraph-postgres:
    image: postgres:16
    environment:
      POSTGRES_DB: postgres
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: postgres
    volumes:
      - langgraph-data:/var/lib/postgresql/data

  langgraph-api:
    image: ${IMAGE_NAME}
    ports:
      - "8123:8000"
    environment:
      REDIS_URI: redis://langgraph-redis:6379
      DATABASE_URI: postgres://postgres:postgres@langgraph-postgres:5432/postgres?sslmode=disable
      LANGSMITH_API_KEY: ${LANGSMITH_API_KEY}
      LANGGRAPH_CLOUD_LICENSE_KEY: ${LANGGRAPH_CLOUD_LICENSE_KEY}
```

```bash
langgraph build -t my-app:latest
docker compose up
curl http://localhost:8123/ok  # {"ok": true}
```

**Production** (Kubernetes + Helm):

```bash
helm repo add langchain https://langchain-ai.github.io/helm
helm install my-langgraph langchain/langgraph-cloud \
    --set image.repository=my-registry/my-app \
    --set env.REDIS_URI="redis://my-redis:6379" \
    --set env.DATABASE_URI="postgres://user:pass@my-postgres:5432/langgraph" \
    --set env.LANGSMITH_API_KEY="..." \
    --set env.LANGGRAPH_CLOUD_LICENSE_KEY="..."
```

**Reference**: See **`references/self-hosted-deployment.md`** for deployment models comparison, Docker Compose setup, Kubernetes + Helm configuration, PostgreSQL/Redis configuration, environment variables, horizontal scaling, monitoring, security, and production checklists.

## Production Persistence

For production, use PostgreSQL or Redis checkpointers instead of in-memory storage.

### PostgreSQL (Recommended)

```python
# pip install langgraph-checkpoint-postgres
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver

DB_URI = "postgresql://user:pass@localhost:5432/db"

async with AsyncPostgresSaver.from_conn_string(DB_URI) as checkpointer:
    await checkpointer.setup()  # Create tables (first time only)
    graph = workflow.compile(checkpointer=checkpointer)

    # Use thread_id for conversation continuity
    config = {"configurable": {"thread_id": "user-123"}}
    result = await graph.ainvoke(state, config)
```

### Redis (High Performance)

```python
# pip install langgraph-checkpoint-redis
from langgraph.checkpoint.redis.aio import AsyncRedisSaver

async with AsyncRedisSaver.from_conn_string("redis://localhost:6379") as checkpointer:
    await checkpointer.asetup()  # Create indices (first time only)
    graph = workflow.compile(checkpointer=checkpointer)
```

**Warning**: Never use `InMemorySaver` in production - state is lost on restart.

## FastAPI Integration

```python
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from src.graph import create_graph

app = FastAPI()
graph = create_graph()

class Query(BaseModel):
    input: str

class Response(BaseModel):
    output: str
    metadata: dict

@app.post("/process", response_model=Response)
async def process_query(query: Query):
    """Process query through LangGraph workflow."""
    try:
        result = await graph.ainvoke({
            "messages": [{"role": "user", "content": query.input}],
            "current_step": ""
        })

        return Response(
            output=result["messages"][-1]["content"],
            metadata={"steps": result["current_step"]}
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
```

## Async Execution

```python
# Use ainvoke for async
result = await graph.ainvoke(state)

# Use astream for async streaming with explicit stream mode
# Available modes: "values" (full state), "updates" (deltas),
#                  "messages" (LLM tokens), "custom", "debug"
async for event in graph.astream(state, stream_mode="updates"):
    yield event

# For LLM token streaming (returns AIMessageChunk, metadata tuples):
async for msg, metadata in graph.astream(state, stream_mode="messages"):
    # msg: AIMessageChunk with .content, .tool_calls, etc.
    # metadata: dict with langgraph_node, tags, langgraph_step
    print(msg.content, metadata.get("langgraph_node"))

# Multiple modes (returns tuples with mode identifier):
async for mode, chunk in graph.astream(state, stream_mode=["updates", "messages"]):
    print(f"Mode: {mode}, Data: {chunk}")

# Custom streaming from nodes (Python 3.11+)
from langgraph.config import get_stream_writer

def my_node(state):
    writer = get_stream_writer()
    writer({"progress": "Processing..."})
    return state

async for event in graph.astream(state, stream_mode="custom"):
    print(event)
```

## Streaming API

```python
import json
import asyncio
from fastapi import Request
from fastapi.responses import StreamingResponse

@app.post("/stream")
async def stream_process(query: Query, request: Request):
    """Stream workflow events in real-time using Server-Sent Events."""
    async def event_generator():
        try:
            async for event in graph.astream(
                {
                    "messages": [{"role": "user", "content": query.input}],
                    "current_step": ""
                },
                stream_mode="updates"
            ):
                # Check if client disconnected
                if await request.is_disconnected():
                    break
                yield f"data: {json.dumps(event)}\n\n"
        except asyncio.CancelledError:
            # Client disconnected - cleanup
            raise
        except Exception as e:
            # Send error to client before closing
            yield f"data: {json.dumps({'error': str(e)})}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={"X-Accel-Buffering": "no"}  # Disable nginx buffering
    )
```

## Health Checks

```python
@app.get("/health")
async def health_check():
    """Verify service is running."""
    return {"status": "healthy"}

@app.get("/ready")
async def readiness_check():
    """Verify service is ready to handle requests."""
    try:
        # Verify graph structure exists and has nodes
        graph_repr = graph.get_graph()
        node_count = len(graph_repr.nodes) if graph_repr.nodes else 0
        if node_count == 0:
            raise HTTPException(status_code=503, detail="Graph has no nodes")
        return {"status": "ready", "nodes": node_count}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=503, detail=str(e))
```

## LangSmith Observability

LangSmith provides automatic tracing for LangGraph with zero code changes.

```python
import os

os.environ["LANGCHAIN_TRACING_V2"] = "true"
os.environ["LANGCHAIN_API_KEY"] = "your-api-key"  # From LangSmith
os.environ["LANGCHAIN_PROJECT"] = "production-app"

# Tracing is automatic - no code changes needed
result = await graph.ainvoke(state)
```

**Features**: Token tracking, latency analysis, trace visualization, agent debugging.

Use Prometheus for infrastructure metrics; LangSmith for agent/LLM tracing.

## Monitoring with Prometheus

Use `prometheus-async` for correct async timing measurement. The standard `prometheus_client`
`@Histogram.time()` decorator does not work correctly with async functions.

```python
# pip install prometheus-async prometheus-client
from prometheus_client import Counter, Histogram, Gauge, generate_latest, CONTENT_TYPE_LATEST
from prometheus_async.aio import time, track_inprogress
from fastapi.responses import Response

# Define metrics with labels for better observability
REQUEST_COUNT = Counter(
    'langgraph_requests_total',
    'Total requests processed',
    ['endpoint']
)
REQUEST_LATENCY = Histogram(
    'langgraph_request_latency_seconds',
    'Request latency in seconds',
    ['endpoint']
)
REQUESTS_IN_PROGRESS = Gauge(
    'langgraph_requests_in_progress',
    'Number of requests currently being processed',
    ['endpoint']
)

@app.post("/process")
@time(REQUEST_LATENCY.labels(endpoint="/process"))  # Async-safe timing
@track_inprogress(REQUESTS_IN_PROGRESS.labels(endpoint="/process"))
async def process_query(query: Query):
    REQUEST_COUNT.labels(endpoint="/process").inc()
    result = await graph.ainvoke({"messages": [{"role": "user", "content": query.input}]})
    return {"output": result["messages"][-1]["content"]}

@app.get("/metrics")
async def metrics():
    return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)
```

## LangGraph CLI

### Installation

```bash
pip install "langgraph-cli[inmem]"  # Requires Python 3.11+
```

### Commands

| Command | Description |
|---------|-------------|
| `langgraph new` | Create project from template |
| `langgraph dev` | Run local server (port 2024) |
| `langgraph up` | Launch in Docker (port 8123) |
| `langgraph build` | Build Docker image |

### Configuration (langgraph.json)

```json
{
  "dependencies": [".", "langchain-anthropic"],
  "graphs": {
    "agent": "./src/graph.py:graph"
  },
  "env": ".env",
  "python_version": "3.11"
}
```

## Environment Configuration

```python
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    anthropic_api_key: str
    langchain_api_key: str = ""
    log_level: str = "INFO"
    max_retries: int = 3

settings = Settings()
```

## Security

### API Key Authentication

```python
from fastapi import Depends, HTTPException, Security
from fastapi.security import APIKeyHeader

api_key_header = APIKeyHeader(name="X-API-Key")

async def verify_api_key(api_key: str = Security(api_key_header)):
    if api_key != settings.api_key:
        raise HTTPException(status_code=401, detail="Invalid API key")
    return api_key

@app.post("/process")
async def process_query(query: Query, api_key: str = Depends(verify_api_key)):
    result = await graph.ainvoke({"messages": [{"role": "user", "content": query.input}]})
    return {"output": result["messages"][-1]["content"]}
```

### Rate Limiting

```python
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

@app.post("/process")
@limiter.limit("10/minute")
async def process_query(request: Request, query: Query):
    result = await graph.ainvoke({"messages": [{"role": "user", "content": query.input}]})
    return {"output": result["messages"][-1]["content"]}
```

## Deployment Checklist

### Infrastructure
- [ ] **Persistence** - PostgreSQL or Redis checkpointer (not MemorySaver)
- [ ] **Thread IDs** - Unique identifiers for conversation continuity

### Application
- [ ] **Async** - Use `ainvoke()`, `astream()`
- [ ] **Error handling** - Return appropriate HTTP errors
- [ ] **Input validation** - Sanitize user inputs
- [ ] **Health endpoints** - `/health`, `/ready`

### Observability
- [ ] **LangSmith** - Environment variables configured
- [ ] **Prometheus** - Infrastructure metrics (optional)
- [ ] **Logging** - Structured JSON logs

### Security
- [ ] **Authentication** - API key or JWT validation
- [ ] **Rate limiting** - Per-user request quotas
- [ ] **HTTPS** - TLS in production
- [ ] **Secrets** - Environment variables only

## Docker Deployment

### Using UV (Recommended)

```dockerfile
# Build stage with UV
FROM python:3.12-slim AS builder
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

WORKDIR /app
ENV UV_COMPILE_BYTECODE=1 UV_LINK_MODE=copy

# Install dependencies (cached layer)
RUN --mount=type=cache,target=/root/.cache/uv \
    --mount=type=bind,source=uv.lock,target=uv.lock \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    uv sync --locked --no-install-project --no-dev

# Copy application and install project
COPY . /app
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --locked --no-dev

# Production stage
FROM python:3.12-slim
COPY --from=builder /app /app
ENV PATH="/app/.venv/bin:$PATH"

EXPOSE 8000
CMD ["uvicorn", "src.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Using pip (Alternative)

```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Adjust module path based on your project structure:
# - main:app           (if app in main.py at root)
# - src.api.main:app   (if app in src/api/main.py)
# - app.main:app       (if app in app/main.py)
CMD ["uvicorn", "src.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

## Reference Files

For detailed documentation on LangGraph Platform features, consult:

- **`references/remotegraph-client.md`** - RemoteGraph client patterns, thread persistence, subgraph composition
- **`references/studio-debugging.md`** - Studio workflows, time travel debugging, state inspection
- **`references/assistants-versioning.md`** - Assistant management, versioning, rollback strategies
- **`references/cron-webhooks.md`** - Scheduled execution, webhooks, security patterns
- **`references/task-queues.md`** - Background processing, multitask strategies, horizontal scaling
- **`references/self-hosted-deployment.md`** - Self-hosted deployment models, Kubernetes, configuration

## Documentation

- [LangGraph Platform](https://docs.langchain.com/langgraph-platform/deployment-options)
- [LangGraph CLI](https://pypi.org/project/langgraph-cli/)
- [LangSmith Observability](https://docs.langchain.com/langsmith/observability-quickstart)
- [LangGraph Streaming](https://docs.langchain.com/oss/python/langgraph/streaming)
- [langgraph-checkpoint-postgres](https://pypi.org/project/langgraph-checkpoint-postgres/)
- [langgraph-checkpoint-redis](https://pypi.org/project/langgraph-checkpoint-redis/)
