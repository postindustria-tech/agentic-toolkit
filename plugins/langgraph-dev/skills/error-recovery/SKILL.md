---
name: error-recovery-in-langgraph
description: This skill should be used when the user asks about "error handling", "error recovery", "fallback", "retry logic", "RetryPolicy", "checkpointing", "fault tolerance", "exception handling", or needs guidance on implementing robust error handling in LangGraph workflows.
version: 0.3.1
---

# Error Recovery in LangGraph

Error recovery in LangGraph enables workflows to handle failures gracefully through built-in retry policies, checkpointing for fault tolerance, and custom fallback patterns.

## Required Imports

```python
from typing import TypedDict, Optional, Any
from langchain_core.messages import BaseMessage, AIMessage, HumanMessage
from langgraph.graph import StateGraph, START, END
from langgraph.types import RetryPolicy
from langgraph.checkpoint.memory import InMemorySaver
import asyncio
# IMPORTANT: asyncio.timeout requires Python 3.11+
# For Python 3.10: pip install async-timeout && from async_timeout import timeout
```

---

## RetryPolicy - Built-in Retry Mechanism (Recommended)

LangGraph provides a built-in `RetryPolicy` for automatic error recovery with exponential backoff and jitter. This is the primary and recommended approach for handling transient failures.

### Basic Usage

```python
from typing import TypedDict, Optional, Any
from langgraph.graph import StateGraph, START, END
from langgraph.types import RetryPolicy

class State(TypedDict):
    query: str
    result: Optional[str]
    error: Optional[str]

def api_call_node(state: State) -> dict[str, Any]:
    """Node that calls an external API.

    NOTE: Replace `fetch_from_api` with your actual API client.
    This is a placeholder function for demonstration.
    """
    def fetch_from_api(query: str) -> str:
        """Placeholder for your API client. Replace with actual implementation."""
        # Example: return requests.get(f"https://api.example.com/search?q={query}").text
        return f"Result for: {query}"

    response = fetch_from_api(state["query"])
    return {"result": response, "error": None}

# Create workflow with retry policy
workflow = StateGraph(State)
workflow.add_node(
    "api_call",
    api_call_node,
    retry_policy=RetryPolicy(max_attempts=5)
)
workflow.add_edge(START, "api_call")
workflow.add_edge("api_call", END)

graph = workflow.compile()
```

### RetryPolicy Parameters

| Parameter | Default | Description |
|-----------|---------|-------------|
| `initial_interval` | 0.5 | Seconds before first retry |
| `backoff_factor` | 2.0 | Multiplier for exponential backoff |
| `max_interval` | 128.0 | Maximum seconds between retries |
| `max_attempts` | 3 | Total attempts including first |
| `jitter` | True | Add randomization to prevent thundering herd |
| `retry_on` | `default_retry_on` | Exception filter (callable or exception types) |

### Complete RetryPolicy Example

```python
from typing import Any
from langgraph.types import RetryPolicy
from langgraph.graph import StateGraph, START, END

def call_external_service(state: State) -> dict[str, Any]:
    """Node that calls an external service.

    Replace with your actual external service call.
    """
    # Placeholder implementation
    return {"result": f"Service response for: {state.get('query', '')}", "error": None}

workflow = StateGraph(State)

# Custom retry configuration
workflow.add_node(
    "external_service",
    call_external_service,
    retry_policy=RetryPolicy(
        initial_interval=1.0,    # Wait 1 second before first retry
        backoff_factor=2.0,      # Double wait time each retry
        max_interval=60.0,       # Never wait more than 60 seconds
        max_attempts=5,          # Try up to 5 times total
        jitter=True              # Add randomization
    )
)
workflow.add_edge(START, "external_service")
workflow.add_edge("external_service", END)
```

### Default Retry Behavior

The `default_retry_on` function determines which exceptions trigger retries:

**Exceptions NOT retried** (programming/logic errors):
- `ValueError`, `TypeError`, `ArithmeticError`
- `ImportError`, `LookupError`, `NameError`
- `SyntaxError`, `RuntimeError`, `ReferenceError`
- `StopIteration`, `StopAsyncIteration`, `OSError`

