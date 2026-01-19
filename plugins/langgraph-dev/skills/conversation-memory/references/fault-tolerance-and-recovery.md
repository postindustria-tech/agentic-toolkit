# Fault Tolerance and Recovery

## Overview

LangGraph's checkpointing system provides automatic fault tolerance through pending writes and checkpoint-based recovery. When nodes fail mid-execution, LangGraph preserves completed work and enables resumption without re-executing successful nodes.

This guide covers:
- Pending writes mechanism
- Recovery strategies
- Idempotency considerations
- Production recovery patterns
- Error inspection and diagnosis

## Pending Writes Mechanism

### How Supersteps Work

LangGraph executes nodes in **supersteps** - batches of nodes that can run in parallel. Within a superstep:

1. All schedulable nodes start execution concurrently
2. Each node that completes successfully writes its output
3. If **all** nodes succeed, a checkpoint is created with all writes
4. If **any** node fails, the superstep fails, but successful writes are preserved as "pending writes"

### Pending Writes on Failure

When a node fails, LangGraph stores outputs from nodes that succeeded in the same superstep. These are called **pending writes** and are included in the checkpoint's metadata.

```python
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.graph import StateGraph, START, END
from typing_extensions import TypedDict

class State(TypedDict):
    results: list

def task_a(state: State):
    print("Task A executing...")
    return {"results": state["results"] + ["a"]}

def task_b(state: State):
    print("Task B executing...")
    return {"results": state["results"] + ["b"]}

def task_c(state: State):
    print("Task C executing...")
    raise ValueError("Task C failed!")

def aggregate(state: State):
    return {"results": state["results"] + ["aggregated"]}

# Build graph with parallel tasks
builder = StateGraph(State)
builder.add_node("task_a", task_a)
builder.add_node("task_b", task_b)
builder.add_node("task_c", task_c)
builder.add_node("aggregate", aggregate)

# Parallel fan-out
builder.add_edge(START, "task_a")
builder.add_edge(START, "task_b")
builder.add_edge(START, "task_c")

# Fan-in to aggregate
builder.add_edge("task_a", "aggregate")
builder.add_edge("task_b", "aggregate")
builder.add_edge("task_c", "aggregate")
builder.add_edge("aggregate", END)

graph = builder.compile(checkpointer=InMemorySaver())

config = {"configurable": {"thread_id": "fault-demo"}}

try:
    result = graph.invoke({"results": []}, config)
except ValueError as e:
    print(f"Execution failed: {e}")

    # Inspect state after failure
    snapshot = graph.get_state(config)

    # Check pending writes
    print(f"Metadata writes: {snapshot.metadata.get('writes', {})}")
    # Output: {'task_a': {'results': ['a']}, 'task_b': {'results': ['b']}}

    # task_a and task_b completed successfully
    # Their outputs are preserved in checkpoint metadata
    # Only task_c needs to be retried or fixed
```

**Key Points**:
- Pending writes are stored in `snapshot.metadata['writes']`
- Successful node outputs are preserved even when superstep fails
- State is NOT updated yet (since superstep failed)
- On resume, LangGraph applies pending writes and skips re-execution

### Automatic Deduplication on Resume

When resuming from a failed checkpoint, LangGraph:

1. Applies pending writes from successful nodes to state
2. Skips re-executing those nodes (deduplication)
3. Only retries failed nodes
4. Continues execution normally

```python
# Fix the failure and resume
fixed_config = graph.update_state(
    config,
    values={"results": ["a", "b", "c"]},  # Manually provide task_c's output
    as_node="task_c"  # Pretend this came from task_c
)

# Resume execution
result = graph.invoke(None, fixed_config)
print(f"Result: {result}")  # {'results': ['a', 'b', 'c', 'aggregated']}

# Note: task_a and task_b did NOT re-execute
# Their pending writes were applied from the checkpoint
```

## Recovery Strategies

### Strategy 1: Automatic Retry (Idempotent Nodes)

If nodes are idempotent (safe to re-execute), simply retry the entire graph:

```python
import time

max_retries = 3
for attempt in range(max_retries):
    try:
        result = graph.invoke({"input": "data"}, config)
        break  # Success
    except Exception as e:
        print(f"Attempt {attempt + 1} failed: {e}")
        if attempt < max_retries - 1:
            time.sleep(2 ** attempt)  # Exponential backoff
        else:
            raise  # Final retry failed
```

**When to use**:
- Nodes have no side effects
- External API calls are idempotent (PUT, not POST)
- Failures are transient (network issues, rate limits)

**Pros**: Simple, no manual intervention
**Cons**: Wastes computation re-running successful nodes

