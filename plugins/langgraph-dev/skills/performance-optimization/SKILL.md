---
name: performance-optimization-for-langgraph
description: This skill should be used when the user asks about "optimize performance", "caching", "cost tracking", "async execution", "reduce latency", "token optimization", or needs guidance on improving LangGraph application performance.
version: 0.3.1
---

# Performance Optimization for LangGraph

Optimize LangGraph workflows through node-level caching, async patterns, and cost monitoring.

> **Note**: Examples in this skill assume a compiled graph instance `graph`. See the Node-Level Caching section for a complete example of graph creation.

## Node-Level Caching with CachePolicy

LangGraph provides node-level caching to avoid redundant computation. Use `CachePolicy` to configure caching per node.

```python
from langgraph.cache.memory import InMemoryCache
from langgraph.types import CachePolicy
from langgraph.graph import StateGraph
from langchain_anthropic import ChatAnthropic

# Initialize LLM instance (reuse for connection pooling)
llm = ChatAnthropic(model="claude-sonnet-4-5-20250929", max_tokens=1024)

def expensive_llm_node(state: dict) -> dict:
    """Node that makes expensive LLM calls."""
    response = llm.invoke(state["query"])
    return {"response": response}

# Create graph builder
builder = StateGraph(dict)

# Add node with cache policy (TTL in seconds)
builder.add_node(
    "llm_node",
    expensive_llm_node,
    cache_policy=CachePolicy(ttl=3600)  # Cache for 1 hour
)

# Compile graph with cache
graph = builder.compile(cache=InMemoryCache())

# Repeated invocations with same input return cached results
result1 = graph.invoke({"query": "What is Python?"})  # Calls LLM
result2 = graph.invoke({"query": "What is Python?"})  # Returns cached
```

**Custom Cache Keys**:
```python
import hashlib
import json

def custom_key_func(input_data: dict) -> str:
    """Generate cache key from specific fields."""
    key_data = {"query": input_data.get("query")}
    serialized = json.dumps(key_data, sort_keys=True)
    return hashlib.md5(serialized.encode(), usedforsecurity=False).hexdigest()

builder.add_node(
    "llm_node",
    expensive_llm_node,
    cache_policy=CachePolicy(ttl=3600, key_func=custom_key_func)
)
```

## Async for Throughput

```python
import asyncio

# Sequential (slow)
def process_queries_sync(queries):
    results = []
    for query in queries:
        result = graph.invoke({"messages": [query]})
        results.append(result)
    return results

# Parallel (fast) with error handling
async def process_queries_async(queries: list[str]) -> list[dict]:
    """Process queries in parallel with error handling."""
    tasks = [graph.ainvoke({"messages": [q]}) for q in queries]
    results = await asyncio.gather(*tasks, return_exceptions=True)
    # Filter out exceptions or handle them as needed
    return [r for r in results if not isinstance(r, Exception)]
```

## Token Tracking (Anthropic Claude)

Track token usage directly from the Anthropic API response:

```python
import anthropic

client = anthropic.Anthropic()

query = "What is Python?"

response = client.messages.create(
    model="claude-sonnet-4-5-20250929",
    max_tokens=1024,
    messages=[{"role": "user", "content": query}]
)

# Access token usage from response
print(f"Input tokens: {response.usage.input_tokens}")
print(f"Output tokens: {response.usage.output_tokens}")
total = response.usage.input_tokens + response.usage.output_tokens
print(f"Total tokens: {total}")
```

**With LangChain ChatAnthropic**:
```python
from langchain_anthropic import ChatAnthropic

llm = ChatAnthropic(model="claude-sonnet-4-5-20250929", max_tokens=1024)
response = llm.invoke("What is Python?")

# Access via response metadata
print(f"Token usage: {response.usage_metadata}")
```

## Batch Processing

```python
import asyncio
from typing import Any, AsyncGenerator

async def process_item(item):
    """Process a single item - replace with your actual processing logic."""
    # Example: call graph with the item
    return await graph.ainvoke({"input": item})

async def batch_process(items: list[Any], batch_size: int = 10) -> AsyncGenerator[list[dict], None]:
    """Process items in batches to limit concurrency."""
    for i in range(0, len(items), batch_size):
        batch = items[i:i+batch_size]
        results = await asyncio.gather(*[
            process_item(item) for item in batch
        ])
        yield results
```

## Reduce Context Size