**Exceptions that ARE retried**:
- `ConnectionError` - always retried
- `httpx.HTTPStatusError` - retried only for 5xx status codes
- `requests.HTTPError` - retried only for 5xx status codes
- All other exceptions - retried by default

### Custom retry_on Function

```python
import httpx
from typing import Any
from langgraph.types import RetryPolicy

def rate_limited_api_node(state: State) -> dict[str, Any]:
    """Node that calls a rate-limited API.

    Replace with your actual rate-limited API call.
    """
    # Placeholder implementation
    return {"result": f"Rate-limited API response for: {state.get('query', '')}", "error": None}

def retry_on_rate_limit(exc: Exception) -> bool:
    """Retry on rate limits and server errors only."""
    if isinstance(exc, httpx.HTTPStatusError):
        return exc.response.status_code in (429, 500, 502, 503, 504)
    # Don't retry programming errors
    return not isinstance(exc, (ValueError, TypeError, KeyError))

workflow.add_node(
    "rate_limited_api",
    rate_limited_api_node,
    retry_policy=RetryPolicy(
        max_attempts=10,
        retry_on=retry_on_rate_limit
    )
)
```

---

## Checkpointing for Fault Tolerance

Checkpointers save graph state at each superstep, enabling recovery from failures and providing an audit trail of execution.

### Basic Checkpointing Setup

```python
from typing import TypedDict, Optional, Any
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.graph import StateGraph, START, END

class State(TypedDict):
    messages: list[str]
    step: str
    error: Optional[str]

def process_node(state: State) -> dict[str, Any]:
    return {"step": "processed", "messages": state["messages"] + ["Processed"]}

# Create checkpointer
# NOTE: InMemorySaver is for testing/debugging only.
# For production, use PostgresSaver from langgraph-checkpoint-postgres
checkpointer = InMemorySaver()

# Build workflow
workflow = StateGraph(State)
workflow.add_node("process", process_node)
workflow.add_edge(START, "process")
workflow.add_edge("process", END)

# Compile with checkpointer
graph = workflow.compile(checkpointer=checkpointer)

# Each invocation uses a thread_id for state tracking
config = {"configurable": {"thread_id": "conversation_123"}}
result = graph.invoke({"messages": ["Hello"], "step": "start", "error": None}, config)
```

### Recovery from Failure

```python
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.graph import StateGraph, START, END

checkpointer = InMemorySaver()
graph = workflow.compile(checkpointer=checkpointer)
config = {"configurable": {"thread_id": "task_456"}}

# Define initial state for the workflow
initial_state: State = {"messages": ["Hello"], "step": "start", "error": None}

try:
    result = graph.invoke(initial_state, config)
except Exception as e:
    # Get last successful state from checkpoint
    state_snapshot = graph.get_state(config)
    print(f"Failed at step: {state_snapshot.values.get('step')}")
    print(f"Last successful state: {state_snapshot.values}")

    # Resume from checkpoint - re-invoke with same thread_id
    # The graph loads the last checkpoint state automatically
    result = graph.invoke(state_snapshot.values, config)
```

### Production Checkpointers

For production use, prefer persistent checkpointers.

**Important**: Checkpoint savers are in separate packages since LangGraph v0.2:

```python
# SQLite (local persistence)
# Install: pip install langgraph-checkpoint-sqlite
from langgraph.checkpoint.sqlite import SqliteSaver

with SqliteSaver.from_conn_string("checkpoints.db") as checkpointer:
    graph = workflow.compile(checkpointer=checkpointer)

# PostgreSQL (production, recommended)
# Install: pip install langgraph-checkpoint-postgres
from langgraph.checkpoint.postgres import PostgresSaver

with PostgresSaver.from_conn_string("postgresql://user:pass@localhost/db") as checkpointer:
    checkpointer.setup()  # Required on first use to create tables
    graph = workflow.compile(checkpointer=checkpointer)
```

---

## Async Error Handling

Use async patterns for non-blocking error recovery in async workflows.

### Async Node with Error Handling