### Strategy 2: Manual State Fix

For non-idempotent operations or logic errors, manually fix state and resume:

```python
try:
    result = graph.invoke({"data": "input"}, config)
except Exception as e:
    print(f"Error: {e}")

    # Inspect error
    snapshot = graph.get_state(config)
    if snapshot.tasks:
        for task in snapshot.tasks:
            if task.error:
                print(f"Failed node: {task.name}")
                print(f"Error details: {task.error}")

    # Fix the issue manually
    fixed_config = graph.update_state(
        config,
        values={"data": "corrected_input"},  # Fix problematic data
        as_node="failed_node"  # Pretend it came from the failed node
    )

    # Resume
    result = graph.invoke(None, fixed_config)
```

**When to use**:
- Logic errors in data
- Need to skip a problematic node
- Manual intervention required

**Pros**: Precise control, no wasted computation
**Cons**: Requires human intervention

### Strategy 3: Conditional Retry with Fallback

Retry with different parameters or fallback strategy:

```python
def resilient_invoke(graph, initial_input, config, max_retries=3):
    """Invoke with automatic fallback on failure."""
    for attempt in range(max_retries):
        try:
            return graph.invoke(initial_input, config)
        except Exception as e:
            snapshot = graph.get_state(config)

            # Check if specific node failed
            if snapshot.tasks and any(t.name == "api_call" and t.error for t in snapshot.tasks):
                # Use cached fallback instead
                fallback_config = graph.update_state(
                    config,
                    values={"use_cache": True},
                    as_node="api_call"
                )
                return graph.invoke(None, fallback_config)

            # Other errors: retry
            if attempt < max_retries - 1:
                continue
            raise
```

**When to use**:
- External API failures with cache fallback
- Primary/secondary service pattern
- Graceful degradation scenarios

## Error Inspection

### Accessing Error Information

Errors are stored in `StateSnapshot.tasks`. Each `PregelTask` contains:

- `name`: Node name that failed
- `error`: Exception information
- `interrupts`: Any interrupts that occurred
- `state`: Task state (pending, error, success)

```python
snapshot = graph.get_state(config)

# Check for errors
if snapshot.tasks:
    for task in snapshot.tasks:
        if task.error:
            print(f"Node '{task.name}' failed")
            print(f"Error type: {type(task.error).__name__}")
            print(f"Error message: {task.error}")

            # Detailed error information
            if hasattr(task.error, '__traceback__'):
                import traceback
                traceback.print_exception(
                    type(task.error),
                    task.error,
                    task.error.__traceback__
                )
```

### Identifying Failing Nodes

```python
def get_failed_nodes(snapshot):
    """Extract names of all failed nodes from snapshot."""
    if not snapshot.tasks:
        return []

    return [
        task.name
        for task in snapshot.tasks
        if task.error is not None
    ]

# Usage
snapshot = graph.get_state(config)
failed = get_failed_nodes(snapshot)
print(f"Failed nodes: {failed}")
```

## Idempotency Considerations

### Idempotent Operations

Safe to retry without side effects:

```python
# ✅ Idempotent: Reading data
def fetch_user(state):
    user = database.get_user(state["user_id"])  # Safe to call multiple times
    return {"user": user}

# ✅ Idempotent: Pure computation
def calculate(state):
    result = state["value"] * 2  # No external effects
    return {"result": result}

# ✅ Idempotent: PUT requests (update)
def update_record(state):
    api.put(f"/records/{state['id']}", data=state["data"])  # Idempotent HTTP
    return {"updated": True}
```

### Non-Idempotent Operations

Require careful handling:

```python
# ❌ Non-idempotent: Creating records
def create_record(state):
    record_id = api.post("/records", data=state["data"])  # Creates new record each time
    return {"record_id": record_id}

# ✅ Solution: Check if already created
def create_record_safe(state):
    if "record_id" in state and state["record_id"]:
        # Already created in previous attempt
        return {"record_id": state["record_id"]}

    record_id = api.post("/records", data=state["data"])
    return {"record_id": record_id}
```

### Designing for Retryability

1. **Check Before Create**: Verify resource doesn't exist before creating
2. **Use Idempotency Keys**: Include unique keys in API requests
3. **Store Completion Status**: Track which steps completed successfully
4. **Separate Reads from Writes**: Place writes in separate nodes

```python
class State(TypedDict):
    data: dict
    api_key_created: bool  # Tracks completion
    api_key: str | None

def create_api_key(state: State):
    """Idempotent API key creation."""
    if state.get("api_key_created"):
        return {}  # Already created

    # Create with idempotency key (derived from user ID)
    idempotency_key = f"user_{state['user_id']}_api_key"
    api_key = api.create_key(idempotency_key=idempotency_key)

    return {"api_key": api_key, "api_key_created": True}
```

