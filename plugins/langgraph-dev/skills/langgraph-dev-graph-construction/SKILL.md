---
name: graph-construction-in-langgraph
description: This skill should be used when the user asks about "create graph", "add nodes", "add edges", "compile graph", "LangGraph workflow", "StateGraph", "START node", "END node", "graph visualization", "streaming execution", "conditional edges based on output", or needs guidance on building LangGraph workflows.
version: 0.3.2
---

# Graph Construction in LangGraph

## Purpose

This skill provides guidance on constructing LangGraph workflows using StateGraph. Graph construction transforms isolated node functions into orchestrated workflows with explicit control flow, enabling complex multi-step agentic systems.

## Compatibility

This skill is compatible with **LangGraph 1.x** (tested with v1.0.5, December 2025).

**Feature-specific version requirements:**
- `interrupt()` function: requires LangGraph >= 0.2.31
- `add_sequence()` method: requires LangGraph >= 0.2.46

## When to Use This Skill

Use this skill when:
- Creating a new LangGraph workflow from scratch
- Adding nodes or edges to existing graphs
- Defining entry points and exit conditions
- Setting up conditional routing between nodes
- Compiling and visualizing graph structures
- Troubleshooting graph connectivity issues

## Core Concepts

### StateGraph Basics

StateGraph is the foundation of LangGraph workflows:

```python
from langgraph.graph import StateGraph, START, END
from typing import TypedDict  # Use typing_extensions.TypedDict for Python 3.9

class State(TypedDict):
    messages: list
    step: str

# Create graph with state schema
workflow = StateGraph(State)
```

### Using MessagesState for Chat Applications

For chat-based applications, LangGraph provides a built-in `MessagesState` with automatic message management:

```python
from langgraph.graph import StateGraph, MessagesState, START, END

# MessagesState provides a 'messages' field with add_messages reducer
workflow = StateGraph(MessagesState)

def chat_node(state: MessagesState) -> dict:
    # Access messages from state
    last_message = state["messages"][-1]
    response = generate_response(last_message)  # Your LLM call here
    return {"messages": [response]}

workflow.add_node("chat", chat_node)
workflow.add_edge(START, "chat")
workflow.add_edge("chat", END)
```

`MessagesState` automatically handles message deduplication and updates based on message IDs.

### Adding Nodes

Nodes are functions that transform state:

```python
def process_input(state: State) -> dict:
    return {"step": "processed"}

# Add node to graph
workflow.add_node("process", process_input)
```

### Adding Edges

Edges define workflow transitions:

```python
# Direct edge: always go from A to B
workflow.add_edge("process", "validate")

# Edge to END: terminate workflow
workflow.add_edge("validate", END)
```

### Setting Entry Point

Every graph needs an entry point. Use the START constant with add_edge:

```python
from langgraph.graph import START

workflow.add_edge(START, "process")
```

### Compiling the Graph

Convert workflow definition to executable app:

```python
app = workflow.compile()
result = app.invoke(initial_state)
```

## Building a Complete Workflow

### Step-by-Step Process

**1. Define State Schema**
```python
from typing import TypedDict, List
from langchain_core.messages import BaseMessage, AIMessage

class AgentState(TypedDict):
    messages: List[BaseMessage]
    current_step: str
```

**2. Create StateGraph**
```python
workflow = StateGraph(AgentState)
```

**3. Define Node Functions**
```python
def classify(state: AgentState) -> dict:
    # Classification logic
    return {"current_step": "respond"}

def respond(state: AgentState) -> dict:
    # Response logic
    response = AIMessage(content="Generated response")
    return {"messages": [response]}
```

**4. Add Nodes**
```python
workflow.add_node("classify", classify)
workflow.add_node("respond", respond)
```

**5. Add Edges**
```python
workflow.add_edge(START, "classify")
workflow.add_edge("classify", "respond")
workflow.add_edge("respond", END)
```

**6. Compile and Execute**
```python
app = workflow.compile()
result = app.invoke({"messages": [user_msg], "current_step": ""})
```

**See also:** For modular graph architectures and reusable workflow components, see the `subgraphs-and-composition` skill.

## Node Design Patterns

### Pure Node Functions

```python
def pure_node(state: State) -> dict:
    """Returns only state updates, no side effects."""
    new_value = state["input"].upper()  # Transform existing state
    return {"field": new_value}
```

### Nodes with External Calls

