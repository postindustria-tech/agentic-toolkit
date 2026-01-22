---
name: langgraph-checkpointing-and-persistence
description: This skill should be used when the user asks about "LangGraph memory", "checkpointer", "InMemorySaver", "PostgresSaver", "thread persistence", "conversation history", "add_messages", "MessagesState", "get_state", "get_state_history", "update_state", "StateSnapshot", "time travel", "checkpoint metadata", "fault tolerance", "pending writes", "thread management", or needs guidance on implementing memory, persistence, state inspection, and recovery in LangGraph workflows.
version: 2.0.0
---

# LangGraph Memory and Persistence

LangGraph provides built-in persistence through checkpointers, enabling workflows to maintain state across interactions, support multiple conversation threads, and recover from failures.

## Checkpointer Types

### InMemorySaver - Development/Testing

```python
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.graph import StateGraph, MessagesState, START, END
from langchain_anthropic import ChatAnthropic

# Create checkpointer for in-memory persistence
checkpointer = InMemorySaver()

# Define the graph
model = ChatAnthropic(model="claude-sonnet-4-5-20250929")

def chatbot(state: MessagesState):
    response = model.invoke(state["messages"])
    return {"messages": [response]}

# Build and compile with checkpointer
builder = StateGraph(MessagesState)
builder.add_node("chatbot", chatbot)
builder.add_edge(START, "chatbot")
builder.add_edge("chatbot", END)
graph = builder.compile(checkpointer=checkpointer)

# Use thread_id to maintain conversation context
config = {"configurable": {"thread_id": "user-123"}}

# Conversation turn 1
result = graph.invoke({"messages": [("user", "Hi, I'm Alice")]}, config)

# Conversation turn 2 - remembers context from turn 1
result = graph.invoke({"messages": [("user", "What's my name?")]}, config)
# Response: "Your name is Alice"
```

**Pros**: Zero setup, fast iteration
**Cons**: Data lost on restart - use only for development

### SqliteSaver - Local Persistence

```python
# Requires: pip install langgraph-checkpoint-sqlite
from langgraph.checkpoint.sqlite import SqliteSaver
from langgraph.graph import StateGraph, MessagesState, START, END
from langchain_anthropic import ChatAnthropic

model = ChatAnthropic(model="claude-sonnet-4-5-20250929")

def chatbot(state: MessagesState):
    response = model.invoke(state["messages"])
    return {"messages": [response]}

builder = StateGraph(MessagesState)
builder.add_node("chatbot", chatbot)
builder.add_edge(START, "chatbot")
builder.add_edge("chatbot", END)

# Use context manager for proper connection handling
with SqliteSaver.from_conn_string("checkpoints.sqlite") as checkpointer:
    graph = builder.compile(checkpointer=checkpointer)

    config = {"configurable": {"thread_id": "session-456"}}
    result = graph.invoke({"messages": [("user", "Hello!")]}, config)
```

**Pros**: Persists to file, survives restarts
**Cons**: Single-process only, not for production

### AsyncSqliteSaver - Async Local Persistence

```python
# Requires: pip install langgraph-checkpoint-sqlite
from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver
from langgraph.graph import StateGraph, MessagesState, START, END
from langchain_anthropic import ChatAnthropic

model = ChatAnthropic(model="claude-sonnet-4-5-20250929")

async def chatbot(state: MessagesState):
    response = await model.ainvoke(state["messages"])
    return {"messages": [response]}

builder = StateGraph(MessagesState)
builder.add_node("chatbot", chatbot)
builder.add_edge(START, "chatbot")
builder.add_edge("chatbot", END)

# Async context manager for proper connection handling
async with AsyncSqliteSaver.from_conn_string("checkpoints.sqlite") as checkpointer:
    graph = builder.compile(checkpointer=checkpointer)

    config = {"configurable": {"thread_id": "async-session-456"}}
    result = await graph.ainvoke({"messages": [("user", "Hello!")]}, config)
```

**Pros**: Async SQLite operations, ideal for FastAPI and async frameworks
**Cons**: Requires async context throughout application

