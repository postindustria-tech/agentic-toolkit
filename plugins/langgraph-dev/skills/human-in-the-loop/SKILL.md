---
name: human-in-the-loop
description: This skill should be used when the user asks about "human-in-the-loop", "interrupt", "interrupt()", "interrupt_before", "interrupt_after", "breakpoints", "approval workflow", "human feedback", "review workflow", "wait for input", "pause execution", "resume execution", "Command API", "state editing", "human approval", "validate input", or needs guidance on implementing human-in-the-loop patterns with LangGraph.
version: 0.1.0
---

# Human-in-the-Loop with LangGraph

Enable human intervention at any point in your LangGraph workflow for approval gates, content review, input validation, and feedback loops. Human-in-the-loop is a core LangGraph differentiator that allows indefinite pauses with persistent state, making it ideal for production agents requiring human oversight.

## When to Use This Pattern

- **Approval gates**: Pause before critical actions (API calls, database writes, financial transactions)
- **Content review**: Allow humans to review and edit LLM-generated content before proceeding
- **Tool approval**: Review tool calls before execution
- **Input validation**: Validate user input in multi-turn conversations
- **Feedback loops**: Incorporate human feedback to guide agent behavior

## Core Concepts

### Dynamic Interrupts with `interrupt()`

**Dynamic interrupts** (recommended for production) pause graph execution from within a node based on the current state. Use the `interrupt()` function to request human input, which gets surfaced to the client. The graph remains paused until resumed with a value via the `Command` primitive.

```python
from langgraph.types import interrupt, Command
from langgraph.checkpoint.memory import InMemorySaver

def approval_node(state: State):
    # Pause and request approval
    approved = interrupt({
        "question": "Do you approve this action?",
        "details": state["action_details"]
    })
    return {"approved": approved}

# Compile with checkpointer (required for interrupts)
memory = InMemorySaver()
graph = workflow.compile(checkpointer=memory)

# Initial run - hits interrupt
config = {"configurable": {"thread_id": "thread-1"}}
result = graph.invoke({"action_details": "..."}, config=config)

# Resume with human decision
graph.invoke(Command(resume=True), config=config)
```

**Requirements:**
- ✅ Must enable a **checkpointer** (e.g., `InMemorySaver`, `SqliteSaver`)
- ✅ Must provide a **thread_id** in config
- ✅ Resume with `Command(resume=<value>)`

**How it works:**
1. When `interrupt()` is called, it raises a `GraphInterrupt` exception
2. The graph saves state and pauses execution
3. The interrupt value is returned to the client in `result['__interrupt__']`
4. Resume execution by invoking the graph with `Command(resume=<value>)`
5. **The node re-executes from the start** with the resume value

### Resuming with the Command Primitive

Use the `Command` primitive to resume execution and optionally route to different nodes:

```python
from typing import Literal
from langgraph.types import Command

def approval_node(state: State) -> Command[Literal["approved", "rejected"]]:
    is_approved = interrupt({
        "question": "Approve this action?",
        "action": state["proposed_action"]
    })

    if is_approved:
        return Command(goto="approved", update={"status": "approved"})
    else:
        return Command(goto="rejected", update={"status": "rejected"})

# Resume with approval decision
graph.invoke(Command(resume=True), config=config)  # Approved path
graph.invoke(Command(resume=False), config=config)  # Rejected path
```

**Command features:**
- `resume=<value>`: Provides the value to resume the interrupt
- `goto=<node>`: Routes to a specific node (conditional routing)
- `update={...}`: Updates the graph state

### Static Interrupts (Debugging Only)

**Static interrupts** (`interrupt_before`, `interrupt_after`) are compile-time breakpoints primarily for debugging. They pause at pre-defined nodes regardless of state.

```python
# Compile with static interrupts (for debugging)
graph = workflow.compile(
    interrupt_before=["approval_node"],  # Pause before this node
    interrupt_after=["review_node"],     # Pause after this node
    checkpointer=memory
)

# Run until breakpoint
graph.invoke(inputs, config=config)

# Resume execution (no value needed)
graph.invoke(None, config=config)
```