```python
import asyncio
from typing import TypedDict, Optional, Any

class State(TypedDict):
    query: str
    result: Optional[str]
    error: Optional[str]

async def async_api_node(state: State) -> dict[str, Any]:
    """Async node with proper error handling.

    NOTE: Replace `fetch_async_api` with your actual async API client.
    """
    async def fetch_async_api(query: str) -> str:
        """Placeholder async API client. Replace with actual implementation."""
        await asyncio.sleep(0.1)  # Simulate API latency
        return f"Async result for: {query}"

    try:
        async with asyncio.timeout(30):  # 30 second timeout
            result = await fetch_async_api(state["query"])
            return {"result": result, "error": None}
    except asyncio.CancelledError:
        # Always re-raise cancellation - never swallow it
        raise
    except asyncio.TimeoutError:
        return {"error": "Operation timed out after 30 seconds", "result": None}
    except Exception as e:
        return {"error": f"{type(e).__name__}: {str(e)}", "result": None}
```

### Async Graph Invocation

```python
from langgraph.checkpoint.memory import InMemorySaver

checkpointer = InMemorySaver()
graph = workflow.compile(checkpointer=checkpointer)
config = {"configurable": {"thread_id": "async_task_789"}}

# Define initial state and use ainvoke for async execution
initial_state: State = {"query": "example query", "result": None, "error": None}
result = await graph.ainvoke(initial_state, config)
```

### Critical: Async Checkpointer Compatibility

When using async checkpointers, you MUST use async methods. Note: `InMemorySaver` supports both sync and async methods.

```python
# Async checkpointer imports:
# from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
# from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver

# CORRECT - use ainvoke with async checkpointers
result = await graph.ainvoke(state, config)
state = await graph.aget_state(config)

# WRONG - using sync invoke with async checkpointer will HANG
# result = graph.invoke(state, config)  # DO NOT DO THIS
```

---

## Manual Error Patterns

For cases requiring custom logic beyond RetryPolicy.

### Error Tracking State

```python
from typing import TypedDict, Optional, Any
from langchain_core.messages import BaseMessage, AIMessage

class State(TypedDict):
    messages: list[BaseMessage]
    step: str  # Consistent with other examples in this document
    error_count: int
    error: Optional[str]

def handle_error(state: State) -> dict[str, Any]:
    """Handle errors with retry limit."""
    error_count = state["error_count"] + 1

    if error_count > 3:
        # Reset after too many errors
        return {
            "messages": [AIMessage(content="Let's start over due to repeated errors.")],
            "error_count": 0,
            "step": "restart",
            "error": None
        }

    # Retry
    return {
        "messages": [AIMessage(content="I encountered an issue. Let me try again.")],
        "error_count": error_count,
        "step": "retry"
    }
```

### Conditional Retry Routing

```python
from typing import Any
from langgraph.graph import StateGraph, START, END

def process_node(state: State) -> dict[str, Any]:
    """Process node that may fail and require retry.

    Replace with your actual processing logic.
    """
    # Simulate processing that could set an error
    if state.get("error"):
        return {"step": "failed", "error": state["error"]}
    return {"step": "processed", "error": None, "error_count": 0}

def should_retry(state: State) -> str:
    """Determine if workflow should retry or finish."""
    if state["error_count"] < 3 and state.get("error"):
        return "retry"
    return "done"

workflow = StateGraph(State)
workflow.add_node("process", process_node)
workflow.add_node("handle_error", handle_error)

workflow.add_edge(START, "process")
workflow.add_conditional_edges(
    "process",
    should_retry,
    {"retry": "handle_error", "done": END}
)
workflow.add_edge("handle_error", "process")  # Loop back to retry
```

### Try-Catch in Nodes

```python
from typing import Any

def safe_node(state: State) -> dict[str, Any]:
    """Node with exception handling."""
    def risky_operation(state: State) -> str:
        """Placeholder for an operation that might fail.

        Replace with your actual operation.
        """
        if not state.get("messages"):
            raise ValueError("Messages are required")
        return f"Processed {len(state.get('messages', []))} messages"

    try:
        result = risky_operation(state)
        return {"result": result, "error": None}
    except ValueError as e:
        # Handle validation errors differently
        return {"error": f"Validation failed: {e}", "error_count": state.get("error_count", 0) + 1}
    except Exception as e:
        # Generic error handling
        return {"error": str(e), "error_count": state.get("error_count", 0) + 1}
```