### PostgresSaver - Production Persistence

```python
# Requires: pip install langgraph-checkpoint-postgres
from langgraph.checkpoint.postgres import PostgresSaver
from langgraph.graph import StateGraph, MessagesState, START, END
from langchain_anthropic import ChatAnthropic
import logging

logger = logging.getLogger(__name__)
model = ChatAnthropic(model="claude-sonnet-4-5-20250929")

def chatbot(state: MessagesState):
    response = model.invoke(state["messages"])
    return {"messages": [response]}

builder = StateGraph(MessagesState)
builder.add_node("chatbot", chatbot)
builder.add_edge(START, "chatbot")
builder.add_edge("chatbot", END)

# Production: Use PostgresSaver for persistent storage
# SECURITY: In production, use environment variables for credentials
# Example: DB_URI = os.environ.get("DATABASE_URL")
DB_URI = "postgresql://user:password@localhost:5432/mydb?sslmode=disable"

try:
    with PostgresSaver.from_conn_string(DB_URI) as checkpointer:
        checkpointer.setup()  # Required on first use - creates tables
        graph = builder.compile(checkpointer=checkpointer)

        config = {"configurable": {"thread_id": "customer-789"}}
        result = graph.invoke({"messages": [("user", "Hello!")]}, config)
except Exception as e:
    logger.error(f"Database connection failed: {e}")
    raise
```

**Pros**: Production-ready, multi-instance, scalable
**Cons**: Requires PostgreSQL setup

> **Tip**: For better performance, install with binary extras:
> `pip install "langgraph-checkpoint-postgres[binary]"` or `pip install psycopg[binary]`

### AsyncPostgresSaver - Production Async

```python
# Requires: pip install langgraph-checkpoint-postgres
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
from langgraph.graph import StateGraph, MessagesState, START, END
from langchain_anthropic import ChatAnthropic

model = ChatAnthropic(model="claude-sonnet-4-5-20250929")

async def chatbot(state: MessagesState):
    response = await model.ainvoke(state["messages"])
    return {"messages": [response]}

builder = StateGraph(MessagesState)
builder.add_node("chatbot", chatbot)
builder.add_edge(START, "chatbot")
builder.add_edge("chatbot", END)

# Async production usage with PostgreSQL
# SECURITY: In production, use environment variables for credentials
# Example: DB_URI = os.environ.get("DATABASE_URL")
DB_URI = "postgresql://user:password@localhost:5432/mydb?sslmode=disable"

async with AsyncPostgresSaver.from_conn_string(DB_URI) as checkpointer:
    await checkpointer.asetup()  # Required on first use - creates tables
    graph = builder.compile(checkpointer=checkpointer)

    config = {"configurable": {"thread_id": "async-session-123"}}
    result = await graph.ainvoke({"messages": [("user", "Hello!")]}, config)
```

**Pros**: Native async support, non-blocking I/O
**Cons**: Requires async context throughout application

## Managing Long Conversations

### Message Trimming - Token-Efficient History

```python
from langchain_core.messages.utils import trim_messages, count_tokens_approximately
from langgraph.graph import StateGraph, MessagesState, START, END
from langgraph.checkpoint.memory import InMemorySaver
from langchain_anthropic import ChatAnthropic

model = ChatAnthropic(model="claude-sonnet-4-5-20250929")

def chatbot(state: MessagesState):
    # Trim messages to fit context window
    # end_on accepts: str ("human"), type (HumanMessage), or Sequence (["human", "tool"])
    trimmed = trim_messages(
        state["messages"],
        strategy="last",
        token_counter=count_tokens_approximately,
        max_tokens=4000,
        start_on="human",
        end_on=["human", "tool"],  # List of types to end on
    )
    response = model.invoke(trimmed)
    return {"messages": [response]}

builder = StateGraph(MessagesState)
builder.add_node("chatbot", chatbot)
builder.add_edge(START, "chatbot")
builder.add_edge("chatbot", END)

checkpointer = InMemorySaver()
graph = builder.compile(checkpointer=checkpointer)
```

