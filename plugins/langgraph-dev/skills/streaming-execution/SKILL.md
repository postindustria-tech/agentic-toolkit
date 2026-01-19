---
name: streaming-execution-in-langgraph
description: This skill should be used when the user asks about "stream events", "astream_events", "token streaming", "monitor execution", "streaming workflow", "graph.stream()", "real-time updates", "event streaming", "stream modes", "StreamWriter", "custom streaming", or needs guidance on streaming LangGraph workflow execution and real-time token output.
version: 0.5.0
---

# Streaming Execution in LangGraph

## Purpose

Streaming execution enables real-time monitoring of LangGraph workflows by yielding incremental state updates as nodes execute, rather than waiting for complete workflow termination.

## When to Use

- Monitor long-running workflows in real-time
- Provide progressive feedback to users
- Debug workflow execution step-by-step
- Build responsive UI applications
- Stream partial results as they're available
- Display LLM tokens as they're generated

## Core Pattern

```python
# Instead of app.invoke() which blocks until complete
for event in app.stream(initial_state):
    # Process each state update as it occurs
    print(event)
```

## Event Structure

Each event is a dictionary mapping node names to their state updates:

```python
for event in app.stream(initial_state):
    for node_name, state_update in event.items():
        print(f"Node '{node_name}' updated: {state_update}")
```

## Basic Example

```python
from langgraph.graph import StateGraph, START, END
from typing import TypedDict

class State(TypedDict):
    messages: list
    step: str

def greet_func(state: State) -> dict:
    return {"messages": state["messages"] + ["Hello!"], "step": "process"}

def process_func(state: State) -> dict:
    return {"messages": state["messages"] + ["Processed."], "step": "done"}

workflow = StateGraph(State)
workflow.add_node("greet", greet_func)
workflow.add_node("process", process_func)
workflow.add_edge(START, "greet")
workflow.add_edge("greet", "process")
workflow.add_edge("process", END)

app = workflow.compile()

# Stream execution
for event in app.stream({"messages": [], "step": ""}):
    print(f"Event: {event}")
```

Output:
```
Event: {'greet': {'messages': ['Hello!'], 'step': 'process'}}
Event: {'process': {'messages': ['Hello!', 'Processed.'], 'step': 'done'}}
```

**Note:** This output format is specific to `stream_mode="updates"` (the default). Use `stream_mode="values"` to receive complete state snapshots instead.

## Extracting Messages

```python
for event in app.stream(initial_state):
    for output in event.values():
        if "messages" in output:
            for message in output["messages"]:
                # Handle dict-style messages (e.g., OpenAI format)
                if isinstance(message, dict):
                    if message.get("role") == "assistant":
                        print(f"Assistant: {message['content']}")
                    elif message.get("role") == "human":
                        print(f"Human: {message['content']}")
```

**Note:** The example above handles raw dictionary messages. Production applications typically use LangChain message types, which require different attribute access:

```python
from langchain_core.messages import HumanMessage, AIMessage

for event in app.stream(initial_state):
    for output in event.values():
        if "messages" in output:
            for message in output["messages"]:
                if isinstance(message, AIMessage):
                    print(f"Assistant: {message.content}")
```

## Async Streaming

Use `astream()` for async workflows, especially with async frameworks like FastAPI:

### Basic Pattern

```python
async for event in app.astream(initial_state):
    await process_event(event)
```

### FastAPI Integration

```python
from fastapi import FastAPI
from fastapi.responses import StreamingResponse
import json

api = FastAPI()

@api.post("/stream")
async def stream_response(query: str):
    async def generate():
        async for event in graph.astream({"query": query}):
            for node_name, updates in event.items():
                yield f"data: {json.dumps({'node': node_name, 'updates': updates})}\n\n"

    return StreamingResponse(generate(), media_type="text/event-stream")
```

### When to Use Async