## Production Recovery Patterns

### Circuit Breaker Pattern

Prevent cascade failures by stopping retries after threshold:

```python
from datetime import datetime, timedelta

class CircuitBreaker:
    def __init__(self, failure_threshold=5, timeout=60):
        self.failure_threshold = failure_threshold
        self.timeout = timeout
        self.failures = 0
        self.last_failure_time = None
        self.state = "closed"  # closed, open, half-open

    def call(self, func, *args, **kwargs):
        if self.state == "open":
            # Check if timeout expired
            if datetime.now() - self.last_failure_time > timedelta(seconds=self.timeout):
                self.state = "half-open"
            else:
                raise Exception("Circuit breaker is open")

        try:
            result = func(*args, **kwargs)
            if self.state == "half-open":
                self.reset()
            return result
        except Exception as e:
            self.failures += 1
            self.last_failure_time = datetime.now()

            if self.failures >= self.failure_threshold:
                self.state = "open"
            raise e

    def reset(self):
        self.failures = 0
        self.state = "closed"

# Usage
breaker = CircuitBreaker()

try:
    result = breaker.call(graph.invoke, {"input": "data"}, config)
except Exception as e:
    print(f"Circuit breaker prevented execution: {e}")
```

### Exponential Backoff

Retry with increasing delays:

```python
import time
import random

def invoke_with_backoff(graph, input, config, max_retries=5):
    """Invoke with exponential backoff on failure."""
    for attempt in range(max_retries):
        try:
            return graph.invoke(input, config)
        except Exception as e:
            if attempt == max_retries - 1:
                raise  # Final attempt

            # Exponential backoff with jitter
            delay = (2 ** attempt) + random.uniform(0, 1)
            print(f"Attempt {attempt + 1} failed, retrying in {delay:.2f}s...")
            time.sleep(delay)
```

### Dead Letter Queue

Store failed executions for manual review:

```python
def invoke_with_dlq(graph, input, config, dlq_handler):
    """Invoke with dead letter queue for failures."""
    try:
        return graph.invoke(input, config)
    except Exception as e:
        # Store in dead letter queue
        dlq_entry = {
            "thread_id": config['configurable']['thread_id'],
            "input": input,
            "error": str(e),
            "timestamp": datetime.now().isoformat(),
            "checkpoint_id": graph.get_state(config).config['configurable']['checkpoint_id']
        }
        dlq_handler.store(dlq_entry)

        # Re-raise or return error response
        raise
```

### Health Monitoring

Track recovery metrics for observability:

```python
class RecoveryMonitor:
    def __init__(self):
        self.total_executions = 0
        self.failures = 0
        self.recoveries = 0

    def record_execution(self, success=True, recovered=False):
        self.total_executions += 1
        if not success:
            self.failures += 1
        if recovered:
            self.recoveries += 1

    def get_metrics(self):
        return {
            "total_executions": self.total_executions,
            "failures": self.failures,
            "recoveries": self.recoveries,
            "failure_rate": self.failures / max(self.total_executions, 1),
            "recovery_rate": self.recoveries / max(self.failures, 1)
        }

# Usage
monitor = RecoveryMonitor()

try:
    result = graph.invoke(input, config)
    monitor.record_execution(success=True)
except Exception as e:
    monitor.record_execution(success=False)
    # Attempt recovery
    # If successful: monitor.record_execution(recovered=True)

print(monitor.get_metrics())
```

## Best Practices

1. **Design Idempotent Nodes**: Make node functions safe to retry
2. **Use Pending Writes**: Leverage automatic deduplication instead of re-executing
3. **Separate Concerns**: Split risky operations into separate nodes
4. **Log Checkpoint IDs**: Track checkpoint_id in logs for debugging
5. **Implement Retries Carefully**: Use exponential backoff and circuit breakers
6. **Monitor Recovery Rates**: Track metrics to identify systemic issues
7. **Test Failure Scenarios**: Simulate failures to verify recovery works
8. **Document Non-Idempotent Operations**: Clearly mark and handle carefully

## Common Pitfalls

- **Assuming Full Re-execution**: Pending writes mean only failed nodes retry
- **Ignoring Side Effects**: Non-idempotent operations need special handling
- **Infinite Retries**: Always set max retry limits
- **Missing Error Inspection**: Check `tasks` field for detailed error info
- **Not Testing Recovery**: Test recovery paths, not just happy paths
- **Synchronous Retries**: Use async/background retries for better UX