**Pros**: Predictable token usage, keeps recent context
**Cons**: Loses older conversation details

### Conversation Summarization

```python
from typing import Annotated
from typing_extensions import TypedDict
from langgraph.graph import StateGraph, add_messages, START, END
from langgraph.checkpoint.memory import InMemorySaver
from langchain_core.messages import HumanMessage, RemoveMessage
from langchain_anthropic import ChatAnthropic

# Custom state with summary field
class ConversationState(TypedDict):
    messages: Annotated[list, add_messages]
    summary: str  # Access with state.get("summary", "") for safety on first invocation

model = ChatAnthropic(model="claude-sonnet-4-5-20250929")

def chatbot(state: ConversationState):
    # Include summary in system message if available
    messages = state["messages"]
    if state.get("summary"):
        system_msg = f"Summary of earlier conversation: {state['summary']}"
        messages = [{"role": "system", "content": system_msg}] + list(messages)

    response = model.invoke(messages)
    return {"messages": [response]}

def maybe_summarize(state: ConversationState):
    """Summarize when conversation gets long."""
    messages = state["messages"]
    if len(messages) <= 10:
        return {}

    # Generate summary of older messages
    summary_prompt = "Summarize this conversation concisely:"
    summary_request = list(messages) + [HumanMessage(content=summary_prompt)]
    summary = model.invoke(summary_request)

    # Keep only last 2 messages, remove older ones
    delete_messages = [RemoveMessage(id=m.id) for m in messages[:-2]]
    return {"summary": summary.content, "messages": delete_messages}

builder = StateGraph(ConversationState)
builder.add_node("chatbot", chatbot)
builder.add_node("summarize", maybe_summarize)
builder.add_edge(START, "chatbot")
builder.add_edge("chatbot", "summarize")
builder.add_edge("summarize", END)

graph = builder.compile(checkpointer=InMemorySaver())
```

**Pros**: Preserves context across long conversations
**Cons**: Summary generation adds latency and cost

## State Definition Patterns

### Using MessagesState (Prebuilt)

```python
from langgraph.graph import MessagesState, StateGraph

# MessagesState provides: messages: Annotated[list, add_messages]
builder = StateGraph(MessagesState)
```

### Extending MessagesState

```python
from langgraph.graph import MessagesState

class ExtendedState(MessagesState):
    # Inherits messages key with add_messages reducer
    user_name: str
    preferences: dict
```

### Custom State with add_messages

```python
from typing import Annotated
from typing_extensions import TypedDict
from langgraph.graph import add_messages

class CustomState(TypedDict):
    messages: Annotated[list, add_messages]
    context: str
    turn_count: int
```

## Checkpointer Comparison

| Checkpointer | Use Case | Persistence | Installation |
|--------------|----------|-------------|--------------|
| InMemorySaver | Development, testing | In-memory (lost on restart) | Included in `langgraph` |
| SqliteSaver | Local apps, prototypes (sync) | File-based | `pip install langgraph-checkpoint-sqlite` |
| AsyncSqliteSaver | Local apps, prototypes (async) | File-based | `pip install langgraph-checkpoint-sqlite` |
| PostgresSaver | Production (sync) | Database | `pip install langgraph-checkpoint-postgres` |
| AsyncPostgresSaver | Production (async) | Database | `pip install langgraph-checkpoint-postgres` |

## Memory Strategy Comparison

| Strategy | Token Efficiency | Context Preserved | When to Use |
|----------|------------------|-------------------|-------------|
| Full History | Low | 100% | Short conversations (<10 turns) |
| trim_messages | High | Recent only | Long conversations |
| Summarization | Medium | Condensed | Multi-session apps |

## Best Practices

1. **Use InMemorySaver for development** - Fast iteration, no setup required
2. **Use PostgresSaver for production** - Persistent, scalable, supports multiple instances
3. **Always use thread_id** - Isolate conversations per user/session
4. **Use add_messages reducer** - Handles message ID deduplication automatically
5. **Trim or summarize long conversations** - Prevent context window overflow
6. **Call setup() on database checkpointers** - Creates required tables on first use
7. **Use context managers** - Ensures proper connection cleanup for file/database checkpointers

