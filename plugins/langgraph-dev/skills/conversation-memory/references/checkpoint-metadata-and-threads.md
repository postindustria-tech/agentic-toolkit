# Checkpoint Metadata and Thread Management

## Overview

Every checkpoint in LangGraph includes rich metadata that provides insight into execution flow, performance, and debugging information. Combined with thread management, this metadata enables sophisticated multi-user applications, workflow monitoring, and execution analysis.

This guide covers:
- Complete checkpoint metadata field reference
- Thread concepts and lifecycle
- Multi-tenant isolation patterns
- Metadata-based querying and filtering
- Thread cleanup and archival strategies

## Checkpoint Metadata Fields

Checkpoint metadata is accessed via `StateSnapshot.metadata`, a dictionary containing execution details. All LangGraph checkpointers populate these fields automatically.

### Core Metadata Fields

| Field | Type | Description | Example |
|-------|------|-------------|---------|
| `step` | `int` | Execution step counter. `0` = initial checkpoint, increments after each superstep. | `0`, `1`, `2`, ... |
| `source` | `str` | Origin of this checkpoint. `"input"` = from user input, `"loop"` = from graph execution. | `"input"` or `"loop"` |
| `writes` | `dict[str, dict]` | Mapping of node names to their output values for this superstep. Shows which nodes executed and what they returned. | `{"node_a": {"value": 1}, "node_b": {"value": 2}}` |

### Accessing Metadata

```python
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.graph import StateGraph, START, END
from typing_extensions import TypedDict

class State(TypedDict):
    counter: int

def node_a(state: State):
    return {"counter": state["counter"] + 1}

def node_b(state: State):
    return {"counter": state["counter"] * 2}

builder = StateGraph(State)
builder.add_node("node_a", node_a)
builder.add_node("node_b", node_b)
builder.add_edge(START, "node_a")
builder.add_edge("node_a", "node_b")
builder.add_edge("node_b", END)

graph = builder.compile(checkpointer=InMemorySaver())

config = {"configurable": {"thread_id": "metadata-example"}}
result = graph.invoke({"counter": 1}, config)

# Inspect metadata
snapshot = graph.get_state(config)
metadata = snapshot.metadata

print(f"Step: {metadata['step']}")  # 2 (0=initial, 1=after node_a, 2=after node_b)
print(f"Source: {metadata['source']}")  # 'loop'
print(f"Writes: {metadata['writes']}")  # {'node_b': {'counter': 4}}

# Traverse history to see all writes
for snapshot in graph.get_state_history(config):
    print(f"Step {snapshot.metadata['step']}: {snapshot.metadata.get('writes', {})}")
```

**Output**:
```
Step 2: {'node_b': {'counter': 4}}
Step 1: {'node_a': {'counter': 2}}
Step 0: {}
```

### step Field

The `step` counter tracks execution progress:
- **0**: Initial checkpoint (created when graph.invoke() is called with user input)
- **1+**: Increments after each superstep (batch of node executions)

In a linear graph (`A -> B -> C`), you'll have checkpoints at steps 0, 1, 2, 3.
In a graph with parallel nodes (`A -> [B, C] -> D`), parallel nodes execute in same superstep.

**Use cases**:
- Find specific execution points: `next(s for s in history if s.metadata['step'] == 2)`
- Calculate execution length: `max(s.metadata['step'] for s in history)`
- Identify initialization vs execution checkpoints: `step == 0` vs `step > 0`

### source Field

Indicates checkpoint origin:
- **`"input"`**: Checkpoint created from user input (step 0)
- **`"loop"`**: Checkpoint created during graph execution (step 1+)

**Use cases**:
- Filter to execution checkpoints only: `[s for s in history if s.metadata['source'] == 'loop']`
- Find user input: `next(s for s in history if s.metadata['source'] == 'input')`

### writes Field

Dictionary mapping node names to their output dictionaries. Shows exactly what each node returned during this superstep.

