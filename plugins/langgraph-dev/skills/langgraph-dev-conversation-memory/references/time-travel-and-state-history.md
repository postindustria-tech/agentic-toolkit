# Time Travel and State History

## Introduction

Time travel in LangGraph allows you to navigate through the execution history of your graph, inspect past states, and resume execution from any previous checkpoint. This powerful capability enables debugging, exploring alternate paths, and implementing sophisticated recovery strategies.

Unlike traditional debugging where you step through code line by line, LangGraph's time travel operates at the checkpoint level. Each checkpoint represents a snapshot of your graph's state at a specific point in execution. You can:

- **Replay**: Resume from a checkpoint and re-execute subsequent nodes with the same state
- **Branch**: Modify state at a checkpoint and explore alternate execution paths
- **Debug**: Inspect state and metadata at any point in history to diagnose issues
- **Recover**: Continue execution after failures by updating state and resuming

Time travel is built on three fundamental APIs: `get_state()` for inspecting current state, `get_state_history()` for traversing history, and `update_state()` for creating alternate timelines. Understanding how these APIs interact with checkpoints is essential for mastering LangGraph's persistence model.

## StateSnapshot Reference

Every checkpoint is represented as a `StateSnapshot` object, a NamedTuple containing all information about the graph's state at a specific moment. StateSnapshot is the foundation of time travel - it's what you get from `get_state()` and `get_state_history()`.

### StateSnapshot Fields

| Field | Type | Description |
|-------|------|-------------|
| `values` | `dict[str, Any] \| Any` | Current state values. If using TypedDict state, this is a dict. If using custom state classes, it's the state object itself. |
| `next` | `tuple[str, ...]` | Tuple of node names scheduled to execute next. Empty tuple `()` means graph execution is complete. Multiple nodes indicate parallel execution. |
| `config` | `RunnableConfig` | Configuration used to fetch this snapshot. Contains `thread_id`, `checkpoint_id`, and optionally `checkpoint_ns`. This is what you pass to resume execution. |
| `metadata` | `CheckpointMetadata \| None` | Rich metadata about this checkpoint including `step` (execution counter), `writes` (node outputs), `source` ("input" or "loop"), and timestamps. |
| `created_at` | `str \| None` | ISO 8601 timestamp of when this checkpoint was created (e.g., "2024-01-13T15:30:45.123456+00:00"). |
| `parent_config` | `RunnableConfig \| None` | Config of the previous checkpoint in the chain. Use this to traverse history backwards. `None` for the initial checkpoint. |
| `tasks` | `tuple[PregelTask, ...]` | Tuple of tasks scheduled for this step. Contains error information if nodes failed. Each PregelTask has `name`, `error`, and other execution details. |
| `interrupts` | `tuple[Interrupt, ...]` | Tuple of pending human-in-the-loop interrupts. Each Interrupt contains the value from `interrupt()` calls. |

### Accessing StateSnapshot Fields

```python
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.graph import StateGraph, START, END
from typing_extensions import TypedDict

class State(TypedDict):
    count: int
    message: str

# Build simple graph
builder = StateGraph(State)
builder.add_node("increment", lambda s: {"count": s["count"] + 1})
builder.add_node("format", lambda s: {"message": f"Count is {s['count']}"})
builder.add_edge(START, "increment")
builder.add_edge("increment", "format")
builder.add_edge("format", END)

graph = builder.compile(checkpointer=InMemorySaver())

# Execute
config = {"configurable": {"thread_id": "example"}}
result = graph.invoke({"count": 0}, config)

# Inspect StateSnapshot
snapshot = graph.get_state(config)

# Access all fields
print(f"State values: {snapshot.values}")  # {'count': 1, 'message': 'Count is 1'}
print(f"Next nodes: {snapshot.next}")  # () - graph is done
print(f"Thread ID: {snapshot.config['configurable']['thread_id']}")  # 'example'
print(f"Checkpoint ID: {snapshot.config['configurable']['checkpoint_id']}")  # UUID string
print(f"Step: {snapshot.metadata['step']}")  # 2
print(f"Last writes: {snapshot.metadata['writes']}")  # {'format': {'message': '...'}}
print(f"Created: {snapshot.created_at}")  # ISO timestamp

# Traverse to parent
if snapshot.parent_config:
    parent = graph.get_state(snapshot.parent_config)
    print(f"Parent step: {parent.metadata['step']}")  # 1
```

### StateSnapshot Immutability

StateSnapshots are **immutable** - they represent a frozen moment in time. Modifying `snapshot.values` directly has no effect on the graph's state. To change state, use `graph.update_state()`, which creates a **new** checkpoint.

## get_state() API Reference

Retrieve the current or a specific checkpoint for a thread.

### Signature

```python
def get_state(
    config: RunnableConfig,
    *,
    subgraphs: bool = False
) -> StateSnapshot
```

### Parameters