## Thread Configuration

```python
# Basic thread configuration
config = {"configurable": {"thread_id": "conversation-1"}}

# With user isolation for cross-thread memory
config = {
    "configurable": {
        "thread_id": "session-abc",
        "user_id": "user-123"
    }
}

# Customer support example
customer_config = {
    "configurable": {
        "thread_id": f"customer_{customer_id}_session_{session_id}"
    }
}
```

## State Inspection APIs

### Get Current State

Use `graph.get_state(config)` to retrieve the current checkpoint for a thread. This returns a `StateSnapshot` object containing all checkpoint data.

```python
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.graph import StateGraph, START, END
from typing_extensions import TypedDict

class State(TypedDict):
    count: int
    result: str

def increment(state: State):
    return {"count": state["count"] + 1}

def process(state: State):
    return {"result": f"Final count: {state['count']}"}

builder = StateGraph(State)
builder.add_node("increment", increment)
builder.add_node("process", process)
builder.add_edge(START, "increment")
builder.add_edge("increment", "process")
builder.add_edge("process", END)

checkpointer = InMemorySaver()
graph = builder.compile(checkpointer=checkpointer)

# Execute graph
config = {"configurable": {"thread_id": "thread-1"}}
result = graph.invoke({"count": 0}, config)

# Get current state
snapshot = graph.get_state(config)

print(f"Values: {snapshot.values}")  # Current state values
print(f"Next nodes: {snapshot.next}")  # Nodes to execute next (empty tuple if done)
print(f"Config: {snapshot.config['configurable']}")  # Config with thread_id and checkpoint_id
print(f"Metadata: {snapshot.metadata}")  # step, writes, source
print(f"Created: {snapshot.created_at}")  # ISO timestamp
print(f"Parent config: {snapshot.parent_config}")  # Previous checkpoint config
```

**StateSnapshot Fields**:
- `values`: Current state values (dict or custom state object)
- `next`: Tuple of node names to execute next (empty if graph completed)
- `config`: RunnableConfig with `thread_id` and `checkpoint_id`
- `metadata`: CheckpointMetadata (step, writes, source)
- `created_at`: ISO timestamp of checkpoint creation
- `parent_config`: Config of previous checkpoint (for traversing history)
- `tasks`: Tuple of PregelTask objects (pending or failed tasks)
- `interrupts`: Tuple of Interrupt objects (pending human-in-the-loop interrupts)

### Get State History

Use `graph.get_state_history(config)` to iterate through all checkpoints for a thread in reverse chronological order (most recent first).

```python
# Execute graph multiple times to create history
config = {"configurable": {"thread_id": "thread-2"}}
graph.invoke({"count": 0}, config)
graph.invoke({"count": 5}, config)
graph.invoke({"count": 10}, config)

# Get full history
history = list(graph.get_state_history(config))

print(f"Total checkpoints: {len(history)}")

for i, snapshot in enumerate(history):
    print(f"\nCheckpoint {i + 1}:")
    print(f"  Checkpoint ID: {snapshot.config['configurable']['checkpoint_id']}")
    print(f"  Step: {snapshot.metadata['step']}")
    print(f"  Values: {snapshot.values}")
    print(f"  Created: {snapshot.created_at}")

# Access specific checkpoint by index
most_recent = history[0]
oldest = history[-1]

# Find checkpoint at specific step
step_1_checkpoint = next(s for s in history if s.metadata['step'] == 1)
```

**History Ordering**: Checkpoints are returned in **reverse chronological order** (newest first). Use `list()` to materialize the full iterator.

## Time Travel

Time travel allows you to resume graph execution from any previous checkpoint, either replaying the same state or modifying it to explore alternate paths.

### Replay from Checkpoint

Resume execution from a previous checkpoint without modifications:

```python
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.graph import StateGraph, START, END
from typing_extensions import TypedDict

class State(TypedDict):
    input: str
    step1_result: str
    step2_result: str
    final_result: str

def step1(state: State):
    return {"step1_result": f"Processed: {state['input']}"}

def step2(state: State):
    return {"step2_result": f"Enhanced: {state['step1_result']}"}

def finalize(state: State):
    return {"final_result": f"Final: {state['step2_result']}"}

builder = StateGraph(State)
builder.add_node("step1", step1)
builder.add_node("step2", step2)
builder.add_node("finalize", finalize)
builder.add_edge(START, "step1")
builder.add_edge("step1", "step2")
builder.add_edge("step2", "finalize")
builder.add_edge("finalize", END)

checkpointer = InMemorySaver()
graph = builder.compile(checkpointer=checkpointer)

# Initial execution
config = {"configurable": {"thread_id": "replay-demo"}}
result = graph.invoke({"input": "hello"}, config)
print(f"Initial result: {result['final_result']}")

# Get checkpoint after step1
history = list(graph.get_state_history(config))
step1_checkpoint = next(s for s in history if 'step1' in str(s.next))

# Resume from step1 checkpoint (will re-execute step2 and finalize)
replay_config = step1_checkpoint.config
result = graph.invoke(None, replay_config)  # None = resume from checkpoint
print(f"Replayed result: {result['final_result']}")
```

**Key Points**:
- Pass `None` as input when resuming from a checkpoint
- The graph resumes from the `next` node(s) in the checkpoint
- Nodes re-execute with the same state (deterministic if no randomness)

### Branch with update_state()

Create alternate execution paths by modifying state at a checkpoint:

```python
# Get checkpoint after step1
history = list(graph.get_state_history(config))
step1_checkpoint = next(s for s in history if s.metadata['step'] == 1)

# Fork the state by updating it
new_config = graph.update_state(
    step1_checkpoint.config,
    values={"input": "goodbye"}  # Change the original input
)

print(f"Original checkpoint ID: {step1_checkpoint.config['configurable']['checkpoint_id']}")
print(f"New checkpoint ID: {new_config['configurable']['checkpoint_id']}")

# Resume from the forked checkpoint
forked_result = graph.invoke(None, new_config)
print(f"Forked result: {forked_result['final_result']}")

# Original execution is unchanged
original_state = graph.get_state(config)
print(f"Original still has: {original_state.values['input']}")
```

**Branching Behavior**:
- `update_state()` creates a **new checkpoint** with a new `checkpoint_id`
- The new checkpoint shares the same `thread_id` but has different history
- Original checkpoint chain remains unchanged (immutable history)
- You now have two divergent paths from the same thread

### Advanced: update_state() with as_node

Control which node the update "comes from" to influence the next node selection:

```python
from langgraph.graph import StateGraph, START, END
from typing_extensions import TypedDict
from langgraph.checkpoint.memory import InMemorySaver

class State(TypedDict):
    value: int
    path: str

def node_a(state: State):
    return {"value": state["value"] + 1, "path": "a"}

def node_b(state: State):
    return {"value": state["value"] + 10, "path": "b"}

def merge(state: State):
    return {"path": state["path"] + "->merge"}

builder = StateGraph(State)
builder.add_node("node_a", node_a)
builder.add_node("node_b", node_b)
builder.add_node("merge", merge)
builder.add_edge(START, "node_a")
builder.add_edge("node_a", "merge")  # a goes to merge
builder.add_edge("node_b", "merge")  # b goes to merge
builder.add_edge("merge", END)

graph = builder.compile(checkpointer=InMemorySaver())

# Execute normally
config = {"configurable": {"thread_id": "as-node-demo"}}
result = graph.invoke({"value": 0}, config)
print(f"Normal path: {result}")  # value=1, path="a->merge"

# Get checkpoint before merge
history = list(graph.get_state_history(config))
before_merge = next(s for s in history if "merge" in s.next)

# Update state AS IF it came from node_b instead
new_config = graph.update_state(
    before_merge.config,
    values={"value": 10, "path": "b"},
    as_node="node_b"  # Pretend this update came from node_b
)

# Resume - will follow node_b -> merge path
alt_result = graph.invoke(None, new_config)
print(f"Alternate path: {alt_result}")  # value=10, path="b->merge"
```

