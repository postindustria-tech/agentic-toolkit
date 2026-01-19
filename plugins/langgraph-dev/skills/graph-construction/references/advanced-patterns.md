# Advanced Graph Construction Patterns

This reference provides advanced patterns and techniques for building complex LangGraph workflows.

## Contents

1. [Dynamic Graph Construction](#dynamic-graph-construction)
2. [Nested Conditional Logic](#nested-conditional-logic)
3. [Error Recovery Patterns](#error-recovery-patterns)
4. [State Transformation Patterns](#state-transformation-patterns)
5. [Custom Execution Strategies](#custom-execution-strategies)

---

## Dynamic Graph Construction

### Pattern: Graph Builder Based on Configuration

**Purpose**: Build different graph structures based on runtime configuration.

```python
from langgraph.graph import StateGraph, START, END
from typing import TypedDict, List, Callable

class DynamicState(TypedDict):
    input: str
    steps: List[str]
    result: str

def build_dynamic_graph(steps_config: List[dict]) -> StateGraph:
    """
    Build graph dynamically based on configuration.

    Args:
        steps_config: List of step definitions
            [{"name": "step1", "func": func1}, ...]

    Returns:
        Configured StateGraph ready to compile
    """
    workflow = StateGraph(DynamicState)

    # Add nodes from configuration
    for step in steps_config:
        workflow.add_node(step["name"], step["func"])

    # Add edges: START → step1 → step2 → ... → END
    workflow.add_edge(START, steps_config[0]["name"])

    for i in range(len(steps_config) - 1):
        current = steps_config[i]["name"]
        next_step = steps_config[i + 1]["name"]
        workflow.add_edge(current, next_step)

    workflow.add_edge(steps_config[-1]["name"], END)

    return workflow

# Usage: Configure workflow at runtime
def transform_uppercase(state: DynamicState) -> dict:
    return {"result": state["input"].upper(), "steps": state["steps"] + ["uppercase"]}

def add_prefix(state: DynamicState) -> dict:
    return {"result": f"PREFIX: {state['result']}", "steps": state["steps"] + ["prefix"]}

def add_suffix(state: DynamicState) -> dict:
    return {"result": f"{state['result']} SUFFIX", "steps": state["steps"] + ["suffix"]}

# Build different pipelines based on config
simple_pipeline = [
    {"name": "uppercase", "func": transform_uppercase}
]

full_pipeline = [
    {"name": "uppercase", "func": transform_uppercase},
    {"name": "prefix", "func": add_prefix},
    {"name": "suffix", "func": add_suffix}
]

# Create graphs from configurations
simple_graph = build_dynamic_graph(simple_pipeline).compile()
full_graph = build_dynamic_graph(full_pipeline).compile()
```

**Key Points**:
- Graph structure determined at runtime
- Enables configuration-driven workflows
- Useful for multi-tenant systems with different requirements
- Validate configuration before building

---

## Nested Conditional Logic

### Pattern: Multi-Level Decision Trees

**Purpose**: Complex routing with nested conditions and fallbacks.

```python
from typing import Literal

class ComplexState(TypedDict):
    user_type: str  # "premium", "standard", "trial"
    request_type: str  # "query", "command", "admin"
    complexity: str  # "simple", "complex"
    result: str

# First-level routing: by user type
UserRoute = Literal["premium_path", "standard_path", "trial_path"]

def route_by_user(state: ComplexState) -> UserRoute:
    """First level: Route by user tier."""
    user_type = state.get("user_type", "trial")

    routing = {
        "premium": "premium_path",
        "standard": "standard_path",
        "trial": "trial_path"
    }

    return routing.get(user_type, "trial_path")  # type: ignore

# Second-level routing: by request type (premium users only)
PremiumRoute = Literal["premium_query", "premium_admin", "premium_command"]

def route_premium_request(state: ComplexState) -> PremiumRoute:
    """Second level: Route premium users by request type."""
    request_type = state.get("request_type", "query")

    routing = {
        "query": "premium_query",
        "command": "premium_command",
        "admin": "premium_admin"
    }

    return routing.get(request_type, "premium_query")  # type: ignore

# Third-level routing: by complexity (for queries)
ComplexityRoute = Literal["simple_query", "complex_query"]

def route_by_complexity(state: ComplexState) -> ComplexityRoute:
    """Third level: Route queries by complexity."""
    if state.get("complexity") == "complex":
        return "complex_query"
    return "simple_query"

# Build nested graph
def create_nested_conditional_graph():
    workflow = StateGraph(ComplexState)

    # Add all nodes
    workflow.add_node("premium_path", lambda s: {"result": "Premium processing"})
    workflow.add_node("standard_path", lambda s: {"result": "Standard processing"})
    workflow.add_node("trial_path", lambda s: {"result": "Trial processing"})

    workflow.add_node("premium_query", lambda s: {"result": "Premium query handler"})
    workflow.add_node("premium_command", lambda s: {"result": "Premium command handler"})
    workflow.add_node("premium_admin", lambda s: {"result": "Premium admin handler"})

    workflow.add_node("simple_query", lambda s: {"result": "Simple query result"})
    workflow.add_node("complex_query", lambda s: {"result": "Complex query result"})

    # Level 1: User type routing
    workflow.add_edge(START, "route_user")  # Assume route_user node exists
    workflow.add_conditional_edges(
        "route_user",
        route_by_user,
        {
            "premium_path": "route_premium",
            "standard_path": "standard_path",
            "trial_path": "trial_path"
        }
    )

    # Level 2: Premium request type routing
    workflow.add_conditional_edges(
        "route_premium",
        route_premium_request,
        {
            "premium_query": "route_complexity",
            "premium_command": "premium_command",
            "premium_admin": "premium_admin"
        }
    )

    # Level 3: Query complexity routing
    workflow.add_conditional_edges(
        "route_complexity",
        route_by_complexity,
        {
            "simple_query": "simple_query",
            "complex_query": "complex_query"
        }
    )

    # All paths eventually reach END
    for node in ["standard_path", "trial_path", "premium_command", "premium_admin", "simple_query", "complex_query"]:
        workflow.add_edge(node, END)

    return workflow.compile()
```

**Key Points**:
- Each routing level handles one concern
- Clear separation of routing logic
- Type-safe with Literal types
- Fallbacks at each level prevent errors

---

## Error Recovery Patterns

### Pattern: Automatic Retry with State Tracking

**Purpose**: Retry failed nodes without manual intervention.

```python
class RetryState(TypedDict):
    input: str
    attempts: int
    max_retries: int
    error: str
    result: str

def risky_operation(state: RetryState) -> dict:
    """
    Operation that might fail.

    Simulates intermittent failures for demonstration.
    """
    import random

    attempts = state.get("attempts", 0) + 1

    # Simulate 50% failure rate
    if random.random() < 0.5 and attempts < state["max_retries"]:
        return {
            "error": f"Operation failed (attempt {attempts})",
            "attempts": attempts
        }
    else:
        return {
            "result": f"Success after {attempts} attempts",
            "attempts": attempts,
            "error": ""
        }

RetryRoute = Literal["retry", "success", "failed"]

def should_retry(state: RetryState) -> RetryRoute:
    """
    Decide whether to retry based on attempts and error state.

    Routes:
    - retry: Error present and attempts < max_retries
    - success: No error
    - failed: Exceeded max_retries
    """
    if not state.get("error"):
        return "success"

    if state.get("attempts", 0) < state.get("max_retries", 3):
        return "retry"

    return "failed"

# Build retry graph
def create_retry_graph():
    workflow = StateGraph(RetryState)

    workflow.add_node("operation", risky_operation)
    workflow.add_node("success_handler", lambda s: {"result": f"Completed: {s['result']}"})
    workflow.add_node("failure_handler", lambda s: {"result": f"Failed after {s['attempts']} attempts"})

    workflow.add_edge(START, "operation")

    workflow.add_conditional_edges(
        "operation",
        should_retry,
        {
            "retry": "operation",  # Loop back for retry
            "success": "success_handler",
            "failed": "failure_handler"
        }
    )

    workflow.add_edge("success_handler", END)
    workflow.add_edge("failure_handler", END)

    return workflow.compile()
```

**Key Points**:
- State tracks retry attempts
- Max retries prevent infinite loops
- Separate handlers for success and failure
- Self-healing pattern for transient failures

---

## State Transformation Patterns

### Pattern: State Reducer Functions

**Purpose**: Complex state transformations with custom logic.

```python
from typing import Annotated

def merge_with_dedup(existing: List[str], new: List[str]) -> List[str]:
    """
    Custom reducer: merge lists and remove duplicates.

    Preserves order of existing items, appends new unique items.
    """
    result = existing.copy()
    for item in new:
        if item not in result:
            result.append(item)
    return result

def accumulate_with_limit(existing: List, new: List, limit: int = 100) -> List:
    """
    Custom reducer: accumulate with maximum size limit.

    Keeps most recent items when limit exceeded.
    """
    combined = existing + new
    if len(combined) > limit:
        return combined[-limit:]  # Keep last N items
    return combined

class AdvancedState(TypedDict):
    unique_items: Annotated[List[str], merge_with_dedup]
    recent_events: Annotated[List[dict], lambda e, n: accumulate_with_limit(e, n, limit=50)]

# Nodes can now update these fields with automatic reduction
def node_with_reducers(state: AdvancedState) -> dict:
    return {
        "unique_items": ["new1", "new2"],  # Will merge with dedup
        "recent_events": [{"event": "action"}]  # Will accumulate with limit
    }
```

**Key Points**:
- Reducers enable complex merge logic
- Useful for accumulating results from multiple nodes
- Can implement business rules in reducers
- More maintainable than manual merging in nodes

---

## Custom Execution Strategies

### Pattern: Conditional Subgraph Execution

**Purpose**: Execute entire subgraphs conditionally.

```python
def create_conditional_subgraph_system():
    """
    System with optional subgraph execution.

    Subgraph is only executed if conditions are met.
    """

    # Subgraph for advanced processing
    def create_advanced_processor():
        sub_workflow = StateGraph(DynamicState)

        sub_workflow.add_node("preprocess", lambda s: {"result": f"Pre: {s['input']}"})
        sub_workflow.add_node("analyze", lambda s: {"result": f"Analyzed: {s['result']}"})
        sub_workflow.add_node("postprocess", lambda s: {"result": f"Post: {s['result']}"})

        sub_workflow.add_edge(START, "preprocess")
        sub_workflow.add_edge("preprocess", "analyze")
        sub_workflow.add_edge("analyze", "postprocess")
        sub_workflow.add_edge("postprocess", END)

        return sub_workflow.compile()

    advanced_processor = create_advanced_processor()

    # Main graph with conditional subgraph
    main_workflow = StateGraph(DynamicState)

    def check_complexity(state: DynamicState) -> dict:
        """Determine if input needs advanced processing."""
        needs_advanced = len(state["input"]) > 10
        return {"needs_advanced": needs_advanced}

    def simple_processor(state: DynamicState) -> dict:
        """Simple processing path."""
        return {"result": f"Simple: {state['input']}"}

    def advanced_processor_wrapper(state: DynamicState) -> dict:
        """Wrapper to call subgraph."""
        result = advanced_processor.invoke(state)
        return {"result": result["result"]}

    # Add nodes
    main_workflow.add_node("check", check_complexity)
    main_workflow.add_node("simple", simple_processor)
    main_workflow.add_node("advanced", advanced_processor_wrapper)

    # Route based on complexity
    main_workflow.add_edge(START, "check")
    main_workflow.add_conditional_edges(
        "check",
        lambda s: "advanced" if s.get("needs_advanced") else "simple",
        {"advanced": "advanced", "simple": "simple"}
    )

    main_workflow.add_edge("simple", END)
    main_workflow.add_edge("advanced", END)

    return main_workflow.compile()
```

**Key Points**:
- Subgraphs are first-class nodes
- Can be conditionally executed
- Enables modular, reusable workflow components
- Clear separation of concerns

---

## Pattern Selection Guide

| Pattern | Use Case | Complexity | Flexibility |
|---------|----------|------------|-------------|
| **Dynamic Construction** | Multi-tenant, configurable workflows | Medium | Very High |
| **Nested Conditionals** | Complex business rules | High | Medium |
| **Auto Retry** | Unreliable operations | Low | Low |
| **Custom Reducers** | Complex state merging | Medium | High |
| **Conditional Subgraphs** | Modular workflows | High | Very High |

---

## Best Practices

1. **Keep routing functions pure**: No side effects in router functions
2. **Document routing logic**: Complex conditionals need clear comments
3. **Validate state transitions**: Check state is valid at each step
4. **Use type hints**: Literal types prevent routing errors
5. **Test edge cases**: Verify all routing paths work correctly
6. **Limit nesting depth**: 3-4 levels maximum for maintainability
7. **Centralize configuration**: Don't hardcode workflow structure

---

## References

- See `SKILL.md` for basic graph construction
- See `examples/` for working demonstrations
- LangGraph Patterns: https://docs.langchain.com/oss/python/langgraph/patterns
- StateGraph API: https://reference.langchain.com/python/langgraph/graphs/