```python
# Example: Graph with parallel nodes
# Superstep executes both node_a and node_b simultaneously
metadata['writes'] = {
    'node_a': {'field_1': 'value_a'},
    'node_b': {'field_2': 'value_b'}
}

# Example: Sequential execution
# Only one node executes per superstep
metadata['writes'] = {
    'node_a': {'field_1': 'value_a'}
}
```

**Use cases**:
- Find when a specific node executed: `'my_node' in snapshot.metadata.get('writes', {})`
- Extract node outputs: `snapshot.metadata['writes']['my_node']`
- Debug which nodes ran: `list(snapshot.metadata.get('writes', {}).keys())`

## Checkpoint IDs

In addition to metadata, every checkpoint has unique identifiers stored in `StateSnapshot.config['configurable']`.

### Checkpoint ID Fields

| Field | Type | Description |
|-------|------|-------------|
| `thread_id` | `str` | User-provided thread identifier. Required for all checkpoint operations. |
| `checkpoint_id` | `str` | Auto-generated UUID for this specific checkpoint. Unique across all threads. |
| `checkpoint_ns` | `str` | Namespace for subgraph checkpoints. Empty string `""` for main graph. |

### thread_id

The primary isolation boundary. All checkpoints with the same `thread_id` belong to the same execution history.

**Requirements**:
- Must be provided in config for all checkpoint operations
- Must be a string (common pattern: UUIDs, user IDs, session IDs)
- Should be unique per isolated conversation/workflow

```python
# Different thread_ids = completely isolated
config_1 = {"configurable": {"thread_id": "user-alice-session-1"}}
config_2 = {"configurable": {"thread_id": "user-bob-session-2"}}

graph.invoke({"data": "A"}, config_1)  # Alice's state
graph.invoke({"data": "B"}, config_2)  # Bob's state (separate)

# Retrieving state
state_1 = graph.get_state(config_1)  # Only sees Alice's checkpoints
state_2 = graph.get_state(config_2)  # Only sees Bob's checkpoints
```

### checkpoint_id

Auto-generated UUID assigned by the checkpointer when creating a checkpoint. Uniquely identifies this specific checkpoint globally.

**Format**: UUID string (e.g., `"1ef663ba-28fe-6528-8002-5a559208592c"`)

**Use cases**:
- Resume from specific checkpoint: Include `checkpoint_id` in config
- Compare checkpoints: Use `checkpoint_id` as unique key
- Audit trail: Log `checkpoint_id` for all executions

```python
# Get latest checkpoint
snapshot = graph.get_state(config)
checkpoint_id = snapshot.config['configurable']['checkpoint_id']

# Resume from that exact checkpoint later
specific_config = {
    "configurable": {
        "thread_id": "my-thread",
        "checkpoint_id": checkpoint_id
    }
}
specific_snapshot = graph.get_state(specific_config)
```

### checkpoint_ns

Namespace for subgraph checkpoints. When using nested graphs (subgraphs), each level has its own namespace.

**Default**: Empty string `""` for main graph
**Subgraphs**: Namespace like `"subgraph_name:node_name"`

Most users won't need to interact with this field directly.

## parent_config

`StateSnapshot.parent_config` links checkpoints into a history chain. It's a `RunnableConfig` (or `None`) pointing to the **previous** checkpoint.

```python
history = list(graph.get_state_history(config))

# Latest checkpoint
latest = history[0]
print(f"Latest checkpoint: {latest.config['configurable']['checkpoint_id']}")

# Its parent (the checkpoint before it)
if latest.parent_config:
    parent = graph.get_state(latest.parent_config)
    print(f"Parent checkpoint: {parent.config['configurable']['checkpoint_id']}")
    print(f"Parent step: {parent.metadata['step']}")  # One less than latest
```

**Traversing history manually**:
```python
# Walk backwards through checkpoints
current = graph.get_state(config)
while current.parent_config:
    print(f"Step {current.metadata['step']}: {current.values}")
    current = graph.get_state(current.parent_config)
```