**as_node Parameter**:
- Specifies which node the update is "coming from"
- Affects which edges are followed next
- Useful for testing alternate paths through the graph
- If omitted, defaults to the last node that updated state (if unambiguous)

## Checkpoint Metadata

Every checkpoint includes rich metadata for debugging and monitoring:

```python
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.graph import StateGraph, START, END
from typing_extensions import TypedDict

class State(TypedDict):
    data: str

def process_a(state: State):
    return {"data": state["data"] + "->a"}

def process_b(state: State):
    return {"data": state["data"] + "->b"}

builder = StateGraph(State)
builder.add_node("process_a", process_a)
builder.add_node("process_b", process_b)
builder.add_edge(START, "process_a")
builder.add_edge("process_a", "process_b")
builder.add_edge("process_b", END)

graph = builder.compile(checkpointer=InMemorySaver())

config = {"configurable": {"thread_id": "metadata-demo"}}
result = graph.invoke({"data": "start"}, config)

# Inspect checkpoint metadata
snapshot = graph.get_state(config)
metadata = snapshot.metadata

print(f"Step: {metadata['step']}")  # Execution step number (0, 1, 2, ...)
print(f"Source: {metadata['source']}")  # "input" or "loop"
print(f"Writes: {metadata['writes']}")  # Dict of {node_name: output_value}

# Checkpoint IDs
config_info = snapshot.config['configurable']
print(f"Thread ID: {config_info['thread_id']}")
print(f"Checkpoint ID: {config_info['checkpoint_id']}")  # UUID
print(f"Checkpoint NS: {config_info.get('checkpoint_ns', '')}")  # Namespace for subgraphs

# Parent relationship
if snapshot.parent_config:
    parent_id = snapshot.parent_config['configurable']['checkpoint_id']
    print(f"Parent checkpoint: {parent_id}")
```

**Metadata Fields**:
- `step`: Integer counter of execution progress (0 = initial, 1+ = after each superstep)
- `source`: `"input"` (from user input) or `"loop"` (from graph execution)
- `writes`: Dictionary mapping node names to their output values for this step
- `checkpoint_id`: Unique UUID for this checkpoint
- `checkpoint_ns`: Namespace string (used for subgraphs)
- `parent_config`: Config of previous checkpoint (forms linked list of history)

## Fault Tolerance & Recovery

LangGraph automatically preserves state when nodes fail, enabling recovery without re-executing successful work.

### Pending Writes

When a node fails mid-execution during a superstep, LangGraph stores the outputs from other nodes that completed successfully:

```python
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.graph import StateGraph, START, END
from typing_extensions import TypedDict

class State(TypedDict):
    values: list

def task_a(state: State):
    return {"values": state["values"] + ["a"]}

def task_b(state: State):
    return {"values": state["values"] + ["b"]}

def task_c(state: State):
    # Simulate failure
    raise ValueError("task_c failed!")

def aggregate(state: State):
    return {"values": state["values"] + ["aggregated"]}

builder = StateGraph(State)
builder.add_node("task_a", task_a)
builder.add_node("task_b", task_b)
builder.add_node("task_c", task_c)
builder.add_node("aggregate", aggregate)
builder.add_edge(START, "task_a")
builder.add_edge(START, "task_b")
builder.add_edge(START, "task_c")
builder.add_edge("task_a", "aggregate")
builder.add_edge("task_b", "aggregate")
builder.add_edge("task_c", "aggregate")
builder.add_edge("aggregate", END)

graph = builder.compile(checkpointer=InMemorySaver())

config = {"configurable": {"thread_id": "fault-demo"}}

try:
    result = graph.invoke({"values": []}, config)
except ValueError as e:
    print(f"Execution failed: {e}")

    # Get state after failure
    snapshot = graph.get_state(config)

    # Check pending writes from successful nodes
    print(f"Pending writes: {snapshot.metadata.get('writes', {})}")
    # Will show: {'task_a': {'values': ['a']}, 'task_b': {'values': ['b']}}

    # task_a and task_b completed successfully
    # Their outputs are preserved in the checkpoint
    # Only task_c needs to be retried
```

