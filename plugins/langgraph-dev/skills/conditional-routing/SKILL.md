---
name: conditional-routing-in-langgraph
description: This skill should be used when the user asks about "conditional routing", "branch logic", "dynamic routing", "decision edges", "add_conditional_edges", "routing function", "state-based routing", "Command API", "Send API", or needs guidance on implementing conditional flow in LangGraph workflows.
version: 0.4.0
---

# Conditional Routing in LangGraph

## Purpose

Conditional routing enables LangGraph workflows to make dynamic decisions about execution paths based on state values. This transforms static pipelines into adaptive agentic systems that respond intelligently to runtime conditions.

## When to Use This Skill

Use this skill when workflows need to:
- Branch execution based on confidence scores or quality metrics
- Route to different nodes based on classification results
- Implement retry logic with conditional loops
- Handle success/failure paths differently
- Create adaptive multi-path workflows
- Combine state updates with routing decisions (Command API)
- Implement map-reduce parallel workflows (Send API)

## Required Imports

```python
from typing import Literal, TypedDict, Annotated, Sequence, Callable, Any
from collections.abc import Hashable  # For type annotations in path functions
from langgraph.graph import StateGraph, START, END
from langgraph.types import Send, Command
import operator  # For reducer functions in parallel execution
```

**Note**: The Command API was released December 2024. The Send API has been available since LangGraph 0.2.0+. LangGraph v1.0 was released October 2025 as a stability-focused release. All examples are tested with LangGraph 1.0.x and remain compatible with future 1.x releases. Check [PyPI](https://pypi.org/project/langgraph/) for the latest version.

**Convention**: Throughout this skill, examples use `workflow` as the variable name for the `StateGraph` instance. Create it with: `workflow = StateGraph(YourStateClass)`.

## Core Concepts

### Conditional Edges

Unlike direct edges (`add_edge`), conditional edges use functions to determine the next node:

```python
from typing import Literal

def router(state: State) -> Literal["high_confidence_path", "low_confidence_path"]:
    """Returns name of next node based on state."""
    if state["confidence"] > 0.8:
        return "high_confidence_path"
    return "low_confidence_path"

workflow.add_conditional_edges(
    "classify",
    router,
    {
        "high_confidence_path": "respond",
        "low_confidence_path": "clarify"
    }
)
```

### The path_map Parameter

The `add_conditional_edges` method has the following signature:

```python
add_conditional_edges(
    source: str,                                                                      # Starting node
    path: Callable[..., Hashable | Sequence[Hashable]]                                # Router function (sync)
        | Callable[..., Awaitable[Hashable | Sequence[Hashable]]]                     # Router function (async)
        | Runnable[Any, Hashable | Sequence[Hashable]],                               # Or a Runnable
    path_map: dict[Hashable, str] | list[str] | None = None                           # Optional mapping
) -> Self
```

**Note**: `Hashable` and `Sequence` are from `collections.abc`; `Awaitable` is from `typing`. The `Runnable` type is from `langchain_core.runnables`.

**When to use path_map**:
- When router returns keys that differ from node names
- To make routing logic more readable
- To provide explicit mapping for visualization

**When path_map is optional**:
- When using `Literal` return type hints on router function
- When router directly returns actual node names

Without type hints on the path function's return value (e.g., `-> Literal["foo", "__end__"]:`) or a `path_map`, the graph visualization assumes the edge could transition to any node.

### Router Function Requirements

Router functions must:
1. Accept state as single parameter
2. Return string matching a key in the mapping dictionary (or node name directly)
3. Be deterministic (same state -> same output)
4. Use `Literal` type hints for proper visualization

```python
from typing import Literal

def should_continue(state: State) -> Literal["continue", "end"]:
    """Valid router function with proper type hints."""
    return "continue" if state["task_list"] else "end"
```

### Async Router Functions

Router functions can be async for use with async graph execution:

```python
from typing import Literal

async def async_router(state: State) -> Literal["fast_path", "slow_path"]:
    """Async router that may perform I/O.

    Note: check_external_service is a placeholder for your async I/O function
    (e.g., database lookup, API call, cache check).
    """
    result = await check_external_service(state["query"])
    return "fast_path" if result["cached"] else "slow_path"

# Use with async graph execution
result = await graph.ainvoke(initial_state)
```

## Complete Runnable Example

Here is a complete, copy-pasteable example demonstrating conditional routing:

```python
from typing import Literal, TypedDict
from langgraph.graph import StateGraph, START, END

# 1. Define the state schema
class AgentState(TypedDict):
    query: str
    confidence: float
    response: str

# 2. Define node functions
def classify_node(state: AgentState) -> dict:
    """Simulates classification - in production, use an LLM."""
    query = state["query"].lower()
    if "urgent" in query or "help" in query:
        return {"confidence": 0.95}
    elif "question" in query:
        return {"confidence": 0.7}
    return {"confidence": 0.3}

def high_confidence_node(state: AgentState) -> dict:
    """Handle high-confidence queries directly."""
    return {"response": f"Direct response to: {state['query']}"}

def clarify_node(state: AgentState) -> dict:
    """Request clarification for low-confidence queries."""
    return {"response": f"Could you clarify: {state['query']}?"}

# 3. Define router function with Literal type hint
def route_by_confidence(state: AgentState) -> Literal["respond", "clarify"]:
    """Route based on classification confidence."""
    if state["confidence"] > 0.8:
        return "respond"
    return "clarify"

# 4. Build the graph
workflow = StateGraph(AgentState)

# Add nodes
workflow.add_node("classify", classify_node)
workflow.add_node("respond", high_confidence_node)
workflow.add_node("clarify", clarify_node)

# Add edges
workflow.add_edge(START, "classify")
workflow.add_conditional_edges(
    "classify",
    route_by_confidence,
    {"respond": "respond", "clarify": "clarify"}
)
workflow.add_edge("respond", END)
workflow.add_edge("clarify", END)

# 5. Compile and run
graph = workflow.compile()

# Test with different inputs
result1 = graph.invoke({"query": "Urgent help needed!", "confidence": 0.0, "response": ""})
print(f"High confidence: {result1['response']}")
# Output: Direct response to: Urgent help needed!

result2 = graph.invoke({"query": "Random text", "confidence": 0.0, "response": ""})
print(f"Low confidence: {result2['response']}")
# Output: Could you clarify: Random text?
```

## Routing Patterns

### Binary Routing (Success/Failure)

```python
from typing import Literal

def check_success(state: State) -> Literal["success", "failure"]:
    return "success" if not state.get("error") else "failure"

workflow.add_conditional_edges(
    "process",
    check_success,
    {"success": END, "failure": "error_handler"}
)
```

### Multi-Way Routing

```python
from typing import Literal

def classify_priority(state: State) -> Literal["urgent", "normal", "low"]:
    score = state["priority_score"]
    if score > 0.8:
        return "urgent"
    elif score > 0.5:
        return "normal"
    return "low"

workflow.add_conditional_edges(
    "triage",
    classify_priority,
    {
        "urgent": "immediate_response",
        "normal": "queue_processing",
        "low": "batch_processing"
    }
)
```

### Loop Routing

```python
from typing import Literal

def should_retry(state: State) -> Literal["retry", "done"]:
    if state["retry_count"] < 3 and state.get("error"):
        return "retry"
    return "done"

workflow.add_conditional_edges(
    "attempt",
    should_retry,
    {"retry": "attempt", "done": END}  # Loop back or end
)
```

### Fan-Out Routing with Send API (Map-Reduce)

The Send API is the recommended approach for dynamic parallel execution where each parallel branch receives different state:

```python
from langgraph.types import Send
from typing import Annotated, TypedDict
import operator

# Main graph state with reducer for collecting results
class OverallState(TypedDict):
    tasks: list[str]
    results: Annotated[list[str], operator.add]  # Reducer aggregates parallel results

# Worker node state (different from main graph state)
class TaskState(TypedDict):
    """State for individual task processing nodes."""
    task: str
    index: int

def fan_out_to_processors(state: OverallState) -> list[Send]:
    """Send each task to a processor node with task-specific state."""
    return [
        Send("process_task", {"task": task, "index": i})
        for i, task in enumerate(state["tasks"])
    ]

def process_task(state: TaskState) -> dict:
    """Worker node processes a single task.

    Returns results in list format for reducer aggregation.
    """
    result = f"Processed: {state['task']} (index {state['index']})"
    return {"results": [result]}  # List format required for operator.add reducer

workflow.add_conditional_edges(START, fan_out_to_processors)
workflow.add_edge("process_task", END)  # Results auto-aggregated by reducer
```

**How the reducer works**: When parallel `process_task` nodes complete, the `Annotated[list[str], operator.add]` reducer automatically combines all returned `results` lists into the main state. Each worker returns `{"results": [result]}` and the reducer concatenates them.

**Send Constructor**: `Send(node: str, arg: Any)`
- `node`: Target node name to invoke
- `arg`: State to pass to the target node (can differ from main graph state)

**Use Send when**:
- Processing a dynamic list of items in parallel
- Each parallel branch needs different input state
- Implementing map-reduce workflows

### Static Parallel Routing

For static parallel execution (same nodes always), return a list:

```python
from typing import Literal

def route_parallel(state: State) -> list[Literal["process_a", "process_b", "process_c"]]:
    """Return list of nodes to execute in parallel."""
    return ["process_a", "process_b", "process_c"]

workflow.add_conditional_edges("fan_out", route_parallel)
```

## Command API (Modern Alternative)

The Command API combines state updates with routing decisions in a single return value. This is the recommended pattern when you need to both update state and control flow.

### Basic Command Usage

```python
from typing import Literal
from langgraph.types import Command

def process_node(state: State) -> Command[Literal["next_node", "error_handler"]]:
    """Process data and route to next node."""
    if state["data_valid"]:
        return Command(
            update={"processed": True},
            goto="next_node"
        )
    return Command(
        update={"error": "Invalid data"},
        goto="error_handler"
    )
```

### Command Parameters

```python
from typing import Sequence

Command(
    graph: str | None = None,                        # Target graph (None=current, Command.PARENT=parent)
    update: Any | None = None,                       # State update to apply
    resume: dict[str, Any] | Any | None = None,      # Resume value for interrupts (single value or interrupt ID mapping)
    goto: Send | Sequence[Send | N] | N = ()         # Next node(s): node name, Send object, or sequence thereof
)
```

**Note**: When using keyword arguments (recommended), parameter order does not matter. The signature above shows the official parameter order from the LangGraph source code.

### Command vs add_conditional_edges

| Feature | add_conditional_edges | Command |
|---------|----------------------|---------|
| State update + routing | Separate operations | Combined in one return |
| Defined in | Graph builder | Node function |
| Type safety | Via path_map or Literal | Via Literal annotation |
| Best for | Static routing logic | Dynamic routing with state updates |
| Multi-agent handoffs | Requires external state | Built-in support |

### Multi-Agent Handoff with Command

```python
from typing import Literal
from langgraph.types import Command
from langgraph.graph import END

def agent_a(state: State) -> Command[Literal["agent_b", "agent_c", "__end__"]]:
    """Agent A processes and hands off to appropriate agent.

    Note on type annotations:
    - Use "__end__" in Literal type hints (Python's Literal doesn't accept variables)
    - Use END constant in actual code (END == "__end__")
    """
    result = process_task(state["task"])

    if result["needs_research"]:
        return Command(update={"context": result}, goto="agent_b")
    elif result["needs_code"]:
        return Command(update={"context": result}, goto="agent_c")
    return Command(update={"final_result": result}, goto=END)  # END == "__end__"
```

### Dynamic Routing with Command

```python
from typing import Literal
from langgraph.types import Command

def dynamic_router(state: State) -> Command[Literal["option_a", "option_b", "option_c"]]:
    """Dynamic control flow identical to conditional edges."""
    next_node = determine_next_step(state)

    return Command(
        update={"step_completed": True},
        goto=next_node
    )
```

## State-Based Routing Examples

### Confidence-Based Routing

```python
from typing import Literal, TypedDict

class State(TypedDict):
    intent: str
    confidence: float

def route_by_confidence(state: State) -> Literal["high_conf", "medium_conf", "ask_clarification"]:
    if state["confidence"] > 0.8:
        return "high_conf"
    elif state["confidence"] > 0.5:
        return "medium_conf"
    return "ask_clarification"

workflow.add_conditional_edges(
    "classify",
    route_by_confidence,
    {
        "high_conf": "respond",
        "medium_conf": "validate",
        "ask_clarification": "clarify"
    }
)
```

### Task Completion Routing

```python
from typing import Literal

def check_tasks_remaining(state: State) -> Literal["continue", "summarize"]:
    if state["task_list"]:
        return "continue"
    return "summarize"

workflow.add_conditional_edges(
    "execute_task",
    check_tasks_remaining,
    {"continue": "execute_task", "summarize": "summarize"}
)
```

### Error Count Routing

```python
from typing import Literal

def handle_errors(state: State) -> Literal["retry", "reset"]:
    if state["error_count"] > 3:
        return "reset"
    return "retry"

workflow.add_conditional_edges(
    "error_handler",
    handle_errors,
    {"retry": "process", "reset": "start"}
)
```

## CRAG Routing Pattern

Corrective RAG uses routing for document quality:

```python
from typing import Literal

def decide_to_generate(state: CRAGState) -> Literal["generate", "web_search"]:
    """Route based on document relevance."""
    if state["documents"]:
        return "generate"  # Good documents found
    return "web_search"  # Need external search

workflow.add_conditional_edges(
    "grade_documents",
    decide_to_generate,
    {"generate": "generate", "web_search": "web_search"}
)
```

## Multi-Agent Routing

### Supervisor Pattern with add_conditional_edges

```python
from typing import Literal

def supervisor_route(state: SupervisorState) -> Literal["research", "code", "finish"]:
    """LLM decides which agent to use.

    Note: supervisor_llm is a placeholder for your configured LLM instance
    (e.g., ChatAnthropic, ChatOpenAI) with structured output for decisions.
    """
    decision = supervisor_llm.invoke(state["messages"])
    return decision.next_agent  # "research", "code", or "finish"

workflow.add_conditional_edges(
    "supervisor",
    supervisor_route,
    {
        "research": "research_agent",
        "code": "code_agent",
        "finish": END
    }
)
```

### Supervisor Pattern with Command API

```python
from typing import Literal
from langgraph.types import Command

def supervisor(state: SupervisorState) -> Command[Literal["research_agent", "code_agent", "__end__"]]:
    """Supervisor with combined state update and routing."""
    decision = supervisor_llm.invoke(state["messages"])

    return Command(
        update={"supervisor_decision": decision.reasoning},
        goto=decision.next_agent if decision.next_agent != "finish" else END
    )
```

**LLM Model Compatibility**: For LLM-based routing with structured output, use models that support tool calling or structured output, such as `claude-sonnet-4-5-20250929` (Claude) or `gpt-4o` (OpenAI). Configure your LLM with a schema that returns the expected routing decisions.

## Best Practices

### Keep Router Logic Simple

**Good:**
```python
def router(state: State) -> Literal["a", "b"]:
    return "a" if state["x"] > 0 else "b"
```

**Avoid:**
```python
def router(state: State) -> str:
    # Complex nested logic
    if state["x"] > 0:
        if state["y"] > 0:
            if state["z"] > 0:
                return "path1"
            return "path2"
        return "path3"
    return "path4"
```

### Use Descriptive Route Names

**Good:** `high_confidence`, `needs_clarification`, `web_search_required`

**Avoid:** `route1`, `pathA`, `next`

### Type Hints for Visualization

Using `Literal` type hints on router functions improves graph visualization:

```python
# Without Literal - visualization shows edges to ALL nodes
def router(state: State) -> str:
    return "node_a" if state["x"] else "node_b"

# With Literal - visualization shows only possible edges
def router(state: State) -> Literal["node_a", "node_b"]:
    return "node_a" if state["x"] else "node_b"
```

This is especially important when using LangGraph Studio for debugging workflows.

### Document Routing Logic

```python
from typing import Literal

def quality_router(state: State) -> Literal["excellent", "good", "poor"]:
    """
    Route based on document quality:
    - excellent (score > 0.9): direct generation
    - good (score > 0.7): validation then generation
    - poor (score <= 0.7): web search
    """
    score = state["quality_score"]
    if score > 0.9:
        return "excellent"
    elif score > 0.7:
        return "good"
    return "poor"
```

### Handle All Cases

Ensure router covers all possible states:

```python
from typing import Literal

def safe_router(state: State) -> Literal["path_a", "path_b", "default_path"]:
    category = state.get("category", "unknown")
    if category == "A":
        return "path_a"
    elif category == "B":
        return "path_b"
    else:
        return "default_path"  # Always have default
```

### Error Handling in Routers

For production code, handle potential errors when accessing state fields:

```python
from typing import Literal

def robust_router(state: State) -> Literal["success", "error", "default"]:
    """Router with error handling for missing or invalid state fields."""
    try:
        confidence = state["confidence"]
        if not isinstance(confidence, (int, float)):
            return "error"
        if confidence > 0.8:
            return "success"
        return "default"
    except KeyError:
        return "error"  # Handle missing state fields gracefully
    except Exception:
        return "error"  # Catch unexpected errors
```

## Troubleshooting

**Issue:** "Key not found in routing map"

**Solution:** Ensure router function returns only keys in mapping dict, or add default case

**Issue:** Infinite loops

**Solution:** Add loop exit conditions, track iteration counts in state

**Issue:** Router function errors

**Solution:** Add error handling in router, validate state has required fields

**Issue:** Graph visualization shows edges to all nodes

**Solution:** Add `Literal` type hints to router function return type, or provide explicit `path_map`

**Issue:** Send API not working as expected

**Solution:** Ensure you import `Send` from `langgraph.types` (not `langgraph.graph`)

## When to Use Each Approach

| Scenario | Recommended Approach |
|----------|---------------------|
| Simple branching | `add_conditional_edges` with Literal hints |
| State update + routing combined | Command API |
| Dynamic parallel execution (map-reduce) | Send API |
| Static parallel execution | Return `list[str]` from router |
| Multi-agent handoffs | Command API |
| Complex visualization needs | Use `path_map` or Literal hints |

## Additional Resources

### Official Documentation

- [LangGraph Graphs Reference](https://reference.langchain.com/python/langgraph/graphs/) - Complete API documentation for `add_conditional_edges`
- [LangGraph Types Reference](https://reference.langchain.com/python/langgraph/types/) - Send and Command class documentation
- [Command API Blog Post](https://blog.langchain.com/command-a-new-tool-for-multi-agent-architectures-in-langgraph/) - In-depth Command patterns for multi-agent systems
- [LangGraph Graph API Guide](https://docs.langchain.com/oss/python/langgraph/use-graph-api) - Graph API overview covering state, branches, and loops
- [LangGraph Overview](https://docs.langchain.com/oss/python/langgraph/overview) - Main LangGraph documentation hub
