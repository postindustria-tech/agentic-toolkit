# Performance Optimization and Checkpoint Management

This reference provides guidance on optimizing LangGraph performance and managing checkpoints effectively.

## Contents

1. [Performance Optimization](#performance-optimization)
2. [Checkpoint Configuration](#checkpoint-configuration)
3. [Production Checkpointing](#production-checkpointing)
4. [State Size Management](#state-size-management)
5. [Execution Monitoring](#execution-monitoring)

---

## Performance Optimization

### Pattern: Minimize State Size

**Purpose**: Reduce memory usage and serialization overhead.

**Problem**: Large state objects slow down graph execution.

```python
from typing import TypedDict, List

# ❌ BAD: Storing large objects in state
class BadState(TypedDict):
    llm_instance: Any  # Don't store LLM instances
    vectorstore: Any  # Don't store databases
    embeddings: List[List[float]]  # Huge arrays
    raw_documents: List[str]  # Large text

# ✅ GOOD: Store references and results only
class GoodState(TypedDict):
    document_ids: List[str]  # References, not full docs
    query: str  # Input only
    result_text: str  # Final result only
    metadata: dict  # Small metadata only
```

**Key Points**:
- Store IDs/references instead of full objects
- Don't store model instances or connections
- Keep only essential data in state
- Use external storage for large datasets

---

### Pattern: Lazy Loading

**Purpose**: Load data only when needed, not upfront.

```python
class LazyState(TypedDict):
    document_id: str
    document_content: str  # Loaded on demand
    processed: bool

def lazy_load_node(state: LazyState) -> dict:
    """
    Load document content only when this node executes.

    Don't preload in initial state - load in the node that needs it.
    """
    if not state.get("processed"):
        # Load from external source (DB, file, API)
        content = load_document_from_db(state["document_id"])
        return {
            "document_content": content,
            "processed": True
        }

    return {}  # No changes if already processed
```

**Key Points**:
- Initialize state with minimal data
- Load expensive data in nodes that need it
- Clean up large data after use
- Don't pass large objects between nodes unnecessarily

---

### Pattern: Parallel Node Execution

**Purpose**: Execute independent nodes concurrently for speed.

```python
from typing import Annotated
import operator

class ParallelState(TypedDict):
    query: str
    results: Annotated[List[dict], operator.add]  # Accumulates parallel results

# These nodes can run in parallel
def fetch_from_db(state: ParallelState) -> dict:
    """Fetch from database (independent operation)."""
    result = {"source": "db", "data": "..."}
    return {"results": [result]}

def fetch_from_api(state: ParallelState) -> dict:
    """Fetch from API (independent operation)."""
    result = {"source": "api", "data": "..."}
    return {"results": [result]}

def fetch_from_cache(state: ParallelState) -> dict:
    """Fetch from cache (independent operation)."""
    result = {"source": "cache", "data": "..."}
    return {"results": [result]}

# Graph structure for parallelism:
# workflow.add_edge("start", "fetch_db")
# workflow.add_edge("start", "fetch_api")
# workflow.add_edge("start", "fetch_cache")
#
# All three nodes execute concurrently because they don't depend on each other
```

**Key Points**:
- Independent nodes can run in parallel
- Use `operator.add` to accumulate results
- Fan-out from one node, fan-in to next
- Significant speedup for I/O-bound operations

---

### Pattern: Caching LLM Calls

**Purpose**: Avoid redundant expensive operations.

```python
from functools import lru_cache

# Cache expensive LLM calls
@lru_cache(maxsize=100)
def cached_llm_call(prompt: str) -> str:
    """
    Cache LLM responses.

    Note: Only works for deterministic prompts.
    Use external cache (Redis) for production.
    """
    response = llm.invoke(prompt)
    return response.content

def node_with_cache(state: TypedDict) -> dict:
    """Node that uses cached LLM calls."""
    prompt = state["prompt"]

    # This will hit cache on repeated prompts
    result = cached_llm_call(prompt)

    return {"result": result}
```

**Production Caching**:

```python
import redis
import json

class ProductionCache:
    """Redis-based cache for production use."""

    def __init__(self, redis_url: str, ttl: int = 3600):
        self.client = redis.from_url(redis_url)
        self.ttl = ttl

    def get(self, key: str):
        """Get cached value."""
        value = self.client.get(key)
        if value:
            return json.loads(value)
        return None

    def set(self, key: str, value: any):
        """Cache value with TTL."""
        self.client.setex(key, self.ttl, json.dumps(value))

# Usage
cache = ProductionCache("redis://localhost:6379")

def node_with_redis_cache(state: TypedDict) -> dict:
    """Node with Redis caching."""
    prompt = state["prompt"]
    cache_key = f"llm:{hash(prompt)}"

    # Check cache
    cached = cache.get(cache_key)
    if cached:
        return {"result": cached, "from_cache": True}

    # Call LLM
    result = llm.invoke(prompt).content

    # Cache result
    cache.set(cache_key, result)

    return {"result": result, "from_cache": False}
```

**Key Points**:
- Cache deterministic operations
- Use TTL to prevent stale data
- External cache (Redis) for distributed systems
- Monitor cache hit rate

---

## Checkpoint Configuration

### Pattern: Development vs Production Checkpointers

**Purpose**: Different checkpoint strategies for different environments.

**Development (InMemorySaver)**:

```python
from langgraph.checkpoint.memory import InMemorySaver

# For testing and development only
memory = InMemorySaver()
app = workflow.compile(checkpointer=memory)

# Pros: No setup, fast
# Cons: Not persistent, single process only
```

**Production (PostgresSaver)**:

```python
from langgraph.checkpoint.postgres import PostgresSaver
import psycopg

# For production use
conn_string = "postgresql://user:password@localhost:5432/langraph_db"
connection = psycopg.connect(conn_string)

# Note: Create checkpoint tables first
# PostgresSaver.create_tables(connection)

checkpointer = PostgresSaver(connection)
app = workflow.compile(checkpointer=checkpointer)

# Pros: Persistent, multi-process safe, resumable
# Cons: Requires database, slower than memory
```

**Key Points**:
- InMemorySaver: Development and testing only
- PostgresSaver: Production with persistence
- Other options: SQLiteSaver (local files), custom implementations
- Always use database checkpointers in production

---

### Pattern: Checkpoint Cleanup Strategies

**Purpose**: Prevent unlimited growth of checkpoint data.

```python
from datetime import datetime, timedelta
import psycopg

def cleanup_old_checkpoints(
    connection,
    older_than_days: int = 30
):
    """
    Delete checkpoints older than specified days.

    Run this periodically (e.g., daily cron job).
    """
    cutoff_date = datetime.now() - timedelta(days=older_than_days)

    with connection.cursor() as cursor:
        cursor.execute(
            """
            DELETE FROM checkpoints
            WHERE created_at < %s
            """,
            (cutoff_date,)
        )
        deleted_count = cursor.rowcount

    connection.commit()
    return deleted_count

# Usage: Clean up monthly
deleted = cleanup_old_checkpoints(connection, older_than_days=30)
print(f"Deleted {deleted} old checkpoints")
```

**Retention Policies**:

```python
def cleanup_by_status(connection, keep_completed: int = 7, keep_failed: int = 90):
    """
    Different retention for different statuses.

    - Completed: Keep 7 days
    - Failed: Keep 90 days (for debugging)
    - In-progress: Keep 30 days
    """
    # Implementation depends on your checkpoint schema
    pass
```

**Key Points**:
- Old checkpoints consume storage
- Set retention policies based on business needs
- Keep failed checkpoints longer for debugging
- Automate cleanup with scheduled jobs

---

## Production Checkpointing

### Pattern: Thread ID Management

**Purpose**: Organize checkpoints by conversation/session.

```python
from uuid import uuid4

class ConversationManager:
    """Manage conversation threads for checkpointing."""

    @staticmethod
    def new_conversation() -> str:
        """Create new conversation thread ID."""
        return f"conv-{uuid4()}"

    @staticmethod
    def user_conversation(user_id: str) -> str:
        """Get or create thread ID for user."""
        # In production, look up in database
        return f"user-{user_id}-main"

    @staticmethod
    def session_conversation(session_id: str) -> str:
        """Thread ID based on session."""
        return f"session-{session_id}"

# Usage patterns

# New conversation
thread_id = ConversationManager.new_conversation()
config = {"configurable": {"thread_id": thread_id}}
result = app.invoke(initial_state, config)

# User-specific conversation (persists across sessions)
thread_id = ConversationManager.user_conversation("user_123")
config = {"configurable": {"thread_id": thread_id}}
result = app.invoke(state, config)

# Session-specific (clears on logout)
thread_id = ConversationManager.session_conversation(session.id)
config = {"configurable": {"thread_id": thread_id}}
result = app.invoke(state, config)
```

**Key Points**:
- Thread IDs organize checkpoints
- Consistent naming convention
- Map thread IDs to business entities (users, sessions)
- Store thread ID mappings in database

---

### Pattern: Checkpoint Recovery

**Purpose**: Resume interrupted workflows.

```python
def get_latest_checkpoint(app, thread_id: str):
    """
    Get most recent checkpoint for conversation.

    Returns state dict or None if no checkpoints.
    """
    config = {"configurable": {"thread_id": thread_id}}

    # Get checkpoint history
    state = app.get_state(config)

    if state and state.values:
        return state.values

    return None

# Usage: Resume after interruption
thread_id = "conv-abc-123"
config = {"configurable": {"thread_id": thread_id}}

# Try to get existing state
checkpoint = get_latest_checkpoint(app, thread_id)

if checkpoint:
    # Resume from checkpoint
    print(f"Resuming conversation at step: {checkpoint.get('current_step')}")
    result = app.invoke(
        {"messages": ["Continue processing"]},
        config
    )
else:
    # Start new conversation
    print("Starting new conversation")
    result = app.invoke(initial_state, config)
```

**Key Points**:
- Checkpoints enable fault tolerance
- Resume after crashes or interruptions
- Check for existing state before starting
- Maintain conversation continuity

---

## State Size Management

### Pattern: State Pruning

**Purpose**: Remove unnecessary data from state periodically.

```python
class PrunableState(TypedDict):
    messages: List[str]
    intermediate_results: List[dict]
    final_result: str

def prune_state(state: PrunableState) -> dict:
    """
    Remove intermediate data after final result is generated.

    Call this node after completion to reduce checkpoint size.
    """
    if state.get("final_result"):
        # Keep only final result, discard intermediate data
        return {
            "intermediate_results": [],  # Clear
            "messages": state["messages"][-5:]  # Keep last 5 only
        }

    return {}  # No pruning yet

# Add pruning node to graph
# workflow.add_node("prune", prune_state)
# workflow.add_edge("final_step", "prune")
# workflow.add_edge("prune", END)
```

**Key Points**:
- Prune after workflow completes
- Keep only data needed for resume or display
- Especially important for long-running workflows
- Reduces checkpoint storage costs

---

## Execution Monitoring

### Pattern: Performance Metrics

**Purpose**: Track and optimize graph performance.

```python
import time
import logging

logger = logging.getLogger(__name__)

class PerformanceState(TypedDict):
    start_time: float
    node_timings: dict
    current_node: str

def timed_node(node_name: str, node_func):
    """
    Wrapper to add timing to nodes.

    Tracks how long each node takes to execute.
    """
    def wrapper(state: PerformanceState) -> dict:
        start = time.time()
        result = node_func(state)
        duration = time.time() - start

        # Update timings
        timings = state.get("node_timings", {})
        timings[node_name] = duration

        logger.info(f"Node {node_name} took {duration:.2f}s")

        # Add timing to result
        result["node_timings"] = timings

        return result

    return wrapper

# Usage
def slow_operation(state: PerformanceState) -> dict:
    time.sleep(1)  # Simulate slow operation
    return {"result": "done"}

# Wrap node with timing
workflow.add_node("slow", timed_node("slow", slow_operation))

# After execution, analyze timings
def analyze_performance(state: PerformanceState):
    """Analyze node performance."""
    timings = state.get("node_timings", {})

    total = sum(timings.values())
    print(f"Total execution time: {total:.2f}s")

    for node, duration in sorted(timings.items(), key=lambda x: -x[1]):
        percentage = (duration / total * 100) if total > 0 else 0
        print(f"  {node}: {duration:.2f}s ({percentage:.1f}%)")
```

**Key Points**:
- Track node execution times
- Identify performance bottlenecks
- Log slow operations
- Optimize slowest nodes first

---

## Best Practices Summary

### Performance

1. **Minimize state size**: Store references, not objects
2. **Use caching**: Cache expensive operations (LLM calls, API requests)
3. **Parallel execution**: Independent nodes should run concurrently
4. **Lazy loading**: Load data only when needed
5. **Monitor metrics**: Track execution times and optimize bottlenecks

### Checkpointing

1. **Use PostgresSaver in production**: InMemorySaver is for development only
2. **Manage thread IDs**: Consistent naming and mapping to business entities
3. **Clean up old checkpoints**: Implement retention policies
4. **Prune state**: Remove unnecessary data before checkpointing
5. **Enable recovery**: Design for resumability from any checkpoint

### Scalability

1. **Connection pooling**: Use connection pools for database checkpointers
2. **Horizontal scaling**: Stateless nodes enable multi-instance deployment
3. **Rate limiting**: Protect external services from overload
4. **Circuit breakers**: Prevent cascading failures
5. **Resource limits**: Set timeouts and memory limits

---

## References

- LangGraph Performance: https://docs.langchain.com/oss/python/langgraph/performance
- Checkpointing Guide: https://docs.langchain.com/oss/python/langgraph/persistence
- PostgresSaver: https://reference.langchain.com/python/langgraph/checkpoints/#postgresaver
- See `SKILL.md` for basic checkpoint usage
- See `examples/03_graph_with_checkpoints.py` for working code