```python
def llm_node(state: State) -> dict:
    """Calls external services (LLM, API, etc.)."""
    response = llm.invoke(state["messages"])
    return {"messages": [response]}
```

### Multi-Update Nodes

```python
def multi_update_node(state: State) -> dict:
    """Updates multiple state fields."""
    new_message = AIMessage(content="Processing complete")
    return {
        "messages": [new_message],
        "current_step": "next",
        "confidence": 0.95
    }
```

### Nodes with Error Handling

Production nodes should handle errors gracefully:

```python
def safe_llm_node(state: State) -> dict:
    """Node with error handling for robustness."""
    try:
        response = llm.invoke(state["messages"])
        return {"messages": [response], "error": None}
    except Exception as e:
        return {"error": str(e), "current_step": "error_recovery"}
```

## Edge Patterns

### Linear Flow

```python
workflow.add_edge("step1", "step2")
workflow.add_edge("step2", "step3")
workflow.add_edge("step3", END)
```

### Sequential Pipeline with add_sequence

For simple sequential workflows, use `add_sequence` to reduce boilerplate:

```python
# Instead of manual edges:
# workflow.add_node("step1", step1_node)
# workflow.add_node("step2", step2_node)
# workflow.add_node("step3", step3_node)
# workflow.add_edge("step1", "step2")
# workflow.add_edge("step2", "step3")

# Use add_sequence for cleaner code:
workflow.add_sequence([
    ("step1", step1_node),
    ("step2", step2_node),
    ("step3", step3_node),
])
workflow.add_edge(START, "step1")
workflow.add_edge("step3", END)
```

`add_sequence` automatically adds nodes and connects them in order.

### Branching (see conditional-routing skill)

```python
# Conditional edges require a router function and path_map
def router_function(state: State) -> str:
    if state.get("confidence", 0) > 0.8:
        return "respond"
    return "clarify"

workflow.add_conditional_edges(
    "classify",
    router_function,
    path_map={"respond": "respond", "clarify": "clarify"}  # Explicit mapping recommended
)
```

### Loops

Loops in LangGraph MUST use conditional edges with explicit termination conditions. Direct self-edges create infinite loops.

```python
# CORRECT: Self-loop with termination condition
def should_continue_processing(state: State) -> str:
    if state.get("iteration_count", 0) >= 3 or state.get("done"):
        return "end"
    return "continue"

workflow.add_conditional_edges(
    "process",
    should_continue_processing,
    path_map={"continue": "process", "end": END}
)

# Cycle between nodes (also requires condition)
def should_reprocess(state: State) -> str:
    if state.get("valid"):
        return "complete"
    return "reprocess"

workflow.add_conditional_edges(
    "validate",
    should_reprocess,
    path_map={"reprocess": "process", "complete": "respond"}
)
```

## Graph Compilation

### Basic Compilation

```python
app = workflow.compile()
```

### Compilation with Checkpointing

```python
from langgraph.checkpoint.memory import InMemorySaver

memory = InMemorySaver()
app = workflow.compile(checkpointer=memory)

# Note: InMemorySaver is for debugging/testing only.
# For production, use PostgresSaver from langgraph-checkpoint-postgres.
```

### Using Checkpoints with Thread ID

Checkpointing requires a thread_id to persist and resume conversations:

```python
from langgraph.checkpoint.memory import InMemorySaver

memory = InMemorySaver()
app = workflow.compile(checkpointer=memory)

# Thread ID is required for checkpoint persistence
config = {"configurable": {"thread_id": "conversation-1"}}
result = app.invoke(initial_state, config)

# Resume later with same thread_id to continue conversation
result2 = app.invoke({"messages": ["follow-up"]}, config)
```

### Compilation with Interrupts

LangGraph supports two approaches for human-in-the-loop workflows:

**Option 1: Compile-time interrupts (interrupt_before/interrupt_after)**
```python
# Pause before specific nodes
app = workflow.compile(interrupt_before=["human_review"])
```

**Option 2: interrupt() function (recommended for LangGraph 0.2.31+)**
```python
from langgraph.types import interrupt, Command

def human_feedback_node(state: State) -> dict:
    # Pause and wait for user input
    feedback = interrupt("Please provide feedback:")
    return {"user_feedback": feedback}

# Checkpointer required for interrupt()
memory = InMemorySaver()
app = workflow.compile(checkpointer=memory)

# Resume with Command
result = app.invoke(Command(resume="User's feedback here"), config)
```

