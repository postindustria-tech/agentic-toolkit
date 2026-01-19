# RemoteGraph Client Patterns

Comprehensive guide to interacting with deployed LangGraph applications using the RemoteGraph client.

## Overview

`RemoteGraph` is a client-side interface that provides API parity with `CompiledGraph`, allowing you to interact with deployed graphs using the same methods (`invoke()`, `stream()`, `get_state()`, etc.) in both development and production environments.

**Key Benefits**:
- **Separation of concerns**: Build/test locally with `CompiledGraph`, deploy to Platform, call with `RemoteGraph`
- **Thread-level persistence**: Maintain conversation state across calls with thread IDs
- **Subgraph embedding**: Compose modular multi-agent workflows
- **Reusable workflows**: Use deployed graphs as nodes or tools in other graphs

**IMPORTANT WARNING**: Do not use `RemoteGraph` to call itself or another graph on the same deployment - this causes deadlocks and resource exhaustion. Use local graph composition or subgraphs for same-deployment scenarios.

## Installation

```bash
pip install langgraph-sdk
```

Latest version: 0.3.1 (December 2025)

## Initialization Patterns

### Pattern 1: URL-Based Initialization

**When to use**: Simplest approach for basic interactions, auto-creates both sync and async clients

```python
from langgraph.pregel.remote import RemoteGraph

# Using graph name (uses default assistant)
url = "<DEPLOYMENT_URL>"
graph_name = "agent"  # From langgraph.json
remote_graph = RemoteGraph(graph_name, url=url)

# Using specific assistant ID
assistant_id = "<ASSISTANT_ID>"
remote_graph = RemoteGraph(assistant_id, url=url)
```

**How it works**:
- Both sync and async clients created automatically
- Uses provided URL, headers (if provided), default config (timeout, etc.)
- Suitable for most use cases

### Pattern 2: Client-Based Initialization

**When to use**: Need fine-grained control over client configuration (timeout, headers, connection pooling)

```python
from langgraph_sdk import get_client, get_sync_client
from langgraph.pregel.remote import RemoteGraph

url = "<DEPLOYMENT_URL>"
client = get_client(url=url, api_key="...")  # Async client
sync_client = get_sync_client(url=url, api_key="...")  # Sync client

# Using graph name
graph_name = "agent"
remote_graph = RemoteGraph(
    graph_name,
    client=client,
    sync_client=sync_client
)

# Using assistant ID
assistant_id = "<ASSISTANT_ID>"
remote_graph = RemoteGraph(
    assistant_id,
    client=client,
    sync_client=sync_client
)
```

**Client/sync_client take precedence** over `url` if both provided.

### Required Parameters

**Always required**:
- `name`: Graph name (from `langgraph.json`) **OR** assistant ID
- `api_key`: LangSmith API key (env var `LANGSMITH_API_KEY` or explicit argument)

**One of**:
- `url`: Deployment URL (creates clients automatically)
- `client`: `LangGraphClient` instance (async operations)
- `sync_client`: `SyncLangGraphClient` instance (sync operations)

**ValueError** raised if none of url/client/sync_client provided.

## Invocation Patterns

### Async Invocation

**Requires**: `url` or `client` provided during initialization

```python
# Single invocation
result = await remote_graph.ainvoke({
    "messages": [{"role": "user", "content": "what's the weather in sf"}]
})

# Streaming outputs
async for chunk in remote_graph.astream({
    "messages": [{"role": "user", "content": "what's the weather in la"}]
}):
    print(chunk)
```

### Sync Invocation

**Requires**: `url` or `sync_client` provided during initialization

```python
# Single invocation
result = remote_graph.invoke({
    "messages": [{"role": "user", "content": "what's the weather in sf"}]
})

# Streaming outputs
for chunk in remote_graph.stream({
    "messages": [{"role": "user", "content": "what's the weather in la"}]
}):
    print(chunk)
```

## Thread-Level Persistence

**Problem**: By default, graph runs are stateless - intermediate checkpoints and final state not persisted

**Solution**: Create a thread and pass its ID through config to maintain conversation history

```python
from langgraph_sdk import get_sync_client

url = "<DEPLOYMENT_URL>"
graph_name = "agent"
sync_client = get_sync_client(url=url)
remote_graph = RemoteGraph(graph_name, url=url)

# Create thread (or use existing thread ID)
thread = sync_client.threads.create()

# Invoke with thread config for persistence
config = {"configurable": {"thread_id": thread["thread_id"]}}
result = remote_graph.invoke({
    "messages": [{"role": "user", "content": "what's the weather in sf"}]
}, config=config)

# Verify state was persisted
thread_state = remote_graph.get_state(config)
print(thread_state)

# Continue conversation in same thread
result2 = remote_graph.invoke({
    "messages": [{"role": "user", "content": "what about tomorrow?"}]
}, config=config)  # Context retained from previous turn
```