- **config**: `RunnableConfig` - Configuration dict with at minimum:
  - `configurable.thread_id` (required): The thread to query
  - `configurable.checkpoint_id` (optional): Specific checkpoint UUID. If omitted, returns the **latest** checkpoint.
- **subgraphs**: `bool` - Whether to include subgraph snapshots (advanced, default `False`)

### Return Value

Returns a `StateSnapshot` object representing the checkpoint.

### Usage Patterns

#### Get Latest Checkpoint

```python
# Get the most recent checkpoint for a thread
config = {"configurable": {"thread_id": "my-thread"}}
snapshot = graph.get_state(config)

# snapshot contains the final state after last invoke()
```

#### Get Specific Checkpoint

```python
# Get a specific checkpoint by UUID
config = {
    "configurable": {
        "thread_id": "my-thread",
        "checkpoint_id": "1ef663ba-28fe-6528-8002-5a559208592c"
    }
}
snapshot = graph.get_state(config)

# snapshot contains state at that specific checkpoint
```

#### Check if Graph is Done

```python
snapshot = graph.get_state(config)
if not snapshot.next:
    print("Graph execution is complete")
else:
    print(f"Next nodes to execute: {snapshot.next}")
```

## get_state_history() API Reference

Iterate through all checkpoints for a thread in reverse chronological order (newest first).

### Signature

```python
def get_state_history(
    config: RunnableConfig,
    *,
    filter: dict[str, Any] | None = None,
    before: RunnableConfig | None = None,
    limit: int | None = None
) -> Iterator[StateSnapshot]
```

### Parameters

- **config**: `RunnableConfig` - Configuration with `thread_id` (checkpoint_id is ignored)
- **filter**: `dict[str, Any]` - Filter checkpoints by metadata fields (checkpointer-specific)
- **before**: `RunnableConfig` - Return only checkpoints before this config's checkpoint
- **limit**: `int` - Maximum number of checkpoints to return

### Return Value

Returns an `Iterator[StateSnapshot]` yielding checkpoints in **reverse chronological order** (most recent first).

### Usage Patterns

#### Iterate All Checkpoints

```python
config = {"configurable": {"thread_id": "my-thread"}}
history = list(graph.get_state_history(config))

print(f"Total checkpoints: {len(history)}")
for i, snapshot in enumerate(history):
    print(f"{i}: Step {snapshot.metadata['step']}, Created: {snapshot.created_at}")
```

#### Find Checkpoint by Criteria

```python
# Find checkpoint where a specific node executed
history = graph.get_state_history(config)
checkpoint = next(
    (s for s in history if "my_node" in s.metadata.get('writes', {})),
    None
)

# Find checkpoint at specific step
checkpoint_at_step_3 = next(
    (s for s in history if s.metadata['step'] == 3),
    None
)
```

#### Paginate Through History

```python
# Get first 10 checkpoints
config = {"configurable": {"thread_id": "my-thread"}}
page_1 = list(graph.get_state_history(config, limit=10))

# Get next 10 (after the last one from page 1)
page_2 = list(graph.get_state_history(config, before=page_1[-1].config, limit=10))
```

## update_state() API Reference

Create a new checkpoint by updating state at a specific point in time. This is the core API for branching and state modification.

### Signature

```python
def update_state(
    config: RunnableConfig,
    values: dict[str, Any] | Any | None,
    as_node: str | None = None,
    task_id: str | None = None,
) -> RunnableConfig
```

### Parameters

- **config**: `RunnableConfig` - Config of the checkpoint to update (must include `thread_id`, optionally `checkpoint_id`)
- **values**: `dict[str, Any] | Any | None` - New values to merge into state. Follows the same reducer logic as node returns. Use `None` to create checkpoint without state changes.
- **as_node**: `str | None` - Pretend the update came from this node. Affects which edges are followed on next resume. If `None`, defaults to the last node that updated state (if unambiguous).
- **task_id**: `str | None` - Advanced: specific task ID to update (rarely needed)

### Return Value

Returns a new `RunnableConfig` with:
- Same `thread_id` as the input config
- **New** `checkpoint_id` (UUID) for the created checkpoint
- This config can be passed to `invoke()` to resume from the new checkpoint

### Behavior

1. **Creates a new checkpoint** - Does NOT modify the existing checkpoint
2. **Merges values** - Uses state reducers (e.g., `add_messages` for message lists)
3. **Updates `next`** - Based on `as_node` parameter and graph edges
4. **Preserves parent chain** - New checkpoint's `parent_config` points to the original checkpoint

### Usage Patterns

#### Simple State Update

```python
config = {"configurable": {"thread_id": "my-thread"}}

# Update state at latest checkpoint
new_config = graph.update_state(
    config,
    values={"count": 42, "message": "Updated"}
)

print(f"New checkpoint ID: {new_config['configurable']['checkpoint_id']}")

# Resume from updated state
result = graph.invoke(None, new_config)
```

#### Branching from History