The `interrupt()` function is more flexible, allowing you to pause at any point within a node and pass context to the user.

## Execution Patterns

### Synchronous Invocation

```python
result = app.invoke(initial_state)
```

### Asynchronous Invocation

```python
result = await app.ainvoke(initial_state)
```

### Streaming Execution

```python
# Default streaming (updates mode)
for event in app.stream(initial_state):
    print(event)

# Stream full state after each step
for state in app.stream(initial_state, stream_mode="values"):
    print(state)

# Stream LLM tokens (for chat applications)
for chunk in app.stream(initial_state, stream_mode="messages"):
    print(chunk)

# Multiple modes simultaneously
for event in app.stream(initial_state, stream_mode=["updates", "messages"]):
    print(event)
```

Available stream modes: `values`, `updates`, `messages`, `custom`, `debug`, `checkpoints`, `tasks`.

## Visualization

### Generate Mermaid Diagram

```python
# Get Mermaid code (works on both workflow and compiled app)
mermaid_code = workflow.get_graph().draw_mermaid()
print(mermaid_code)
```

### PNG Visualization (Recommended for Notebooks)

```python
from IPython.display import Image, display

# Compile first, then visualize
app = workflow.compile()
png_data = app.get_graph().draw_mermaid_png()
display(Image(png_data))
```

### ASCII Visualization

```python
print(workflow.get_graph().draw_ascii())
```

## Best Practices

### Organize Nodes Logically

Group related functionality:
```python
# Input processing
workflow.add_node("parse_input", parse_input)
workflow.add_node("validate_input", validate_input)

# Core logic
workflow.add_node("classify", classify)
workflow.add_node("process", process)

# Output
workflow.add_node("format_output", format_output)
```

### Use Descriptive Node Names

**Good:** `classify_intent`, `retrieve_documents`, `generate_response`

**Avoid:** `node1`, `process`, `handle`

### Keep Graphs Focused

**Prefer:** Multiple small graphs for different workflows

**Avoid:** One massive graph doing everything

### Document Complex Routing

```python
def router(state: State) -> str:
    """
    Route based on confidence:
    - > 0.8: high_confidence
    - 0.5-0.8: medium_confidence
    - < 0.5: low_confidence
    """
    if state["confidence"] > 0.8:
        return "high_confidence"
    elif state["confidence"] > 0.5:
        return "medium_confidence"
    return "low_confidence"
```

## Common Patterns

### Simple Pipeline

```python
workflow = StateGraph(State)
workflow.add_node("input", process_input)
workflow.add_node("transform", transform_data)
workflow.add_node("output", generate_output)

workflow.add_edge(START, "input")
workflow.add_edge("input", "transform")
workflow.add_edge("transform", "output")
workflow.add_edge("output", END)
```

### Error Handling

```python
workflow.add_node("process", process_node)
workflow.add_node("error_handler", handle_error)

workflow.add_conditional_edges(
    "process",
    lambda state: "error" if state.get("error") else "success",
    path_map={"error": "error_handler", "success": END}
)
```

### Retry Loop

```python
def should_retry(state: State) -> str:
    if state["retry_count"] < 3 and state.get("error"):
        return "retry"
    return "end"

workflow.add_conditional_edges(
    "process",
    should_retry,
    path_map={
        "retry": "process",  # Loop back
        "end": END
    }
)
```

## Troubleshooting

**Issue:** "Node not found" error

**Solution:** Ensure node is added before referencing in edges: `workflow.add_node()` before `workflow.add_edge()`

**Issue:** Graph has no entry point

**Solution:** Add `workflow.add_edge(START, "node_name")` - ensure START is imported from langgraph.graph

**Issue:** Infinite loop in graph

**Solution:** Ensure loops have exit conditions via conditional edges

**Issue:** State not updating between nodes

**Solution:** Verify nodes return dictionaries with state updates

## Additional Resources

### Official Documentation

- [LangGraph Documentation](https://docs.langchain.com/oss/python/langgraph/overview) - Official documentation and concepts
- [LangGraph How-To Guides](https://docs.langchain.com/oss/python/langgraph/use-graph-api) - Graph API usage and patterns
- [LangGraph API Reference](https://reference.langchain.com/python/langgraph/graphs/) - StateGraph API reference
- [LangGraph PyPI](https://pypi.org/project/langgraph/) - Package information and changelog

### Related Skills

- **conditional-routing** - Advanced routing and branching patterns
- **state-management** - State schema design and reducers