**When to use:**
- ✅ **Debugging**: Step through graph execution in development
- ✅ **LangGraph Studio**: Inspect state at specific points
- ❌ **Production**: Use dynamic interrupts (`interrupt()`) instead

## Common Patterns

### 1. Approve or Reject Action

Pause before a critical step and route based on human decision:

```python
def approval_gate(state: State) -> Command[Literal["execute", "cancel"]]:
    approved = interrupt({
        "action": "delete_database",
        "warning": "This action cannot be undone"
    })

    return Command(
        goto="execute" if approved else "cancel",
        update={"approved": approved}
    )
```

### 2. Review and Edit Content

Allow humans to review and modify generated content:

```python
def review_content(state: State):
    edited_text = interrupt({
        "instruction": "Review and edit this content",
        "draft": state["generated_text"]
    })
    return {"final_text": edited_text}

# Resume with edited version
graph.invoke(Command(resume="Improved and edited content"), config)
```

### 3. Validate User Input

Request and validate human input with retry logic:

```python
def get_age(state: State):
    prompt = "What is your age?"

    while True:
        answer = interrupt(prompt)

        if isinstance(answer, int) and answer > 0:
            break
        else:
            prompt = f"Invalid: '{answer}'. Enter a positive number."

    return {"age": answer}
```

### 4. Review Tool Calls

Pause to review tool calls before execution (see `references/advanced-workflows.md` for details).

## Best Practices

### ✅ DO

- **Use dynamic interrupts for production**: `interrupt()` provides full control over when to pause
- **Place interrupts at node start**: Nodes re-execute on resume, so interrupts should be early
- **Keep resume values JSON-serializable**: Interrupts must be persistable
- **Make pre-interrupt operations idempotent**: Since nodes re-execute, avoid side effects before interrupts
- **Provide context in interrupt values**: Include enough information for humans to make informed decisions

### ❌ DON'T

- **Don't wrap `interrupt()` in try/except**: This breaks the interrupt mechanism
- **Don't reorder interrupt calls**: Multiple interrupts in a node are matched by order
- **Don't use complex objects as resume values**: Stick to primitives, dicts, lists
- **Don't use static interrupts in production**: They're for debugging only
- **Don't forget the checkpointer**: Interrupts require persistence to work

## Compatibility

This skill is compatible with **LangGraph v1.0+** (tested with v1.0.5).

**Version-specific notes:**
- `interrupt()` function: Requires LangGraph >= 0.2.31
- `NodeInterrupt`: Deprecated as of v1.0, use `interrupt()` instead
- `__interrupt__` in invoke/stream: Added in v0.4.0
- Dynamic interrupts: Require a checkpointer (any version)
- Static interrupts: Available since v0.2.0

## Additional Resources

### Official Documentation
- [Human-in-the-loop concepts](https://langchain-ai.github.io/langgraph/concepts/human_in_the_loop/)
- [Enable human intervention guide](https://langchain-ai.github.io/langgraph/how-tos/human_in_the_loop/add-human-in-the-loop/)
- [interrupt() API reference](https://langchain-ai.github.io/langgraph/reference/types/#langgraph.types.interrupt)
- [Command API reference](https://langchain-ai.github.io/langgraph/reference/types/#langgraph.types.Command)

### Related Skills
- **graph-construction**: Building LangGraph workflows
- **state-management**: Managing graph state and reducers
- **conditional-routing**: Using Command API for routing
- **conversation-memory**: Checkpointers and persistence

### Advanced Topics
- See `references/interrupt-patterns.md` for complete interrupt() API details
- See `references/static-interrupts.md` for debugging with breakpoints
- See `references/advanced-workflows.md` for complex patterns (subgraphs, tools, multi-step approvals)
- See `examples/` directory for working code samples