### Fallback Routing

```python
from typing import Any
from langgraph.graph import StateGraph

def check_errors(state: State) -> str:
    """Route based on error state."""
    if state.get("error"):
        return "error_handler"
    return "continue"

def next_step_node(state: State) -> dict[str, Any]:
    """Continue to next step after successful processing."""
    return {"step": "completed"}

# Note: process_node and handle_error are defined in previous sections
workflow = StateGraph(State)
workflow.add_node("process", process_node)
workflow.add_node("error_handler", handle_error)
workflow.add_node("next_step", next_step_node)

workflow.add_conditional_edges(
    "process",
    check_errors,
    {"error_handler": "error_handler", "continue": "next_step"}
)
```

---

## Manual Exponential Backoff

Note: Prefer `RetryPolicy` for automatic retries. Use manual backoff only for custom requirements.

### Sync Version (for sync-only workflows)

```python
import time
from typing import Any

def retry_with_backoff_sync(state: State) -> dict[str, Any]:
    """Manual backoff for synchronous workflows only."""
    def external_api_call(state: State) -> str:
        """Placeholder sync API call. Replace with your actual implementation."""
        return f"Sync result for retry_count={state.get('retry_count', 0)}"

    retry_count = state.get("retry_count", 0)
    wait_time = min(2 ** retry_count, 60)  # Cap at 60 seconds

    if retry_count > 0:
        time.sleep(wait_time)  # Only use in sync-only workflows

    try:
        result = external_api_call(state)
        return {"result": result, "retry_count": 0, "error": None}
    except Exception as e:
        return {"error": str(e), "retry_count": retry_count + 1}
```

### Async Version (for async workflows)

```python
import asyncio
from typing import Any

async def retry_with_backoff_async(state: State) -> dict[str, Any]:
    """Non-blocking backoff for async workflows."""
    async def external_async_api(state: State) -> str:
        """Placeholder async API call. Replace with your actual implementation."""
        await asyncio.sleep(0.1)  # Simulate network latency
        return f"Async result for retry_count={state.get('retry_count', 0)}"

    retry_count = state.get("retry_count", 0)
    wait_time = min(2 ** retry_count, 60)  # Cap at 60 seconds

    if retry_count > 0:
        await asyncio.sleep(wait_time)  # Non-blocking

    try:
        result = await external_async_api(state)
        return {"result": result, "retry_count": 0, "error": None}
    except Exception as e:
        return {"error": str(e), "retry_count": retry_count + 1}
```

---

## Choosing an Error Handling Strategy

| Approach | Use Case | Pros | Cons |
|----------|----------|------|------|
| **RetryPolicy** | Transient failures (network, API) | Built-in, configurable, async-safe | No custom logic between retries |
| **Checkpointing** | Long workflows, crash recovery | Full state recovery, audit trail | Storage overhead |
| **Manual retry loops** | Complex retry logic, custom backoff | Full control | More code, error-prone |
| **Conditional edges** | Route to fallback nodes | Flexible routing | Increases graph complexity |

---

## Best Practices

1. **Use RetryPolicy first** - Built-in mechanism handles most retry scenarios
2. **Enable checkpointing** - Always use checkpointers for production workflows
3. **Limit retries** - Prevent infinite loops with `max_attempts`
4. **Log errors** - Track failures for debugging and monitoring
5. **Use async properly** - Never mix `time.sleep()` in async workflows
6. **Handle cancellation** - Always re-raise `asyncio.CancelledError`
7. **Graceful degradation** - Provide partial results when possible
8. **User feedback** - Inform users of recovery attempts

---

## Documentation References

- [How to Add Node Retry Policies](https://docs.langchain.com/oss/python/langgraph/graph-api#add-retry-policies)
- [LangGraph Persistence](https://docs.langchain.com/oss/python/langgraph/persistence)
- [LangGraph Types Reference](https://reference.langchain.com/python/langgraph/types/)
- [LangGraph Checkpointing Reference](https://reference.langchain.com/python/langgraph/checkpoints/)
