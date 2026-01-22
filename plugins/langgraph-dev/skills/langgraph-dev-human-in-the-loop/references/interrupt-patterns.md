# Interrupt Patterns - Complete Reference

This document provides a comprehensive reference for the `interrupt()` function and advanced interrupt patterns in LangGraph.

## Table of Contents

- [How `interrupt()` Works](#how-interrupt-works)
- [Complete API Reference](#complete-api-reference)
- [Serialization Rules](#serialization-rules)
- [State Management](#state-management-during-interrupts)
- [Multiple Interrupts](#multiple-interrupts-in-a-node)
- [Review and Edit Pattern](#review-and-edit-pattern)
- [Multi-Step Validation](#multi-step-validation-pattern)
- [Error Handling](#error-handling-with-interrupts)
- [Thread Management](#thread-management)

## How `interrupt()` Works

Understanding the interrupt mechanism is critical for building robust human-in-the-loop workflows.

### Execution Flow

1. **First call**: `interrupt(value)` raises a `GraphInterrupt` exception
2. **State saved**: LangGraph checkpoints the graph state before the interrupt
3. **Client notified**: The `value` is surfaced to the client via `__interrupt__` key
4. **Execution paused**: The graph halts and waits for resumption
5. **Resumption**: Client calls `graph.invoke(Command(resume=<input>), config)`
6. **Node re-executed**: **Important**: The entire node runs again from the start
7. **Subsequent calls**: `interrupt(value)` returns the resume value instead of raising

### Why Nodes Re-Execute

When you resume from an interrupt, LangGraph **re-runs the entire node**. This design has important implications:

```python
def approval_node(state: State):
    # This code runs TWICE:
    # 1. During initial execution (hits interrupt)
    # 2. During resumption (interrupt returns value)

    print("Preparing action...")  # ⚠️ Executes twice!

    approved = interrupt("Approve?")  # First: raises, Second: returns value

    print("Action approved!")  # Only executes on resumption

    return {"approved": approved}
```

**Best practices:**
- Place interrupts **early** in the node (ideally first operation)
- Make operations **before** the interrupt idempotent
- Avoid expensive computations or side effects before interrupts

## Complete API Reference

### Function Signature

```python
def interrupt(value: Any) -> Any
```

### Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `value` | `Any` | Yes | The value to surface to the client. Must be JSON-serializable. |

### Return Value

- **First invocation**: Raises `GraphInterrupt` exception (does not return)
- **Subsequent invocations** (same task): Returns the value provided during resumption

### Raises

- `GraphInterrupt`: On first invocation, halts execution and surfaces `value` to client

### Example

```python
from langgraph.types import interrupt, Command

def node(state: State):
    # First call: raises GraphInterrupt
    # Second call (after resume): returns the resume value
    user_input = interrupt({
        "prompt": "Enter your name:",
        "context": state["conversation_history"]
    })

    return {"user_name": user_input}

# Initial execution - hits interrupt
result = graph.invoke({"conversation_history": []}, config)
# result['__interrupt__'] = [Interrupt(value={'prompt': '...', ...})]

# Resume with user input
final = graph.invoke(Command(resume="Alice"), config)
# final = {'user_name': 'Alice', ...}
```

## Serialization Rules

Interrupt values must be **JSON-serializable** because they're persisted in the checkpoint.

### ✅ Allowed Types

```python
# Primitives
interrupt("string value")
interrupt(42)
interrupt(3.14)
interrupt(True)
interrupt(None)

# Collections of primitives
interrupt(["item1", "item2", "item3"])
interrupt({"key": "value", "count": 10})

# Nested structures
interrupt({
    "question": "Approve?",
    "details": {
        "action": "delete",
        "target": "database",
        "affected_rows": 1000
    },
    "options": ["approve", "reject", "defer"]
})
```

### ❌ Prohibited Types

```python
# Custom objects (not serializable)
interrupt(MyCustomClass())  # ❌

# Functions
interrupt(lambda x: x + 1)  # ❌

# Complex types
interrupt(datetime.now())  # ❌
interrupt(numpy.array([1, 2, 3]))  # ❌

# File handles
interrupt(open("file.txt"))  # ❌
```

### Workarounds for Complex Types

```python
from datetime import datetime
import json

# Convert to serializable format
dt = datetime.now()
interrupt({
    "timestamp": dt.isoformat(),  # ✅ "2024-01-13T10:30:00"
    "timestamp_unix": dt.timestamp()  # ✅ 1705147800.0
})

# Custom object → dict
class Action:
    def __init__(self, name, params):
        self.name = name
        self.params = params

    def to_dict(self):
        return {"name": self.name, "params": self.params}

action = Action("delete_user", {"user_id": 123})
interrupt(action.to_dict())  # ✅
```

## State Management During Interrupts

### Accessing State

Interrupt values can include state information for human review:

```python
def review_node(state: State):
    edited = interrupt({
        "instruction": "Review this content",
        "draft": state["generated_text"],
        "metadata": {
            "word_count": len(state["generated_text"].split()),
            "model": state["model_used"]
        }
    })
    return {"final_text": edited}
```

### Updating State on Resume

Use `Command` to update state while resuming:

```python
def approval_node(state: State) -> Command[Literal["approved", "rejected"]]:
    decision = interrupt({
        "question": "Approve this proposal?",
        "proposal": state["proposal_text"]
    })

    return Command(
        goto="approved" if decision else "rejected",
        update={
            "approved": decision,
            "reviewed_at": datetime.now().isoformat(),
            "reviewer_notes": "Manually reviewed"
        }
    )

# Resume with state update
graph.invoke(
    Command(resume=True, update={"reviewer_id": "alice"}),
    config
)
```

## Multiple Interrupts in a Node

A single node can have multiple `interrupt()` calls. They are matched **by order**.

### Sequential Interrupts

```python
def multi_step_approval(state: State):
    # First interrupt - matched by index 0
    manager_approved = interrupt({
        "level": "manager",
        "question": "Manager approval?"
    })

    if not manager_approved:
        return {"approved": False}

    # Second interrupt - matched by index 1
    director_approved = interrupt({
        "level": "director",
        "question": "Director approval?"
    })

    return {"approved": director_approved}
```

**Execution flow:**
```python
# Initial run - hits first interrupt
result = graph.invoke(inputs, config)
# result['__interrupt__'][0] - manager approval

# Resume first interrupt
result = graph.invoke(Command(resume=True), config)
# Now hits second interrupt

# Resume second interrupt
final = graph.invoke(Command(resume=True), config)
# Flow complete
```

### Conditional Interrupts

```python
def conditional_approval(state: State):
    if state["amount"] > 10000:
        # Only interrupts for large amounts
        approved = interrupt({
            "question": "Approve large transaction?",
            "amount": state["amount"]
        })

        if not approved:
            return {"status": "rejected"}

    return {"status": "approved"}
```

### Important Rules

1. **Order matters**: Interrupts are matched by the order they appear in code
2. **Don't reorder**: Changing interrupt order breaks resumption
3. **Scope is per-task**: Resume values are scoped to the specific task (node execution)

## Review and Edit Pattern

Allow humans to review and modify content before proceeding.

### Basic Pattern

```python
from langgraph.types import interrupt

def review_content(state: State):
    edited_content = interrupt({
        "instruction": "Review and edit this text",
        "original": state["draft"],
        "suggestions": state.get("ai_suggestions", [])
    })

    return {
        "final_content": edited_content,
        "reviewed": True
    }

# Resume with edited version
graph.invoke(Command(resume="Edited and improved text"), config)
```

### Review with Approval

```python
def review_and_approve(state: State):
    # First: Review and edit
    edited = interrupt({
        "action": "edit",
        "content": state["draft"]
    })

    # Second: Final approval
    approved = interrupt({
        "action": "approve",
        "content": edited
    })

    if approved:
        return {"final_content": edited, "status": "approved"}
    else:
        return {"status": "rejected"}

# Two-step resumption
graph.invoke(Command(resume="Improved text"), config)  # Edit
graph.invoke(Command(resume=True), config)  # Approve
```

## Multi-Step Validation Pattern

Validate user input with retry logic until valid.

### Validation Loop

```python
def get_validated_age(state: State):
    prompt = "What is your age?"

    while True:
        answer = interrupt(prompt)

        # Validation logic
        if isinstance(answer, int) and 0 < answer < 120:
            break  # Valid!
        else:
            # Invalid - update prompt and try again
            prompt = {
                "error": f"Invalid input: '{answer}'",
                "instruction": "Please enter a valid age (1-120)"
            }

    return {"age": answer}
```

**Execution flow:**
```python
# First attempt - invalid
graph.invoke(inputs, config)
graph.invoke(Command(resume="not a number"), config)  # ❌ Invalid

# Second attempt - still invalid
graph.invoke(Command(resume=-5), config)  # ❌ Out of range

# Third attempt - valid
graph.invoke(Command(resume=25), config)  # ✅ Success
```

### Multi-Field Validation

```python
def collect_user_info(state: State):
    fields = {"name": None, "email": None, "age": None}

    for field, validator in [
        ("name", lambda x: isinstance(x, str) and len(x) > 0),
        ("email", lambda x: "@" in x),
        ("age", lambda x: isinstance(x, int) and 0 < x < 120)
    ]:
        prompt = f"Enter your {field}:"

        while True:
            value = interrupt({
                "field": field,
                "prompt": prompt
            })

            if validator(value):
                fields[field] = value
                break
            else:
                prompt = f"Invalid {field}: '{value}'. Try again."

    return {"user_info": fields}
```

## Error Handling with Interrupts

### ❌ DON'T: Wrap interrupt() in try/except

This breaks the interrupt mechanism:

```python
def bad_node(state: State):
    try:
        value = interrupt("Input?")  # ❌ Don't do this!
    except GraphInterrupt:
        value = "default"  # This prevents the interrupt
    return {"value": value}
```

### ✅ DO: Handle errors outside the interrupt

```python
def good_node(state: State):
    # Get input via interrupt
    value = interrupt("Enter value:")

    # Validate and handle errors after
    try:
        processed = process_value(value)
    except ValueError as e:
        return {"error": str(e), "value": None}

    return {"value": processed}
```

### Timeout Handling (Client-Side)

Interrupts don't have built-in timeouts. Implement timeout logic on the client:

```python
import time
from datetime import datetime, timedelta

def wait_for_approval_with_timeout(graph, config, timeout_seconds=3600):
    """Wait for human approval with timeout."""
    start = datetime.now()
    deadline = start + timedelta(seconds=timeout_seconds)

    while datetime.now() < deadline:
        # Check if interrupt is waiting
        state = graph.get_state(config)
        if state.next:  # Still running
            time.sleep(5)
            continue
        elif state.tasks and state.tasks[0].interrupts:
            # Waiting for human input
            return state  # Human can now provide input
        else:
            # Completed
            return state

    # Timeout - cancel the workflow
    raise TimeoutError(f"No approval received within {timeout_seconds}s")
```

## Thread Management

Each graph invocation with a unique `thread_id` creates an independent execution context.

### Thread ID Patterns

```python
import uuid

# Unique thread per conversation
thread_id = f"conversation_{uuid.uuid4()}"

# User-specific threads
thread_id = f"user_{user_id}"

# Session-based threads
thread_id = f"session_{session_id}"

config = {"configurable": {"thread_id": thread_id}}
```

### Concurrent Interrupts

Different threads can have interrupts in progress simultaneously:

```python
# User A's workflow - paused at approval
config_a = {"configurable": {"thread_id": "user_a"}}
graph.invoke(inputs, config_a)  # Hits interrupt

# User B's workflow - independent
config_b = {"configurable": {"thread_id": "user_b"}}
graph.invoke(inputs, config_b)  # Hits interrupt

# Resume User A's workflow
graph.invoke(Command(resume=True), config_a)

# User B's interrupt still pending
```

### Checking Interrupt Status

```python
# Get current state of a thread
state = graph.get_state(config)

# Check if there are pending interrupts
if state.tasks and state.tasks[0].interrupts:
    interrupt_info = state.tasks[0].interrupts[0]
    print(f"Interrupt value: {interrupt_info.value}")
    print(f"Interrupt ID: {interrupt_info.id}")

# Check if graph is still running
if state.next:
    print("Graph is still executing")
else:
    print("Graph completed or paused")
```

---

## Summary

- **`interrupt()`** is the recommended way to pause graph execution (v1.0+)
- **Nodes re-execute** on resume - place interrupts early and keep pre-interrupt operations idempotent
- **Values must be JSON-serializable** - use primitives, dicts, and lists
- **Multiple interrupts** are matched by order - don't reorder them
- **Don't wrap in try/except** - this breaks the interrupt mechanism
- **Use Command for resumption** - provides resume value and optional routing/state updates
- **Thread IDs** enable concurrent workflows with independent interrupt states

For static interrupts and debugging patterns, see `static-interrupts.md`.
For advanced patterns (subgraphs, tools), see `advanced-workflows.md`.