**Note**: Using `get_state_history()` is more efficient than manual traversal.

## Thread Concepts

A **thread** is an isolated execution context identified by `thread_id`. All checkpoints in a thread share the same execution history.

### Thread Lifecycle

1. **Creation**: Thread is created implicitly on first `graph.invoke()` with a new `thread_id`
2. **Execution**: Each `invoke()` adds checkpoints to the thread
3. **Querying**: Use `get_state()` and `get_state_history()` to inspect thread state
4. **Resumption**: Continue execution from any checkpoint in the thread
5. **Archival/Deletion**: Manual cleanup via checkpointer-specific APIs

### Thread Isolation

Threads are **completely isolated** - state never leaks between threads:

```python
# Thread A
config_a = {"configurable": {"thread_id": "thread-a"}}
graph.invoke({"value": 1}, config_a)
graph.invoke({"value": 2}, config_a)

# Thread B (independent)
config_b = {"configurable": {"thread_id": "thread-b"}}
graph.invoke({"value": 100}, config_b)

# Query thread A - only sees its own state
state_a = graph.get_state(config_a)
print(state_a.values)  # Last state from thread A (value: 2)

# Query thread B - only sees its own state
state_b = graph.get_state(config_b)
print(state_b.values)  # Last state from thread B (value: 100)
```

**Isolation guarantees**:
- Separate checkpoint histories
- Separate state values
- No shared memory or state
- Concurrent execution safe (if checkpointer supports it)

## Multi-User Patterns

### Single Thread Per User

Simplest pattern: one thread for all of a user's interactions.

```python
user_id = "user-123"
config = {"configurable": {"thread_id": user_id}}

# All user interactions use same thread
graph.invoke({"query": "Hello"}, config)
graph.invoke({"query": "What's the weather?"}, config)

# User's full conversation history
history = list(graph.get_state_history(config))
```

**Pros**: Simple, maintains full context
**Cons**: Single long conversation, no topic separation

### Multiple Threads Per User

Better pattern: separate threads for different conversations/topics.

```python
import uuid

user_id = "user-123"

# Create new conversation thread
conversation_id = str(uuid.uuid4())
thread_id = f"{user_id}_conversation_{conversation_id}"
config = {"configurable": {"thread_id": thread_id}}

graph.invoke({"query": "Hello"}, config)

# List user's threads (requires custom implementation)
# You'd store {user_id: [thread_id1, thread_id2, ...]} mapping separately
user_threads = get_user_threads(user_id)  # Custom function
for thread_id in user_threads:
    state = graph.get_state({"configurable": {"thread_id": thread_id}})
    print(f"Thread {thread_id}: {state.values}")
```

### Multi-Tenant Isolation

For SaaS applications, ensure strict isolation between customers.

```python
def make_thread_config(customer_id: str, session_id: str):
    """Ensure customer_id is included for audit and isolation."""
    return {
        "configurable": {
            "thread_id": f"customer_{customer_id}_session_{session_id}",
            "customer_id": customer_id  # Extra metadata for filtering
        }
    }

# Customer A
config_a = make_thread_config("customer-001", "session-abc")
graph.invoke({"data": "A's data"}, config_a)

# Customer B (completely isolated)
config_b = make_thread_config("customer-002", "session-xyz")
graph.invoke({"data": "B's data"}, config_b)

# Query by customer (requires custom checkpointer filtering)
# Standard checkpointers don't support querying by custom config fields
```

## Thread Cleanup Strategies

Checkpoints accumulate over time. Implement cleanup strategies to manage storage:

### Time-Based Cleanup

Delete threads older than N days.

