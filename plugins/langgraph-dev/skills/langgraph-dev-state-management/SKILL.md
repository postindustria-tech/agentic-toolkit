---
name: state-management-in-langgraph
description: This skill should be used when the user asks about "state schema", "TypedDict", "state management", "Annotated fields", "state reducers", "graph state", "state patterns", "how to define state", "add_messages", "MessagesState", or needs guidance on structuring LangGraph workflow state.
version: 0.2.4
---

# State Management in LangGraph

## Purpose

This skill provides guidance on designing and managing state in LangGraph workflows. State management is the foundation of LangGraph applications—every node reads state, performs operations, and returns state updates. Proper state design ensures type safety, prevents bugs, and makes workflows maintainable and testable.

## When to Use This Skill

Use this skill when:
- Defining state schema for a new LangGraph workflow
- Adding fields to existing state structures
- Implementing state reducers or append-only fields
- Troubleshooting state-related bugs or type errors
- Deciding between flat vs nested state structures
- Integrating LangChain components (memory, messages) into state

## Core Concepts

### State as TypedDict

LangGraph uses TypedDict for explicit state contracts. This provides:
- Type safety with editor autocomplete
- Self-documenting state structure
- Runtime validation opportunities
- Clear contracts between nodes

**Basic state definition:**
```python
from typing import TypedDict
from langchain_core.messages import BaseMessage

class AgentState(TypedDict):
    messages: list[BaseMessage]
    current_step: str
    confidence: float
```

### Immutable State Transitions

Nodes should not mutate state directly. Instead, return dictionaries with updates:

**Correct pattern:**
```python
def process_node(state: AgentState) -> dict:
    # Don't mutate: state["messages"].append(...)
    # Instead, return updates:
    return {
        "messages": [new_message],
        "current_step": "next_step"
    }
```

LangGraph merges returned dictionaries into the current state automatically.

### Annotated Fields for Special Semantics

Use `Annotated` to specify how field updates should be handled:

**Append-only lists with operator.add:**
```python
from typing import Annotated, TypedDict
import operator

class State(TypedDict):
    results: Annotated[list, operator.add]
    # Updates to results are appended, not replaced
```

### The add_messages Reducer (Recommended for Messages)

For message fields, use the purpose-built `add_messages` reducer instead of `operator.add`:

```python
from typing import Annotated, TypedDict
from langgraph.graph.message import add_messages
from langchain_core.messages import BaseMessage

class State(TypedDict):
    messages: Annotated[list[BaseMessage], add_messages]
```

**Why use add_messages instead of operator.add?**

| Feature | operator.add | add_messages |
|---------|-------------|--------------|
| Basic appending | Yes | Yes |
| ID-based updates | No | Yes |
| OpenAI format conversion | No | Yes |
| Streaming support | No | Yes |
| Tool response handling | No | Yes |

**Example with ID-based updates:**
```python
from langgraph.graph.message import add_messages
from langchain_core.messages import HumanMessage

msgs1 = [HumanMessage(content="Hello", id="1")]
msgs2 = [HumanMessage(content="Hello again", id="1")]

result = add_messages(msgs1, msgs2)
# Result: [HumanMessage(content='Hello again', id='1')]
# The message was updated by ID, not duplicated
```

### Custom Reducers

For custom merge logic, define a reducer function with signature `(existing, new) -> merged`:

```python
from typing import Any

def merge_results(existing: list[Any], new: list[Any]) -> list[Any]:
    """Custom reducer: merge lists while deduplicating new entries."""
    return existing + [x for x in new if x not in existing]

class State(TypedDict):
    results: Annotated[list, merge_results]
```

**See also:** For multi-agent state management patterns and coordination, see the `multi-agent-supervisor` skill.

## State Design Patterns

### Pattern 1: Message-Based State

For conversational or agentic workflows:

```python
from typing import Annotated, TypedDict
from langgraph.graph.message import add_messages
from langchain_core.messages import BaseMessage

class ConversationState(TypedDict):
    messages: Annotated[list[BaseMessage], add_messages]
    context: dict  # Additional context
```

**When to use:** Chatbots, agents, multi-turn conversations

### MessagesState (Quick Start)

LangGraph provides a prebuilt state for simple conversational workflows:

```python
from langgraph.graph import StateGraph, START, MessagesState
# For custom state with AnyMessage type:
from langchain_core.messages import AnyMessage

# MessagesState is equivalent to:
# class MessagesState(TypedDict):
#     messages: Annotated[list[AnyMessage], add_messages]
#
# AnyMessage is a type alias representing any LangChain message type:
# AIMessage, HumanMessage, SystemMessage, ToolMessage, etc.

builder = StateGraph(MessagesState)
builder.add_node("chatbot", chatbot_node)
builder.add_edge(START, "chatbot")
graph = builder.compile()
```

**When to use:** Simple chatbots or agents where you only need message history

**Deprecation Note:** `MessageGraph` (from `langgraph.graph.message`) is deprecated in LangGraph v1.0 and will be removed in v2.0. Use `StateGraph` with `MessagesState` or a custom state with a `messages` field instead.

**See also:** For state mapping between parent and child graphs in modular architectures, see the `subgraphs-and-composition` skill.

### Pattern 2: Task List State

For workflows that execute sequential subtasks:

```python
from typing import TypedDict

class TaskState(TypedDict):
    task_list: list[str]
    completed_tasks: list[str]
    current_task: str
    results: dict
```

**When to use:** Multi-step workflows, pipeline processing

### Pattern 3: Control Flow State

For explicit state machine behavior:

```python
from typing import TypedDict

class WorkflowState(TypedDict):
    current_step: str  # Controls routing
    data: dict  # Payload
    error_count: int  # Error tracking
```

