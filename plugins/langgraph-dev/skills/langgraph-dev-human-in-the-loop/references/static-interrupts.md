# Static Interrupts - Debugging Reference

This document covers static interrupts (`interrupt_before` and `interrupt_after`), which are compile-time breakpoints primarily used for debugging and development.

## Table of Contents

- [Overview](#overview)
- [When to Use Static Interrupts](#when-to-use-static-interrupts)
- [interrupt_before](#interrupt_before)
- [interrupt_after](#interrupt_after)
- [Combining Multiple Breakpoints](#combining-multiple-breakpoints)
- [LangGraph Studio Integration](#langgraph-studio-integration)
- [Debugging Workflows](#debugging-workflows)
- [Production Considerations](#production-considerations)

## Overview

**Static interrupts** are **compile-time breakpoints** that pause graph execution before or after specific nodes, regardless of the graph's state. They are configured when compiling the graph and do not require code changes within nodes.

### Static vs Dynamic Interrupts

| Feature | Static Interrupts | Dynamic Interrupts |
|---------|-------------------|-------------------|
| **Configuration** | Compile-time (`interrupt_before`, `interrupt_after`) | Runtime (`interrupt()` function) |
| **Conditional** | No - always triggers | Yes - based on state/logic |
| **Primary use case** | Debugging, development | Production workflows |
| **Requires code changes** | No - just compilation config | Yes - add `interrupt()` calls |
| **Resume value needed** | No - just invoke to continue | Yes - provide value via Command |

### Basic Example

```python
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.graph import StateGraph

# Build graph
graph_builder = StateGraph(State)
graph_builder.add_node("fetch_data", fetch_node)
graph_builder.add_node("process", process_node)
graph_builder.add_node("save", save_node)
graph_builder.add_edge("fetch_data", "process")
graph_builder.add_edge("process", "save")

# Compile with static interrupts
checkpointer = InMemorySaver()
graph = graph_builder.compile(
    interrupt_before=["process"],  # Pause BEFORE process node
    interrupt_after=["save"],       # Pause AFTER save node
    checkpointer=checkpointer       # Required for interrupts
)

# Execute
config = {"configurable": {"thread_id": "debug-1"}}

# Runs until interrupt_before="process"
result = graph.invoke(inputs, config)
print("Paused before process node")

# Resume - runs process, then pauses at interrupt_after="save"
result = graph.invoke(None, config)
print("Paused after save node")

# Resume - completes execution
result = graph.invoke(None, config)
print("Completed")
```

## When to Use Static Interrupts

### ✅ Good Use Cases

1. **Stepping through graph execution**
   - Inspect state at each step during development
   - Verify graph routing logic
   - Debug unexpected behavior

2. **Debugging in LangGraph Studio**
   - Set breakpoints to examine state visually
   - Step through complex workflows
   - Understand control flow

3. **Development and testing**
   - Pause before expensive operations (API calls, database writes)
   - Verify state transformations
   - Test error handling at specific points

### ❌ When NOT to Use

1. **Production workflows**
   - Use dynamic interrupts (`interrupt()`) instead
   - Static interrupts don't provide context or request input
   - They're not conditional on state

2. **Human approval/feedback**
   - Use `interrupt()` to request specific input
   - Static interrupts don't carry custom messages

3. **Conditional pausing**
   - Static interrupts always fire
   - Use `interrupt()` for state-based pausing

## interrupt_before

Pause graph execution **before** a node runs.

### Syntax

```python
graph = builder.compile(
    interrupt_before=["node_name"],  # Single node
    # OR
    interrupt_before=["node1", "node2", "node3"],  # Multiple nodes
    checkpointer=checkpointer
)
```

### Use Cases

**Inspect state before critical operations:**

```python
# Pause before expensive API call
graph = builder.compile(
    interrupt_before=["call_external_api"],
    checkpointer=checkpointer
)

# Examine state
result = graph.invoke(inputs, config)
state = graph.get_state(config)
print(f"State before API call: {state.values}")

# Decide whether to proceed
if state.values["should_call_api"]:
    graph.invoke(None, config)  # Continue
else:
    # Cancel or modify
    graph.update_state(config, {"skip_api": True})
    graph.invoke(None, config)
```

**Debug routing decisions:**

```python
# Pause before conditional routing
graph = builder.compile(
    interrupt_before=["router_node"],
    checkpointer=checkpointer
)

result = graph.invoke(inputs, config)
state = graph.get_state(config)

# Verify routing conditions
print(f"Next node will be: {state.next}")
```

### Execution Flow

```
START → node_a → [PAUSE] → node_b → node_c → END
                    ↑
            interrupt_before=["node_b"]
```

1. Graph executes `node_a`
2. State saved to checkpoint
3. **Pause before `node_b`**
4. Resume: `node_b` executes, then `node_c`

## interrupt_after

Pause graph execution **after** a node completes.

### Syntax

```python
graph = builder.compile(
    interrupt_after=["node_name"],  # Single node
    # OR
    interrupt_after=["node1", "node2"],  # Multiple nodes
    checkpointer=checkpointer
)
```

### Use Cases

**Verify node output:**

```python
# Pause after LLM generation
graph = builder.compile(
    interrupt_after=["llm_generate"],
    checkpointer=checkpointer
)

result = graph.invoke(inputs, config)
state = graph.get_state(config)

# Inspect generated content
print(f"LLM output: {state.values['generated_text']}")

# Modify if needed before continuing
if "inappropriate" in state.values['generated_text']:
    graph.update_state(config, {"generated_text": "[REDACTED]"})

graph.invoke(None, config)  # Continue
```

**Debug state transformations:**

```python
# Pause after each step to verify state
graph = builder.compile(
    interrupt_after=["step1", "step2", "step3"],
    checkpointer=checkpointer
)

for step in ["step1", "step2", "step3"]:
    result = graph.invoke(None if step != "step1" else inputs, config)
    state = graph.get_state(config)
    print(f"After {step}: {state.values}")
```

### Execution Flow

```
START → node_a → [PAUSE] → node_b → END
                    ↑
            interrupt_after=["node_a"]
```

1. Graph executes `node_a`
2. Node completes, state updated
3. **Pause after `node_a`**
4. State saved to checkpoint
5. Resume: `node_b` executes

## Combining Multiple Breakpoints

You can use both `interrupt_before` and `interrupt_after` together, and specify multiple nodes for each.

### Example: Full Debug Mode

```python
graph = builder.compile(
    interrupt_before=["critical_operation"],  # Pause before risky step
    interrupt_after=["fetch", "transform", "validate"],  # Pause after each step
    checkpointer=checkpointer
)
```

### Execution Order

If a node has both `interrupt_before` and `interrupt_after`:

```python
graph = builder.compile(
    interrupt_before=["node_b"],
    interrupt_after=["node_b"],
    checkpointer=checkpointer
)
```

**Execution flow:**
```
node_a → [PAUSE before node_b] → node_b → [PAUSE after node_b] → node_c
```

You'll need to resume **twice** to get past `node_b`:
1. First resume: executes `node_b`
2. Second resume: continues to `node_c`

## LangGraph Studio Integration

[LangGraph Studio](https://github.com/langchain-ai/langgraph-studio) is a visual debugger for LangGraph applications. Static interrupts work seamlessly with Studio.

### Setting Breakpoints in Studio

1. **Visual breakpoints**: Click on nodes in the graph visualization to set breakpoints
2. **Auto-compilation**: Studio automatically adds `interrupt_before` or `interrupt_after`
3. **Step through execution**: Use "Step" button to advance one node at a time
4. **Inspect state**: View graph state at each breakpoint

### Example Studio Workflow

```python
# Your graph code
graph = builder.compile(checkpointer=checkpointer)

# Studio allows you to:
# 1. Set breakpoint on "process_node" visually
# 2. Run graph - pauses at breakpoint
# 3. Inspect state.values in UI
# 4. Click "Continue" or "Step" to proceed
```

### Best Practices with Studio

- **Don't hardcode breakpoints**: Let Studio manage them dynamically
- **Use Studio for exploration**: Understand graph behavior before writing tests
- **Export for CI/CD**: Once debugged, remove breakpoints for production builds

## Debugging Workflows

### Workflow 1: Step-by-Step Debugging

Pause after every node to verify state at each step:

```python
# Get all node names
all_nodes = list(graph_builder._nodes.keys())

# Compile with breakpoints after each node
graph = builder.compile(
    interrupt_after=all_nodes,
    checkpointer=checkpointer
)

config = {"configurable": {"thread_id": "debug"}}
result = graph.invoke(inputs, config)

# Step through each node
while result.get("__interrupt__"):
    state = graph.get_state(config)
    print(f"Paused at: {state.tasks[0].name if state.tasks else 'END'}")
    print(f"State: {state.values}")

    input("Press Enter to continue...")
    result = graph.invoke(None, config)
```

### Workflow 2: Conditional Debugging

Only enable breakpoints in development:

```python
import os

# Environment-based debugging
debug_mode = os.getenv("DEBUG_GRAPH", "false").lower() == "true"

graph = builder.compile(
    interrupt_before=["risky_node"] if debug_mode else [],
    checkpointer=checkpointer
)
```

### Workflow 3: Selective Breakpoints

Set breakpoints only around problematic areas:

```python
# Known issue: node_b sometimes fails
# Pause before and after to diagnose

graph = builder.compile(
    interrupt_before=["node_b"],  # Inspect inputs
    interrupt_after=["node_b"],   # Inspect outputs
    checkpointer=checkpointer
)

config = {"configurable": {"thread_id": "debug"}}

# Before node_b
result = graph.invoke(inputs, config)
state_before = graph.get_state(config)
print("State BEFORE node_b:", state_before.values)

# After node_b
result = graph.invoke(None, config)
state_after = graph.get_state(config)
print("State AFTER node_b:", state_after.values)
```

## Production Considerations

### ❌ Don't Use Static Interrupts in Production

Static interrupts are for **debugging only**. In production:

1. **Use dynamic interrupts (`interrupt()`)** for human-in-the-loop workflows
2. **Remove all static breakpoints** from production builds
3. **Don't rely on static interrupts for control flow**

### Migration: Static → Dynamic

**Before (static - debugging):**
```python
graph = builder.compile(
    interrupt_before=["approval_node"],
    checkpointer=checkpointer
)
```

**After (dynamic - production):**
```python
def approval_node(state: State):
    approved = interrupt({
        "question": "Approve this action?",
        "details": state["action_details"]
    })
    return {"approved": approved}

graph = builder.compile(checkpointer=checkpointer)
```

### Build Configurations

Use separate builds for development and production:

```python
def build_graph(debug: bool = False):
    builder = StateGraph(State)
    # ... add nodes and edges ...

    if debug:
        # Development: enable all breakpoints
        return builder.compile(
            interrupt_after=["step1", "step2", "step3"],
            checkpointer=checkpointer
        )
    else:
        # Production: no static interrupts
        return builder.compile(checkpointer=checkpointer)

# Development
dev_graph = build_graph(debug=True)

# Production
prod_graph = build_graph(debug=False)
```

---

## Summary

- **Static interrupts** (`interrupt_before`, `interrupt_after`) are compile-time breakpoints
- **Primary use case**: Debugging and development, **not production**
- **`interrupt_before`**: Pause before a node executes (inspect inputs)
- **`interrupt_after`**: Pause after a node completes (inspect outputs)
- **LangGraph Studio**: Visual debugger that uses static interrupts
- **Production**: Use dynamic interrupts (`interrupt()`) instead

For dynamic interrupts and production patterns, see `interrupt-patterns.md`.
For complex workflows with tools and subgraphs, see `advanced-workflows.md`.