**Use cases**:
- Multi-turn conversations
- Human-in-the-loop workflows
- Interrupt and resume patterns
- State debugging and inspection

## State Management

### Get State

```python
config = {"configurable": {"thread_id": "<THREAD_ID>"}}
state = remote_graph.get_state(config)
```

### Update State

```python
# Update specific state fields
remote_graph.update_state(
    config,
    values={"messages": [{"role": "assistant", "content": "Updated!"}]}
)

# With metadata
remote_graph.update_state(
    config,
    values={"step": "completed"},
    as_node="human_review"  # Attribute update to specific node
)
```

## Subgraph Patterns

### Pattern: Remote Subgraph in Local Graph

**When to use**: Modular architecture where different responsibilities split across separate deployed graphs

**IMPORTANT**: If parent graph uses `checkpointer`, use UUIDs as thread IDs for remote subgraph

```python
from langgraph_sdk import get_sync_client
from langgraph.graph import StateGraph, MessagesState, START

url = "<DEPLOYMENT_URL>"
graph_name = "specialist_agent"
remote_graph = RemoteGraph(graph_name, url=url)

# Define parent graph
builder = StateGraph(MessagesState)

# Add remote graph directly as a node
builder.add_node("specialist", remote_graph)
builder.add_edge(START, "specialist")
graph = builder.compile()

# Invoke parent graph (calls remote subgraph)
result = graph.invoke({
    "messages": [{"role": "user", "content": "what's the weather in sf"}]
})

# Stream with subgraph visibility
for chunk in graph.stream(
    {"messages": [{"role": "user", "content": "analyze this data"}]},
    subgraphs=True  # See outputs from both parent and remote subgraph
):
    print(chunk)
```

**State flow**: Parent state passed to remote subgraph, remote subgraph returns updated state

### Multi-Remote-Subgraph Architecture

```python
# Multiple remote graphs as specialized agents
specialist_1 = RemoteGraph("data_analyst", url=url_1)
specialist_2 = RemoteGraph("report_generator", url=url_2)
specialist_3 = RemoteGraph("fact_checker", url=url_3)

builder = StateGraph(MessagesState)
builder.add_node("analyze", specialist_1)
builder.add_node("generate", specialist_2)
builder.add_node("verify", specialist_3)

# Sequential pipeline
builder.add_edge(START, "analyze")
builder.add_edge("analyze", "generate")
builder.add_edge("generate", "verify")

graph = builder.compile()
```

## SDK Client Methods

### SyncLangGraphClient

```python
from langgraph_sdk import get_sync_client

client = get_sync_client(url="http://localhost:2024", api_key="...")

# Assistants management
assistants = client.assistants.search()
assistant = client.assistants.get("asst_123")

# Thread management
thread = client.threads.create()
threads = client.threads.list()
thread_info = client.threads.get("<THREAD_ID>")

# Run management
run = client.runs.create(thread_id="...", assistant_id="...")
runs = client.runs.list(thread_id="...")

# Cron jobs (scheduled execution)
cron = client.cron.create(schedule="0 9 * * *", input={...})
cron_jobs = client.cron.list()

# Storage (cross-thread persistence)
client.store.put(namespace=("user", "123"), key="pref", value={...})
items = client.store.search(namespace=("user", "123"))
```

### LangGraphClient (Async)

```python
from langgraph_sdk import get_client

client = get_client(url="http://localhost:2024", api_key="...")

# All methods are async
assistants = await client.assistants.search()
thread = await client.threads.create()
# ... etc (same methods as sync, but await required)
```

## Authentication Patterns

### API Key from Environment

```python
import os

os.environ["LANGSMITH_API_KEY"] = "your-api-key"

# Auto-detected
remote_graph = RemoteGraph("agent", url=deployment_url)
```

### API Key Explicit

```python
# Method 1: In RemoteGraph
remote_graph = RemoteGraph("agent", url=url, api_key="...")

# Method 2: In client
client = get_client(url=url, api_key="...")
remote_graph = RemoteGraph("agent", client=client)
```

### Custom Headers

```python
remote_graph = RemoteGraph(
    "agent",
    url=url,
    headers={"Authorization": "Bearer ...", "X-Custom": "value"}
)
```

## Error Handling

### Network Errors

```python
from httpx import HTTPError

try:
    result = remote_graph.invoke(input_data)
except HTTPError as e:
    print(f"Network error: {e}")
    # Retry logic or fallback
```

### State Errors

```python
try:
    state = remote_graph.get_state(config)
except ValueError as e:
    print(f"Invalid thread ID or config: {e}")
```

### Timeout Configuration

```python
from langgraph_sdk import get_client

client = get_client(
    url=url,
    timeout=60.0  # 60 seconds (default: 30)
)
remote_graph = RemoteGraph("agent", client=client)
```