**When to use:** Complex routing, error recovery, explicit state machines

### Pattern 4: Nested Pydantic State

For complex data with validation:

```python
from typing import Annotated, TypedDict
from pydantic import BaseModel
from langgraph.graph.message import add_messages
from langchain_core.messages import BaseMessage

class Config(BaseModel):
    temperature: float
    max_tokens: int

class State(TypedDict):
    config: Config  # Pydantic model for validation
    messages: Annotated[list[BaseMessage], add_messages]
```

**Important Pydantic Limitations:**
- Runtime validation only occurs on inputs to the first node
- Graph output will NOT be a Pydantic instance (returns dict)
- Pydantic is less performant than TypedDict for state
- Use Pydantic only when you need strict input validation

**When to use:** Complex configuration, input validation requirements

**See also:** For graph mechanics, compilation, and building workflows with your state schema, see the `graph-construction` skill.

## Best Practices

### Keep State Flat When Possible

**Prefer:**
```python
class State(TypedDict):
    user_id: str
    user_name: str
    user_email: str
```

**Avoid (unless necessary):**
```python
class State(TypedDict):
    user: dict  # Nested structure loses type safety
```

### Use Descriptive Field Names

**Good:** `classification_confidence`, `processing_stage`, `retrieved_documents`

**Avoid:** `data`, `result`, `temp`, `x`

### Document Field Purpose

```python
from typing import TypedDict
from langchain_core.documents import Document

class State(TypedDict):
    retrieved_docs: list[Document]  # Documents from vector search
    query_vector: list[float]  # Embedded user query
    relevance_scores: list[float]  # Similarity scores per document
```

### Avoid Storing Large Objects

**Avoid:**
```python
class State(TypedDict):
    llm_instance: ChatOpenAI  # Don't store instances
    vectorstore: FAISS  # Don't store databases
```

**Prefer:**
```python
class State(TypedDict):
    llm_config: dict  # Store configuration
    document_ids: list[str]  # Store references
```

### Initialize State with Defaults

```python
def create_initial_state() -> AgentState:
    return {
        "messages": [],
        "current_step": "start",
        "confidence": 0.0
    }
```

## Common Patterns

### Adding to Lists (Append-Only)

```python
from typing import Annotated, TypedDict
import operator

class State(TypedDict):
    results: Annotated[list, operator.add]

def node1(state): return {"results": [1, 2]}
def node2(state): return {"results": [3, 4]}
# Final state["results"] = [1, 2, 3, 4]
```

### Replacing Values

```python
class State(TypedDict):
    current_step: str  # No Annotated = replacement

def node1(state): return {"current_step": "processing"}
def node2(state): return {"current_step": "complete"}
# Final state["current_step"] = "complete"
```

### Conditional Updates

```python
def conditional_node(state: State) -> dict:
    if state["confidence"] > 0.8:
        return {"current_step": "high_confidence_path"}
    return {"current_step": "clarify"}
```

### Parallel Execution with Reducers

```python
from typing import Annotated
import operator

class State(TypedDict):
    parallel_results: Annotated[list, operator.add]

# Multiple nodes can update parallel_results simultaneously
# All updates are accumulated via operator.add
```

## Troubleshooting

**Issue:** Type errors when accessing state fields

**Solution:** Ensure TypedDict definition matches actual usage. Use type hints consistently.

**Issue:** State updates not persisting

**Solution:** Verify nodes return dictionaries, not mutated state objects.

**Issue:** Lists being replaced instead of appended

**Solution:** Use `Annotated[list[...], operator.add]` for general lists, or `Annotated[list[BaseMessage], add_messages]` for messages.

**Issue:** State becoming too complex

**Solution:** Review state design. Consider splitting into multiple smaller workflows or using nested Pydantic models with validation.

## Integration with LangChain Components

### Messages

```python
from typing import Annotated, TypedDict
from langgraph.graph.message import add_messages
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage

class State(TypedDict):
    messages: Annotated[list[BaseMessage], add_messages]

def add_user_message(state: State) -> dict:
    return {"messages": [HumanMessage(content="Hello")]}

def add_ai_response(state: State) -> dict:
    return {"messages": [AIMessage(content="Hi there!")]}
```

### Persistence with Checkpointing

LangGraph automatically saves state at each node when a checkpointer is configured:

```python
from langgraph.graph import StateGraph
from langgraph.checkpoint.memory import InMemorySaver

builder = StateGraph(State)
# ... add nodes and edges ...

# Note: Only use InMemorySaver for debugging or testing.
# For production: pip install langgraph-checkpoint-postgres
# Then: from langgraph.checkpoint.postgres import PostgresSaver
checkpointer = InMemorySaver()
graph = builder.compile(checkpointer=checkpointer)

# State is automatically saved after each node execution
result = graph.invoke(
    {"messages": []},
    config={"configurable": {"thread_id": "1"}}
)
```

This enables:
- Resume from failures
- Human-in-the-loop workflows
- Time-travel debugging

## Additional Resources

### Reference Files

For detailed patterns and advanced techniques:
- **`references/state-patterns.md`** - Complete pattern catalog with examples

### Examples

Working examples in `examples/`:
- **`state-examples.py`** - Common state patterns demonstrating all concepts in this skill

## Official Documentation

- [LangGraph Graph API Overview](https://docs.langchain.com/oss/python/langgraph/graph-api)
- [LangGraph API Reference](https://reference.langchain.com/python/langgraph/graphs/)
- [LangChain Core Messages](https://reference.langchain.com/python/langchain/messages/)
- [add_messages Guide](https://dev.to/aiengineering/a-beginners-guide-to-getting-started-with-addmessages-reducer-in-langgraph-4gk0)

See `references/` for complete pattern examples.
