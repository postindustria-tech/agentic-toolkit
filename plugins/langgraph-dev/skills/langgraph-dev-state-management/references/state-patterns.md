# State Patterns Reference

Complete catalog of LangGraph state patterns.

## Message-Based Patterns

### Basic Conversation State

```python
from typing import Annotated, TypedDict
from langgraph.graph import StateGraph, START
from langgraph.graph.message import add_messages
from langchain_core.messages import BaseMessage, AIMessage

class State(TypedDict):
    messages: Annotated[list[BaseMessage], add_messages]
    next_step: str

def greet(state: State) -> dict:
    return {
        "messages": [AIMessage(content="Hello!")],
        "next_step": "get_name"
    }

workflow = StateGraph(State)
workflow.add_node("greet", greet)
workflow.add_edge(START, "greet")
```

### Append-Only Messages with add_messages

```python
from typing import Annotated, TypedDict
from langgraph.graph.message import add_messages
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage

class State(TypedDict):
    messages: Annotated[list[BaseMessage], add_messages]
    current_step: str

# Multiple nodes can append to messages without replacing
def node1(state): return {"messages": [HumanMessage(content="Hello")]}
def node2(state): return {"messages": [AIMessage(content="Hi there!")]}
# Result: state["messages"] contains both messages (appended)
```

## Task Execution Patterns

### Task List with Sequential Processing

```python
from typing import Annotated, TypedDict
from langgraph.graph.message import add_messages
from langchain_core.messages import BaseMessage, AIMessage

class State(TypedDict):
    messages: Annotated[list[BaseMessage], add_messages]
    current_step: str
    task_list: list[str]
    error_count: int

def execute_subtask(state: State) -> dict:
    if not state["task_list"]:
        return {"current_step": "summarize"}

    current_task = state["task_list"][0]
    remaining_tasks = state["task_list"][1:]

    # Process task...
    next_step = "execute_subtask" if remaining_tasks else "summarize"

    return {
        "messages": [AIMessage(content=f"Completed: {current_task}")],
        "task_list": remaining_tasks,
        "current_step": next_step
    }
```

## State Machine Patterns

### Error Tracking with Recovery

```python
from typing import Annotated, TypedDict
from langgraph.graph.message import add_messages
from langchain_core.messages import BaseMessage, AIMessage

class State(TypedDict):
    messages: Annotated[list[BaseMessage], add_messages]
    current_step: str
    error_count: int

def handle_error(state: State) -> dict:
    error_count = state["error_count"] + 1

    if error_count > 3:
        return {
            "messages": [AIMessage(content="Let's start over.")],
            "error_count": 0,
            "current_step": "greet_and_ask"
        }
    else:
        return {
            "messages": [AIMessage(content="Could you please rephrase?")],
            "error_count": error_count
        }
```

### Confidence-Based Routing

```python
from typing import Annotated, TypedDict
from langgraph.graph.message import add_messages
from langchain_core.messages import BaseMessage

class State(TypedDict):
    messages: Annotated[list[BaseMessage], add_messages]
    intent: str
    confidence: float

def should_continue(state: State) -> str:
    if state["confidence"] > 0.8:
        return "high_confidence"
    return "low_confidence"
```

## Parallel Execution Patterns

### Fan-Out/Fan-In with Reducers

```python
from typing import Annotated, TypedDict
import operator

class State(TypedDict):
    results: Annotated[list, operator.add]
    input_data: str

def branch_1(state): return {"results": [1, 2]}
def branch_2(state): return {"results": [3, 4]}
def branch_3(state): return {"results": [5, 6]}

# All branches execute in parallel
# Results accumulated: [1, 2, 3, 4, 5, 6]
```

**Note:** Without a reducer on `results`, parallel writes would cause `INVALID_CONCURRENT_GRAPH_UPDATE` errors.

### Custom Reducer Logic

```python
from typing import Annotated, TypedDict

def deduplicate_merge(existing: list, new: list) -> list:
    """Merge while removing duplicates."""
    seen = set(existing)
    return existing + [x for x in new if x not in seen]

class State(TypedDict):
    unique_results: Annotated[list, deduplicate_merge]
```

## Integration Patterns

### Persistence with Checkpointing (Recommended)

**Note:** `ConversationBufferMemory` is deprecated. Use LangGraph's checkpointing system instead:

```python
from typing import Annotated, TypedDict
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langgraph.checkpoint.memory import InMemorySaver
from langchain_core.messages import BaseMessage

class State(TypedDict):
    messages: Annotated[list[BaseMessage], add_messages]
    current_step: str

def process_node(state: State) -> dict:
    return {"current_step": "done"}

builder = StateGraph(State)
builder.add_node("process", process_node)
builder.add_edge(START, "process")
builder.add_edge("process", END)

# Note: Only use InMemorySaver for debugging or testing.
# For production, use PostgresSaver from langgraph-checkpoint-postgres.
checkpointer = InMemorySaver()
graph = builder.compile(checkpointer=checkpointer)

# State is persisted automatically
result = graph.invoke(
    {"messages": [], "current_step": "start"},
    config={"configurable": {"thread_id": "user-123"}}
)
```

### Pydantic Models in State

```python
from typing import TypedDict
from pydantic import BaseModel, Field

class MovieReview(BaseModel):
    title: str = Field(description="Movie title")
    year: int = Field(description="Release year")
    rating: float = Field(ge=0, le=10, description="Rating 0-10")

class State(TypedDict):
    query: str
    review: MovieReview  # Validated structured data
    raw_response: str
```

**Limitations:** Pydantic validation only runs on first node input; graph output is dict, not Pydantic instance.

## Advanced Patterns

### Multi-Agent State

```python
from typing import Annotated, TypedDict
from langgraph.graph.message import add_messages
from langchain_core.messages import BaseMessage

class SupervisorState(TypedDict):
    messages: Annotated[list[BaseMessage], add_messages]
    next_agent: str  # Routing decision
    agent_outputs: dict  # Outputs from each agent

def supervisor_node(state: SupervisorState) -> dict:
    # Supervisor makes routing decision
    decision = router.invoke(state["messages"])
    return {"next_agent": decision.next_agent}
```

### CRAG State (Corrective RAG)

```python
from typing import TypedDict
from langchain_core.documents import Document

class CRAGState(TypedDict):
    query: str
    documents: list[Document]
    relevance_scores: list[str]  # "yes" or "no" per doc
    web_search_needed: bool
    generation: str

def grade_documents(state: CRAGState) -> dict:
    filtered_docs = []
    for doc in state["documents"]:
        score = grader.invoke({"query": state["query"], "doc": doc})
        if score.relevance == "yes":
            filtered_docs.append(doc)

    web_search = len(filtered_docs) == 0

    return {
        "documents": filtered_docs,
        "web_search_needed": web_search
    }
```

## Best Practice Patterns

### Initialization Helper

```python
from langchain_core.messages import HumanMessage

def create_initial_state(user_input: str) -> State:
    """Factory function for consistent state initialization."""
    return {
        "messages": [HumanMessage(content=user_input)],
        "current_step": "classify",
        "intent": "",
        "confidence": 0.0,
        "error_count": 0
    }
```

### State Validation

```python
def validate_state(state: State) -> bool:
    """Validate state integrity before processing."""
    if not isinstance(state.get("messages"), list):
        return False
    if state.get("confidence", 0) < 0 or state.get("confidence", 0) > 1:
        return False
    return True
```

### State Snapshot for Debugging

```python
def log_state(state: State, step: str) -> None:
    """Log state at specific workflow steps."""
    print(f"State at {step}:")
    print(f"  current_step: {state.get('current_step')}")
    print(f"  messages: {len(state.get('messages', []))}")
    print(f"  task_list: {state.get('task_list', [])}")
```

## Common Mistakes to Avoid

### ❌ Mutating State Directly

```python
def bad_node(state: State) -> dict:
    state["messages"].append(new_message)  # DON'T DO THIS
    return state  # Wrong!
```

### ✅ Return State Updates

```python
def good_node(state: State) -> dict:
    return {"messages": [new_message]}  # Correct
```

### ❌ Storing Large Objects

```python
class BadState(TypedDict):
    llm: ChatOpenAI  # Don't store instances
    vectorstore: FAISS  # Don't store databases
```

### Store Configuration/References

```python
from typing import TypedDict

class GoodState(TypedDict):
    llm_config: dict  # Store config
    document_ids: list[str]  # Store IDs
```

## Official Documentation

- [LangGraph Graph API](https://reference.langchain.com/python/langgraph/graphs/)
- [LangChain Core Messages](https://reference.langchain.com/python/langchain/messages/)
- [add_messages Reducer](https://dev.to/aiengineering/a-beginners-guide-to-getting-started-with-addmessages-reducer-in-langgraph-4gk0)

See `examples/` for complete working code.