### Recovering from Failures

Resume execution after fixing the issue:

```python
# Fix the state to work around the failure
fixed_config = graph.update_state(
    config,
    values={"values": ["a", "b", "c"]},  # Manually provide task_c's output
    as_node="task_c"  # Pretend this came from task_c
)

# Resume execution - will skip task_a and task_b (already completed)
result = graph.invoke(None, fixed_config)
print(f"Recovered result: {result}")  # ['a', 'b', 'c', 'aggregated']
```

**Recovery Benefits**:
- Failed execution creates a checkpoint with partial progress
- Successful node outputs are preserved (no re-execution needed)
- Update state to fix the issue and resume
- Graph automatically deduplicates work (won't re-run successful nodes)

## Thread Management Patterns

### Multi-Thread Isolation

Each unique `thread_id` creates a completely isolated execution context. Use this for managing multiple concurrent conversations or sessions:

```python
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.graph import StateGraph, MessagesState, START, END
from langchain_anthropic import ChatAnthropic

model = ChatAnthropic(model="claude-sonnet-4-5-20250929")

def chatbot(state: MessagesState):
    response = model.invoke(state["messages"])
    return {"messages": [response]}

builder = StateGraph(MessagesState)
builder.add_node("chatbot", chatbot)
builder.add_edge(START, "chatbot")
builder.add_edge("chatbot", END)

checkpointer = InMemorySaver()
graph = builder.compile(checkpointer=checkpointer)

# Customer A's conversation
config_a = {"configurable": {"thread_id": "customer-alice"}}
graph.invoke({"messages": [("user", "Hi, I'm Alice")]}, config_a)
graph.invoke({"messages": [("user", "What's my name?")]}, config_a)

# Customer B's conversation (completely separate)
config_b = {"configurable": {"thread_id": "customer-bob"}}
graph.invoke({"messages": [("user", "Hi, I'm Bob")]}, config_b)
graph.invoke({"messages": [("user", "What's my name?")]}, config_b)

# Each thread maintains independent state
state_a = graph.get_state(config_a)
state_b = graph.get_state(config_b)

print(f"Thread A knows: Alice")  # Remembers Alice
print(f"Thread B knows: Bob")    # Remembers Bob (no cross-contamination)
```

**Isolation Guarantees**:
- Threads with different `thread_id` values have completely separate state
- State updates in one thread do not affect other threads
- Each thread has its own independent checkpoint history

### Multi-Session Per User

Create multiple conversation threads for a single user:

```python
import uuid

user_id = "user-123"

# User starts a new conversation about topic A
thread_a = f"{user_id}_conversation_{uuid.uuid4()}"
config_a = {"configurable": {"thread_id": thread_a, "user_id": user_id}}
graph.invoke({"messages": [("user", "Tell me about Python")]}, config_a)

# User starts another conversation about topic B (separate thread)
thread_b = f"{user_id}_conversation_{uuid.uuid4()}"
config_b = {"configurable": {"thread_id": thread_b, "user_id": user_id}}
graph.invoke({"messages": [("user", "Tell me about JavaScript")]}, config_b)

# User can continue either conversation independently
graph.invoke({"messages": [("user", "More details please")]}, config_a)  # About Python
graph.invoke({"messages": [("user", "What about TypeScript?")]}, config_b)  # About JS

# Query all threads for this user (if using cross-thread memory)
# Note: Requires custom checkpointer with user_id indexing
```

**Naming Conventions**:
- `f"{user_id}_session_{session_id}"` - Multiple sessions per user
- `f"customer_{customer_id}_{timestamp}"` - Customer support tickets
- `f"project_{project_id}_branch_{branch_name}"` - Collaborative workflows

### Thread Lifecycle Management

**Creating Threads**: Threads are created automatically on first `invoke()` with a new `thread_id`

**Querying Threads**: Use checkpointer-specific APIs to list threads (depends on checkpointer implementation)

**Cleanup Strategies**:
- Time-based: Delete threads older than N days
- Size-based: Limit total checkpoints per thread
- User-triggered: Allow users to delete conversation history
- Archival: Move old threads to cold storage

```python
# Example: Cleanup old checkpoints (manual implementation)
from datetime import datetime, timedelta

def cleanup_old_threads(checkpointer, days=30):
    """Pseudo-code for thread cleanup."""
    cutoff = datetime.now() - timedelta(days=days)

    # Implementation depends on checkpointer type
    # PostgresSaver: DELETE FROM checkpoints WHERE created_at < cutoff
    # SqliteSaver: Similar SQL query
    # InMemorySaver: Clear in-memory store
    pass
```

## Advanced Patterns

### Time-Travel Debugging

Reproduce and debug failed executions by replaying from checkpoints:

```python
# After a failure, examine full history
config = {"configurable": {"thread_id": "debug-session"}}
history = list(graph.get_state_history(config))

# Find the failing checkpoint
for snapshot in history:
    if snapshot.tasks:  # tasks contain error information
        for task in snapshot.tasks:
            if task.error:
                print(f"Error in {task.name}: {task.error}")
                print(f"State at failure: {snapshot.values}")

# Replay from before failure with modified state
previous_checkpoint = history[1]  # Checkpoint before failure
fixed_config = graph.update_state(
    previous_checkpoint.config,
    values={"fixed": True}  # Add debug flag or fix
)
result = graph.invoke(None, fixed_config)
```

### A/B Testing Alternate Paths

Branch from a checkpoint to explore different decisions:

```python
# Execute path A
config_a = {"configurable": {"thread_id": "ab-test", "run": "a"}}
result_a = graph.invoke({"strategy": "aggressive"}, config_a)

# Branch from same starting point with different strategy
history = list(graph.get_state_history(config_a))
initial_state = history[-1]  # Earliest checkpoint

config_b = graph.update_state(
    initial_state.config,
    values={"strategy": "conservative"}
)
config_b["configurable"]["run"] = "b"  # Tag for identification
result_b = graph.invoke(None, config_b)

# Compare outcomes
print(f"Strategy A result: {result_a}")
print(f"Strategy B result: {result_b}")
```

### Rollback to Previous State

Undo recent execution by resuming from an earlier checkpoint:

```python
# Get state before last action
history = list(graph.get_state_history(config))
before_last_action = history[1]  # Second most recent

# Continue from that point
rollback_config = before_last_action.config
result = graph.invoke({"new": "action"}, rollback_config)
```

## Documentation References

- [LangGraph Memory](https://docs.langchain.com/oss/python/langgraph/add-memory) - Official memory, persistence, and thread configuration guide
- [Checkpointing API](https://reference.langchain.com/python/langgraph/checkpoints/) - Checkpointer class reference
- [StateSnapshot Reference](https://langchain-ai.github.io/langgraph/reference/types/#langgraph.types.StateSnapshot) - Complete StateSnapshot field documentation
- [Time Travel Guide](https://langchain-ai.github.io/langgraph/how-tos/human_in_the_loop/time-travel/) - Official time travel how-to
- [Persistence Concepts](https://langchain-ai.github.io/langgraph/concepts/persistence/) - Conceptual overview of checkpointing
- [Messages Reference](https://reference.langchain.com/python/langchain/messages/) - Message trimming and utilities
- [langgraph-checkpoint](https://pypi.org/project/langgraph-checkpoint/) - PyPI package
- [langgraph-checkpoint-sqlite](https://pypi.org/project/langgraph-checkpoint-sqlite/) - SQLite checkpointer
- [langgraph-checkpoint-postgres](https://pypi.org/project/langgraph-checkpoint-postgres/) - PostgreSQL checkpointer