```python
from datetime import datetime, timedelta

def cleanup_old_threads(cutoff_days=30):
    """
    Delete checkpoints older than cutoff_days.
    Implementation depends on checkpointer type.
    """
    cutoff = datetime.now() - timedelta(days=cutoff_days)

    # PostgresSaver example (pseudo-code)
    # DELETE FROM checkpoints WHERE created_at < cutoff

    # SqliteSaver example (pseudo-code)
    # Execute SQL: DELETE FROM checkpoints WHERE timestamp < cutoff

    # InMemorySaver example
    # checkpointer.storage = {
    #     k: v for k, v in checkpointer.storage.items()
    #     if parse_timestamp(v.created_at) >= cutoff
    # }
```

### Size-Based Cleanup

Limit total checkpoints per thread (keep latest N).

```python
def trim_thread_history(thread_id: str, keep_latest=50):
    """Keep only the most recent N checkpoints per thread."""
    config = {"configurable": {"thread_id": thread_id}}
    history = list(graph.get_state_history(config))

    if len(history) <= keep_latest:
        return  # Nothing to trim

    # Delete checkpoints beyond keep_latest
    # (Requires checkpointer-specific delete API)
    to_delete = history[keep_latest:]
    for snapshot in to_delete:
        checkpoint_id = snapshot.config['configurable']['checkpoint_id']
        # checkpointer.delete(checkpoint_id)  # Pseudo-code
```

### User-Triggered Cleanup

Allow users to delete their conversation history.

```python
def delete_user_thread(user_id: str, thread_id: str):
    """Delete a specific thread for a user."""
    # Verify user owns this thread (security check)
    if not thread_id.startswith(f"{user_id}_"):
        raise PermissionError("User doesn't own this thread")

    # Delete all checkpoints for thread
    # Implementation depends on checkpointer
    # PostgresSaver: DELETE FROM checkpoints WHERE thread_id = ?
```

### Archival Strategy

Move old threads to cold storage instead of deleting.

```python
def archive_thread(thread_id: str):
    """Move thread to archive (cheaper storage)."""
    # Export thread data
    config = {"configurable": {"thread_id": thread_id}}
    history = list(graph.get_state_history(config))

    # Serialize to JSON
    archived_data = {
        "thread_id": thread_id,
        "archived_at": datetime.now().isoformat(),
        "checkpoints": [
            {
                "checkpoint_id": s.config['configurable']['checkpoint_id'],
                "values": s.values,
                "metadata": s.metadata,
                "created_at": s.created_at
            }
            for s in history
        ]
    }

    # Save to S3, archive DB, etc.
    # save_to_archive_storage(archived_data)

    # Delete from active checkpointer
    # delete_thread(thread_id)
```

## Metadata-Based Filtering

Some checkpointers support filtering by metadata fields (PostgresSaver, custom implementations).

```python
# Filter by step (pseudo-code, checkpointer-dependent)
history = graph.get_state_history(
    config,
    filter={"step": {"$gte": 5}}  # Steps >= 5
)

# Filter by source
execution_only = graph.get_state_history(
    config,
    filter={"source": "loop"}  # Only execution checkpoints
)

# Filter by writes (node execution)
node_a_executions = graph.get_state_history(
    config,
    filter={"writes.node_a": {"$exists": True}}  # When node_a ran
)
```

**Note**: Filtering syntax depends on checkpointer implementation. InMemorySaver and SqliteSaver have limited filtering support.

## Best Practices

1. **Use descriptive thread_ids**: Include context in the ID (user, session, purpose)
2. **Store thread metadata externally**: Map user_id to thread_ids in your application DB
3. **Implement cleanup early**: Don't wait for storage issues - plan retention from day one
4. **Log checkpoint_ids for debugging**: Include in application logs for traceability
5. **Consider checkpoint size**: Large state objects create large checkpoints - optimize state structure
6. **Use metadata for monitoring**: Track `step` counts, `writes` frequency for performance analysis
7. **Isolate by customer**: In multi-tenant apps, ensure thread_ids include customer identifier
8. **Test isolation**: Verify threads don't leak state in concurrent scenarios