- **Use `astream()`**: Async web frameworks, concurrent I/O operations, async node functions
- **Use `stream()`**: Simple scripts, synchronous codebases, blocking I/O

## Token Streaming with astream_events()

For real-time token-by-token streaming from LLM nodes, use `astream_events()`:

### Basic Pattern

```python
async for event in app.astream_events(initial_state, version="v2"):
    if event["event"] == "on_chat_model_stream":
        content = event["data"]["chunk"].content
        if content:
            print(content, end="", flush=True)
```

### Event Types

| Event | Description |
|-------|-------------|
| `on_chat_model_start` | LLM call initiated |
| `on_chat_model_stream` | Token received from LLM |
| `on_chat_model_end` | LLM call completed |
| `on_tool_start` | Tool execution started |
| `on_tool_end` | Tool execution completed |
| `on_chain_start` | Chain/graph execution started |
| `on_chain_end` | Chain/graph execution completed |
| `on_retriever_start` | Retriever query started |
| `on_retriever_end` | Retriever query completed |

### Version Parameter

Always use `version="v2"` for consistent event structure. Version v1 was deprecated in LangChain 0.2.x and removed in 0.4.0.

### LLM Streaming Configuration

For token streaming to work with `astream_events()`, your LLM must be constructed with streaming enabled:

```python
from langchain_anthropic import ChatAnthropic

# streaming=True is required for token streaming
llm = ChatAnthropic(model="claude-sonnet-4-5-20250929", streaming=True)
```

**Note:** Not all chat model integrations support the `streaming` parameter. If your model does not support it, use `disable_streaming=True` to bypass streaming gracefully.

### Complete Example

```python
import asyncio
from langgraph.graph import StateGraph, START, END
from langchain_anthropic import ChatAnthropic
from typing import TypedDict

class State(TypedDict):
    messages: list

# Create LLM with streaming enabled
llm = ChatAnthropic(model="claude-sonnet-4-5-20250929", streaming=True)

def chat_node(state: State) -> dict:
    response = llm.invoke(state["messages"])
    return {"messages": state["messages"] + [response]}

# Build graph
workflow = StateGraph(State)
workflow.add_node("chat", chat_node)
workflow.add_edge(START, "chat")
workflow.add_edge("chat", END)
app = workflow.compile()

async def stream_tokens(query: str):
    initial_state = {"messages": [{"role": "user", "content": query}]}

    async for event in app.astream_events(initial_state, version="v2"):
        kind = event["event"]

        if kind == "on_chat_model_stream":
            content = event["data"]["chunk"].content
            if content:
                print(content, end="", flush=True)
        elif kind == "on_tool_start":
            print(f"\nStarting tool: {event['name']}")
        elif kind == "on_tool_end":
            print(f"\nTool completed: {event['name']}")

# Usage: asyncio.run(stream_tokens("Hello, how are you?"))
```

## Stream Modes

LangGraph provides seven streaming modes for different use cases.

### Updates Mode (Default)

Yields state updates from each node:

```python
# Yields state updates from each node
for event in app.stream(state):
    pass  # event = {'node_name': state_update_dict}
```

### Values Mode: Full State

Yields complete state after each node:

```python
# Yields complete state after each node
for state in app.stream(initial_state, stream_mode="values"):
    print(state)  # Complete state snapshot
```

### Messages Mode: Token Streaming

Streams LLM tokens as 2-tuples (message, metadata):

```python
async for msg, metadata in app.astream(
    initial_state,
    stream_mode="messages"
):
    if msg.content:
        print(msg.content, end="", flush=True)
```

Filter by node using metadata:

```python
async for msg, metadata in app.astream(initial_state, stream_mode="messages"):
    if metadata.get("langgraph_node") == "agent":
        print(msg.content, end="")
```

**Note:** Token-level streaming requires LLM provider support. Ensure your model supports streaming.

### Choosing Between Token Streaming Methods