```python
# Get checkpoint from history
history = list(graph.get_state_history(config))
old_checkpoint = history[5]  # Some past checkpoint

# Create alternate timeline
new_config = graph.update_state(
    old_checkpoint.config,
    values={"strategy": "alternate"}
)

# Resume from alternate timeline
alternate_result = graph.invoke(None, new_config)

# Original timeline is unchanged
original = graph.get_state(config)
# Still has original strategy
```

#### Using as_node for Edge Control

```python
# Graph has: node_a -> merge, node_b -> merge
# Want to simulate update coming from node_b

new_config = graph.update_state(
    config,
    values={"value": 10},
    as_node="node_b"  # Pretend this came from node_b
)

# When resuming, graph will follow node_b's edges
result = graph.invoke(None, new_config)
```

#### Reducer Behavior

```python
# For MessagesState with add_messages reducer
new_config = graph.update_state(
    config,
    values={"messages": [HumanMessage(content="New message")]}
)

# Message is APPENDED to existing messages (not replaced)
snapshot = graph.get_state(new_config)
# snapshot.values["messages"] contains all old messages + new one
```

## Time Travel Workflow

The canonical workflow for time travel combines all three APIs:

### 1. Run the Graph

```python
config = {"configurable": {"thread_id": "debug-session"}}
result = graph.invoke({"input": "initial data"}, config)
```

### 2. Identify a Checkpoint

```python
# Option A: Get latest
snapshot = graph.get_state(config)

# Option B: Find specific checkpoint in history
history = list(graph.get_state_history(config))

# Find checkpoint before problematic node
checkpoint = next(
    s for s in history
    if s.metadata['step'] == 3 and 'problematic_node' in s.next
)
```

### 3. Update State (Optional)

```python
# Option A: Resume without changes (replay)
resume_config = checkpoint.config

# Option B: Modify state (branch)
resume_config = graph.update_state(
    checkpoint.config,
    values={"debug_mode": True, "data": "fixed"}
)
```

### 4. Resume Execution

```python
# Resume from checkpoint
result = graph.invoke(None, resume_config)

# Pass None as input when resuming from checkpoint
# Graph continues from checkpoint's `next` nodes
```

### Complete Example

```python
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.graph import StateGraph, START, END
from typing_extensions import TypedDict

class State(TypedDict):
    data: list
    step: int

def process_step(state: State):
    return {
        "data": state["data"] + [f"step_{state['step']}"],
        "step": state["step"] + 1
    }

builder = StateGraph(State)
builder.add_node("process", process_step)
builder.add_edge(START, "process")
builder.add_edge("process", "process")  # Loop back

# Compile with conditional to stop at step 3
def should_continue(state: State):
    return "process" if state["step"] < 3 else END

builder.add_conditional_edges("process", should_continue)

graph = builder.compile(checkpointer=InMemorySaver())

# 1. Run graph
config = {"configurable": {"thread_id": "demo"}}
result = graph.invoke({"data": [], "step": 0}, config)
print(f"Final result: {result}")  # data: ['step_0', 'step_1', 'step_2'], step: 3

# 2. Get history
history = list(graph.get_state_history(config))
print(f"Total checkpoints: {len(history)}")

# Find checkpoint after step 1
step_1_checkpoint = next(s for s in history if s.values['step'] == 1)

# 3. Branch: Undo step 2 and 3 by resuming from step 1
resume_config = step_1_checkpoint.config
replayed = graph.invoke(None, resume_config)
print(f"Replayed: {replayed}")  # Same result

# 4. Branch: Modify and explore alternate path
alt_config = graph.update_state(
    step_1_checkpoint.config,
    values={"data": ["step_0", "alternate_step_1"]}  # Different step 1
)
alternate = graph.invoke(None, alt_config)
print(f"Alternate: {alternate}")  # Different result
```

## Best Practices

1. **Always use thread_id**: Never omit thread_id when working with checkpoints
2. **Materialize history carefully**: `list(get_state_history())` loads all checkpoints into memory. Use pagination for long histories.
3. **Use checkpoint_id for precision**: When resuming specific checkpoints, include `checkpoint_id` in config
4. **Understand reducer semantics**: `update_state()` merges values using reducers, not replacement
5. **Check `next` before resuming**: Ensure checkpoint has `next` nodes if you expect execution to continue
6. **Leverage as_node for testing**: Use `as_node` to simulate different execution paths without changing graph structure
7. **Document branching points**: When creating alternate timelines, tag configs for easy identification (e.g., add custom metadata keys)

## Common Pitfalls

- **Forgetting `None` input**: When resuming from checkpoint, pass `None` as input, not the original input
- **Mutating StateSnapshot**: StateSnapshot is immutable. Use `update_state()` to create new checkpoints.
- **Assuming checkpoint_id in history**: `get_state_history()` config should only have `thread_id`, not `checkpoint_id`
- **Confusing parent_config direction**: `parent_config` points to the **previous** checkpoint (backward in time)
- **Over-relying on as_node**: If you need `as_node` frequently, consider redesigning your graph edges