## Best Practices

### 1. Use Thread IDs for Stateful Conversations

```python
# ❌ Bad - stateless, context lost between calls
result1 = remote_graph.invoke({"messages": [...]})
result2 = remote_graph.invoke({"messages": [...]})  # No context from result1

# ✅ Good - stateful, context maintained
config = {"configurable": {"thread_id": "user-session-123"}}
result1 = remote_graph.invoke({"messages": [...]}, config=config)
result2 = remote_graph.invoke({"messages": [...]}, config=config)  # Has context
```

### 2. Reuse Clients

```python
# ❌ Bad - creates new client per request
for _ in range(100):
    remote_graph = RemoteGraph("agent", url=url)
    result = remote_graph.invoke(input_data)

# ✅ Good - reuse client across requests
remote_graph = RemoteGraph("agent", url=url)
for _ in range(100):
    result = remote_graph.invoke(input_data)
```

### 3. Async for High Throughput

```python
import asyncio

# ✅ Good - parallel processing with async
async def process_batch(inputs):
    tasks = [remote_graph.ainvoke(inp) for inp in inputs]
    results = await asyncio.gather(*tasks)
    return results
```

### 4. Context Manager for Cleanup

```python
# ✅ Good - auto-cleanup
from langgraph_sdk import get_sync_client

with get_sync_client(url=url) as client:
    remote_graph = RemoteGraph("agent", sync_client=client)
    result = remote_graph.invoke(input_data)
# Client closed automatically
```

### 5. Avoid Self-Calling

```python
# ❌ Bad - DEADLOCK RISK
# Inside a graph deployed at deployment_url:
remote_graph = RemoteGraph("self", url=deployment_url)
builder.add_node("recursive", remote_graph)  # WILL DEADLOCK

# ✅ Good - use local subgraphs
local_subgraph = subgraph_builder.compile()
builder.add_node("modular", local_subgraph)
```

## Production Checklist

- [ ] **API Key**: Stored in environment variables, never hardcoded
- [ ] **Thread IDs**: Use UUIDs for production conversations
- [ ] **Error Handling**: Catch network errors, implement retries
- [ ] **Timeouts**: Configure appropriate timeouts for long-running graphs
- [ ] **Client Reuse**: Don't create new clients per request
- [ ] **Monitoring**: Track invocation latency, error rates
- [ ] **Self-Calling**: Verify no graphs call themselves via RemoteGraph
- [ ] **Async**: Use async methods for high-throughput applications

## Common Patterns

### Pattern: Client Application Calling Deployed Graph

```python
# FastAPI endpoint calling deployed agent
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

app = FastAPI()
remote_graph = RemoteGraph("customer_support", url=deployment_url)

class Query(BaseModel):
    user_id: str
    message: str

@app.post("/chat")
async def chat(query: Query):
    config = {"configurable": {"thread_id": query.user_id}}
    try:
        result = await remote_graph.ainvoke(
            {"messages": [{"role": "user", "content": query.message}]},
            config=config
        )
        return {"response": result["messages"][-1]["content"]}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
```

### Pattern: Multi-Agent Orchestration

```python
# Orchestrator calling specialized deployed agents
orchestrator = StateGraph(MessagesState)

# Remote specialists
researcher = RemoteGraph("research_agent", url=url)
analyst = RemoteGraph("analysis_agent", url=url)
writer = RemoteGraph("writing_agent", url=url)

orchestrator.add_node("research", researcher)
orchestrator.add_node("analyze", analyst)
orchestrator.add_node("write", writer)

orchestrator.add_edge(START, "research")
orchestrator.add_edge("research", "analyze")
orchestrator.add_edge("analyze", "write")

graph = orchestrator.compile()
```

### Pattern: Fallback Chain

```python
# Primary agent with fallback to simpler agent
primary = RemoteGraph("advanced_agent", url=url_primary)
fallback = RemoteGraph("basic_agent", url=url_fallback)

async def process_with_fallback(input_data):
    try:
        result = await primary.ainvoke(input_data)
        if is_successful(result):
            return result
    except Exception as e:
        print(f"Primary failed: {e}, using fallback")

    return await fallback.ainvoke(input_data)
```

## References

- [RemoteGraph How-To Guide](https://docs.langchain.com/langgraph-platform/use-remote-graph)
- [LangGraph SDK Documentation](https://docs.langchain.com/langsmith/sdk)
- [Python SDK Reference](https://langchain-ai.github.io/langgraph/cloud/reference/sdk/python_sdk_ref/)
- [LangGraph Platform API](https://langchain-ai.github.io/langgraph/cloud/reference/api/api_ref.html)

---

**Created**: 2026-01-14
**LangGraph SDK Version**: 0.3.1+
**Status**: Active