LangGraph provides two approaches for token streaming. Choose based on your use case:

| Approach | Best For | Key Features |
|----------|----------|--------------|
| `stream_mode="messages"` | Chat applications | Native LangGraph API, 2-tuples (message, metadata), simpler integration |
| `astream_events()` | Fine-grained monitoring | Broader event types (tools, retrievers, chains), detailed lifecycle events |

**Use `stream_mode="messages"` when:**
- Building chat-style applications with a `messages` key in state
- You want a simpler API with message/metadata tuples
- You only need to stream LLM token output

**Use `astream_events()` when:**
- You need to monitor tool execution, retriever calls, or chain events
- Building debugging or analytics dashboards
- Migrating from LangChain and need familiar event patterns
- You require fine-grained control over all execution lifecycle events

### Debug Mode: Full Execution Trace

Streams detailed execution information including node entry/exit, state before/after, tool inputs/outputs, and errors:

```python
for chunk in app.stream(initial_state, stream_mode="debug"):
    print(f"Debug: {chunk}")
```

Debug mode events include:
- `type`: Event type (e.g., "task", "checkpoint")
- `timestamp`: When the event occurred
- `payload`: Detailed execution data including state and results

Use debug mode when you need to:
- Troubleshoot workflow issues during development
- Understand execution flow and timing
- Inspect state transformations at each step
- Track down unexpected routing behavior

**Note:** Debug mode generates verbose output and is not recommended for production UIs. It is invaluable during development and testing.

### Checkpoints Mode: Checkpoint Events

Emits checkpoint creation events in the same format as `get_state()`:

```python
# Requires a checkpointer to be configured
from langgraph.checkpoint.memory import MemorySaver

checkpointer = MemorySaver()
app = workflow.compile(checkpointer=checkpointer)
config = {"configurable": {"thread_id": "1"}}

for chunk in app.stream(initial_state, config, stream_mode="checkpoints"):
    print(f"Checkpoint: {chunk}")
```

Use checkpoints mode when you need to:
- Debug state persistence issues
- Monitor checkpoint creation timing
- Integrate with human-in-the-loop workflows
- Verify checkpointer behavior

### Tasks Mode: Task Lifecycle Events

Emits events when tasks start and finish, including their results and errors:

```python
for chunk in app.stream(initial_state, stream_mode="tasks"):
    print(f"Task event: {chunk}")
```

Use tasks mode when you need to:
- Track individual task execution
- Monitor task completion and errors
- Debug parallel execution flows
- Measure task timing and performance

### Custom Mode: User-Defined Data

Emit custom events using `StreamWriter`:

```python
from langgraph.config import get_stream_writer
from langgraph.graph import StateGraph, START, END
from typing import TypedDict

class State(TypedDict):
    query: str
    result: str

def process_node(state: State) -> dict:
    writer = get_stream_writer()
    writer({"status": "processing", "progress": 50})
    # ... processing logic
    writer({"status": "complete", "progress": 100})
    return {"result": "Done"}

workflow = StateGraph(State)
workflow.add_node("process", process_node)
workflow.add_edge(START, "process")
workflow.add_edge("process", END)
app = workflow.compile()

# Consume custom events
for chunk in app.stream({"query": "test", "result": ""}, stream_mode="custom"):
    print(chunk)  # {"status": "processing", "progress": 50}
```

**Python < 3.11 Limitations:** In Python versions before 3.11, asyncio tasks do not support the `context` parameter, which limits LangGraph's automatic context propagation. This affects streaming in two ways:

1. You cannot use `get_stream_writer()` in async nodes - use parameter injection instead
2. You must explicitly pass `RunnableConfig` into async LLM calls