**Use LangGraph State with Summarization**:
```python
from typing import Any
from langgraph.graph import MessagesState
from langchain_anthropic import ChatAnthropic

# Initialize LLM for summarization
llm = ChatAnthropic(model="claude-sonnet-4-5-20250929")

class AgentState(MessagesState):
    """State with message history and summary.

    Inherits 'messages' field from MessagesState with add_messages reducer.
    Do NOT redefine 'messages' - it would override the add_messages reducer.
    """
    summary: str = ""

def summarize_if_needed(state: AgentState) -> dict[str, Any]:
    """Summarize messages when context gets too long."""
    if len(state["messages"]) > 10:
        # Summarize older messages to reduce context
        summary_prompt = f"Summarize this conversation:\n{state['messages'][:8]}"
        summary = llm.invoke(summary_prompt)
        return {
            "summary": summary.content,
            "messages": state["messages"][8:]  # Keep recent messages
        }
    return {}
```

**Selective Retrieval**:
```python
# Assumes vectorstore is initialized, e.g.:
# from langchain_chroma import Chroma
# vectorstore = Chroma.from_documents(documents, embeddings)

# Retrieve fewer documents with relevance threshold
# Default k=4, override with k=2 for fewer results
retriever = vectorstore.as_retriever(
    search_type="similarity_score_threshold",
    search_kwargs={"k": 2, "score_threshold": 0.7}
)
```

## Streaming for Responsiveness

```python
import json
from fastapi import FastAPI
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

app = FastAPI()

class Query(BaseModel):
    input: str

@app.post("/stream")
async def stream_response(query: Query):
    """Stream partial results as they're available."""
    async def generate():
        async for event in graph.astream({"messages": [query.input]}):
            yield json.dumps(event) + "\n"

    return StreamingResponse(generate(), media_type="application/x-ndjson")
```

## Connection Pooling

```python
from langchain_anthropic import ChatAnthropic

# Reuse LLM instances (connection pooling handled internally)
llm = ChatAnthropic(
    model="claude-sonnet-4-5-20250929",
    max_tokens=4096,
    max_retries=3,
    timeout=30.0
)

# Don't create new instances per request - reuse this instance
```

## Monitoring Performance

For async functions, use the `prometheus-async` library instead of the standard `prometheus_client.Histogram.time()` decorator (which only works correctly with sync functions).

```bash
# Install prometheus-async
pip install prometheus-async
# or with uv
uv add prometheus-async
```

```python
from prometheus_client import Histogram
from prometheus_async.aio import time as prom_async_time

# Define metrics
LATENCY = Histogram("workflow_latency_seconds", "Workflow latency")

@prom_async_time(LATENCY)
async def timed_workflow(state: dict) -> dict:
    """Execute workflow with automatic latency tracking.

    Note: Standard prometheus_client.Histogram.time() does NOT work
    correctly with async functions - use prometheus_async.aio.time instead.
    """
    result = await graph.ainvoke(state)
    return result
```

**Sync functions** can still use the standard decorator:
```python
from prometheus_client import Histogram

LATENCY = Histogram("workflow_latency_seconds", "Workflow latency")

@LATENCY.time()
def sync_workflow(state: dict) -> dict:
    """Execute sync workflow with latency tracking."""
    return graph.invoke(state)
```

## Cost Optimization

1. **Cache aggressively** - Avoid repeated identical calls
2. **Use cheaper models** - Claude Haiku for simple tasks, Sonnet for complex
3. **Optimize prompts** - Shorter prompts = fewer tokens
4. **Batch requests** - Reduce API overhead
5. **Monitor usage** - Track and alert on high costs

## Profiling

```python
import cProfile
import pstats

# Define state for profiling
state = {"messages": ["What is Python?"]}

profiler = cProfile.Profile()
profiler.enable()

result = graph.invoke(state)

profiler.disable()
stats = pstats.Stats(profiler)
stats.sort_stats('cumulative')
stats.print_stats(10)  # Top 10 slowest functions
```

## References

- [LangGraph Caching Reference](https://reference.langchain.com/python/langgraph/cache/) - Official cache API documentation
- [LangGraph Streaming](https://docs.langchain.com/oss/python/langgraph/streaming) - Streaming modes and patterns
- [prometheus-async Documentation](https://prometheus-async.readthedocs.io/) - Async metrics support
- [LangChain-Anthropic](https://reference.langchain.com/python/integrations/langchain_anthropic/) - ChatAnthropic integration