```python
from langgraph.types import StreamWriter
from langchain_core.runnables import RunnableConfig

# Parameter injection for StreamWriter (Python < 3.11)
async def process_node(state: State, writer: StreamWriter) -> dict:
    writer({"status": "processing"})
    return {"result": "Done"}

# Explicit config passing for LLM calls (Python < 3.11)
async def llm_node(state: State, config: RunnableConfig) -> dict:
    response = await llm.ainvoke(state["messages"], config=config)
    return {"messages": [response]}
```

## Combining Stream Modes

Combine multiple modes for rich streaming experiences:

```python
async for mode, chunk in app.astream(
    initial_state,
    stream_mode=["messages", "updates"]
):
    if mode == "messages":
        msg, metadata = chunk
        if msg.content:
            print(msg.content, end="")  # Token streaming
    elif mode == "updates":
        print(f"\nState update: {chunk}")  # Node completion
```

Common combinations:

| Combination | Use Case |
|-------------|----------|
| `["messages", "updates"]` | Token streaming with node progress |
| `["custom", "updates"]` | Custom events with state changes |
| `["debug", "values"]` | Detailed traces with full state snapshots |

## Monitoring Patterns

### Progress Tracking

```python
from typing import Any

expected_nodes: set[str] = {"greet", "process", "respond", "finalize", "cleanup"}
completed_nodes: set[str] = set()

for event in app.stream(initial_state):
    for node_name in event.keys():
        completed_nodes.add(node_name)
    print(f"Progress: {len(completed_nodes)}/{len(expected_nodes)} nodes complete")
```

### Error Detection

Error keys are application-specific, not built-in LangGraph behavior. You must explicitly include error handling in your state and node logic:

```python
from typing import Any

for event in app.stream(initial_state):
    for node_name, updates in event.items():
        if "error" in updates:  # Requires error field in your State
            print(f"Error in {node_name}: {updates['error']}")
            break

# For exception handling, use try-except around the stream:
def process_event(event: dict[str, Any]) -> None:
    """Process a single stream event."""
    for node_name, updates in event.items():
        print(f"{node_name}: {updates}")

try:
    for event in app.stream(initial_state):
        process_event(event)
except Exception as e:
    print(f"Workflow error: {e}")
```

### Conditional Processing

```python
from typing import Any

async def notify_user(updates: dict[str, Any]) -> None:
    """Notify user of critical node updates."""
    print(f"Critical update: {updates}")

async for event in app.astream(initial_state):
    for node_name, updates in event.items():
        if node_name == "critical_node":
            # Special handling for specific nodes
            await notify_user(updates)
```

## Best Practices

1. **Process events incrementally** - Don't accumulate all events in memory
2. **Handle partial state** - Events contain updates, not full state (use `stream_mode="values"` for complete state)
3. **Check event structure** - Verify keys exist before accessing
4. **Use async for I/O** - Use `astream()` for async workflows
5. **Use version="v2"** - Always specify `version="v2"` with `astream_events()`
6. **Match async context** - Use `astream()` when you need `await`, `stream()` otherwise

## Troubleshooting

**Issue:** Events not yielding

**Solution:** Ensure nodes return state updates (non-empty dicts)

**Issue:** Missing expected fields in events

**Solution:** Events contain only updated fields, not full state. Use `stream_mode="values"` for complete state.

**Issue:** Token streaming not working

**Solution:** Verify your LLM supports streaming. Some models (like OpenAI o1) do not support token streaming.

**Issue:** get_stream_writer() fails in async code

**Solution:** On Python < 3.11, use parameter injection (`writer: StreamWriter`) instead of `get_stream_writer()`.

## Compatibility

This skill is compatible with LangGraph v1.0+ (released October 2025). All patterns and APIs documented here follow the stable v1.0 interface.

## Additional Resources

- [LangGraph Streaming Documentation](https://docs.langchain.com/oss/python/langgraph/streaming)
- [LangGraph API Reference](https://reference.langchain.com/python/langgraph/graphs/)
- [LangGraph Guides](https://docs.langchain.com/oss/python/langgraph/overview)
