# Advanced Human-in-the-Loop Workflows

This document covers advanced interrupt patterns including tool approval, subgraph interrupts, multi-step approvals, and complex state editing scenarios.

## Table of Contents

- [Tool Call Approval](#tool-call-approval)
- [Multi-Step Approval Chains](#multi-step-approval-chains)
- [Interrupts in Subgraphs](#interrupts-in-subgraphs)
- [Parallel Workflows with Interrupts](#parallel-workflows-with-interrupts)
- [Complex State Editing](#complex-state-editing)
- [Timeout and Cancellation Patterns](#timeout-and-cancellation-patterns)
- [Audit and Logging](#audit-and-logging)

## Tool Call Approval

Review and approve tool calls before execution - critical for agents using external APIs or making irreversible actions.

### Pattern 1: Approve Before Tool Execution

Interrupt before calling tools to review and approve each call:

```python
from langgraph.types import interrupt
from langgraph.prebuilt import ToolNode

def review_tool_calls(state: State):
    """Review tool calls before execution."""
    messages = state["messages"]
    last_message = messages[-1]

    # Check if LLM requested tool calls
    if not last_message.tool_calls:
        return state

    # Present tool calls for approval
    approved_calls = []

    for tool_call in last_message.tool_calls:
        approval = interrupt({
            "action": "approve_tool",
            "tool_name": tool_call["name"],
            "tool_args": tool_call["args"],
            "reasoning": "Review this tool call before execution"
        })

        if approval:
            approved_calls.append(tool_call)

    # Update message with only approved calls
    if approved_calls:
        last_message.tool_calls = approved_calls
        return {"messages": [last_message]}
    else:
        # No tools approved - send rejection message
        return {
            "messages": [{
                "role": "assistant",
                "content": "Tool execution was rejected by human reviewer."
            }]
        }

# Add to graph
builder.add_node("review_tools", review_tool_calls)
builder.add_node("execute_tools", ToolNode(tools))
builder.add_edge("agent", "review_tools")
builder.add_edge("review_tools", "execute_tools")
```

### Pattern 2: Approve Tool Inside Tool Function

Place interrupt directly in the tool function:

```python
from langchain_core.tools import tool
from langgraph.types import interrupt

@tool
def delete_user(user_id: int) -> str:
    """Delete a user from the database. Requires approval."""

    # Request approval before deletion
    approved = interrupt({
        "action": "confirm_deletion",
        "user_id": user_id,
        "warning": "This action cannot be undone",
        "question": "Delete this user?"
    })

    if not approved:
        return f"Deletion of user {user_id} was cancelled."

    # Proceed with deletion
    database.delete_user(user_id)
    return f"User {user_id} deleted successfully."

# Use with ToolNode - interrupts work inside tools!
tools = [delete_user]
tool_node = ToolNode(tools)
```

### Pattern 3: Bulk Tool Approval

Approve multiple tool calls at once:

```python
def bulk_tool_approval(state: State):
    """Approve all tool calls in one decision."""
    tool_calls = state["messages"][-1].tool_calls

    if not tool_calls:
        return state

    # Present all tools for bulk approval
    approved = interrupt({
        "action": "bulk_approve_tools",
        "tools": [
            {
                "name": tc["name"],
                "args": tc["args"]
            }
            for tc in tool_calls
        ],
        "question": f"Approve all {len(tool_calls)} tool calls?"
    })

    if approved:
        return state  # Execute all
    else:
        return {
            "messages": [{
                "role": "assistant",
                "content": "All tool calls rejected."
            }]
        }
```

## Multi-Step Approval Chains

Implement approval hierarchies where multiple stakeholders must approve before proceeding.

### Pattern: Sequential Approvals

```python
from typing import Literal
from langgraph.types import Command

def multi_level_approval(state: State) -> Command[Literal["approved", "rejected"]]:
    """Require approval from multiple roles."""

    # Level 1: Team Lead
    lead_approved = interrupt({
        "level": "team_lead",
        "question": "Team Lead: Approve this request?",
        "request": state["request_details"]
    })

    if not lead_approved:
        return Command(goto="rejected", update={"rejected_by": "team_lead"})

    # Level 2: Manager
    manager_approved = interrupt({
        "level": "manager",
        "question": "Manager: Approve this request?",
        "request": state["request_details"],
        "previous_approvals": ["team_lead"]
    })

    if not manager_approved:
        return Command(goto="rejected", update={"rejected_by": "manager"})

    # Level 3: Director (only for high-value requests)
    if state["request_value"] > 100000:
        director_approved = interrupt({
            "level": "director",
            "question": "Director: Approve this high-value request?",
            "request": state["request_details"],
            "value": state["request_value"],
            "previous_approvals": ["team_lead", "manager"]
        })

        if not director_approved:
            return Command(goto="rejected", update={"rejected_by": "director"})

    # All approvals obtained
    return Command(goto="approved", update={
        "approval_chain": ["team_lead", "manager", "director"],
        "approved_at": datetime.now().isoformat()
    })
```

### Pattern: Parallel Approvals

Multiple approvers can review simultaneously (requires external coordination):

```python
def parallel_approval_workflow(state: State):
    """Collect approvals from multiple people in parallel.

    Note: This requires client-side coordination to resume
    with a combined decision.
    """

    # Request approval from multiple people
    approvals = interrupt({
        "action": "parallel_approval",
        "approvers": ["alice@example.com", "bob@example.com", "carol@example.com"],
        "question": "Approve this proposal?",
        "proposal": state["proposal"],
        "policy": "require_all"  # or "require_majority"
    })

    # Client must collect all approvals and resume with:
    # Command(resume={"alice": True, "bob": True, "carol": False})

    policy = "require_all"  # or get from state

    if policy == "require_all":
        all_approved = all(approvals.values())
        return {"approved": all_approved}
    elif policy == "require_majority":
        majority = sum(approvals.values()) > len(approvals) / 2
        return {"approved": majority}
```

## Interrupts in Subgraphs

Interrupts work in subgraphs - the parent graph can pause when a child graph interrupts.

### Subgraph with Interrupt

```python
from langgraph.graph import StateGraph

# Child graph with interrupt
def build_approval_subgraph():
    builder = StateGraph(ApprovalState)

    def approval_node(state):
        approved = interrupt("Approve sub-workflow action?")
        return {"approved": approved}

    builder.add_node("approval", approval_node)
    builder.set_entry_point("approval")
    return builder.compile()

# Parent graph
parent_builder = StateGraph(ParentState)

def call_subgraph(state: ParentState):
    subgraph = build_approval_subgraph()

    # Subgraph interrupt propagates to parent
    result = subgraph.invoke({"action": state["action"]})

    return {"subgraph_result": result}

parent_builder.add_node("subgraph", call_subgraph)

# When parent graph runs, it will pause when subgraph hits interrupt
parent_graph = parent_builder.compile(checkpointer=checkpointer)
```

### Subgraph Resume Pattern

```python
# Initial run - hits interrupt in subgraph
result = parent_graph.invoke(inputs, config)

# Interrupt from subgraph is surfaced to parent
print(result["__interrupt__"])  # Contains subgraph interrupt

# Resume parent graph - this resumes the subgraph
final = parent_graph.invoke(Command(resume=True), config)
```

## Parallel Workflows with Interrupts

Using the Send API with interrupts for fan-out/fan-in patterns.

### Pattern: Parallel Processing with Individual Approvals

```python
from langgraph.types import Send

def fan_out(state: State):
    """Send tasks to parallel nodes, each with approval."""
    return [
        Send("process_item", {"item": item})
        for item in state["items"]
    ]

def process_item(state: ItemState):
    """Process item with approval gate."""

    # Each parallel execution can have its own interrupt
    approved = interrupt({
        "action": "approve_item",
        "item": state["item"],
        "question": f"Approve processing of {state['item']['name']}?"
    })

    if approved:
        result = process(state["item"])
        return {"result": result}
    else:
        return {"result": None, "skipped": True}

builder.add_node("fan_out", fan_out)
builder.add_node("process_item", process_item)
builder.add_conditional_edges("fan_out", lambda x: "process_item")
```

**Resumption**: Each parallel task creates its own interrupt. Resume them individually:

```python
# Initial run - creates multiple interrupts (one per item)
result = graph.invoke({"items": [item1, item2, item3]}, config)

# Multiple interrupts in result
print(len(result["__interrupt__"]))  # 3 interrupts

# Resume each individually or all at once
# (LangGraph handles resuming parallel tasks)
graph.invoke(Command(resume=True), config)  # Approve all
```

## Complex State Editing

Advanced patterns for editing graph state during interrupts.

### Pattern: Structured State Updates

```python
def edit_proposal(state: State):
    """Allow structured editing of a proposal."""

    current_proposal = state["proposal"]

    # Present proposal for editing
    edited = interrupt({
        "action": "edit_proposal",
        "current": current_proposal,
        "editable_fields": ["title", "budget", "timeline", "scope"],
        "instruction": "Edit any fields as needed"
    })

    # Merge edited fields with original
    updated_proposal = {**current_proposal, **edited}

    return {"proposal": updated_proposal}

# Resume with partial updates
graph.invoke(
    Command(resume={
        "budget": 50000,  # Only update budget
        "timeline": "Q2 2024"  # and timeline
    }),
    config
)
```

### Pattern: Iterative Refinement

```python
def iterative_content_refinement(state: State):
    """Allow multiple rounds of editing."""

    content = state["draft_content"]
    iteration = 0
    max_iterations = 5

    while iteration < max_iterations:
        feedback = interrupt({
            "action": "review_content",
            "content": content,
            "iteration": iteration + 1,
            "options": ["approve", "edit", "regenerate"]
        })

        if feedback["action"] == "approve":
            break
        elif feedback["action"] == "edit":
            content = feedback["edited_content"]
        elif feedback["action"] == "regenerate":
            content = generate_new_content(state["topic"])

        iteration += 1

    return {"final_content": content, "iterations": iteration}
```

## Timeout and Cancellation Patterns

Handle cases where humans don't respond or workflows need cancellation.

### Pattern: Client-Side Timeout

```python
from datetime import datetime, timedelta

def execute_with_timeout(graph, inputs, config, timeout_hours=24):
    """Execute graph with timeout for human response."""

    # Start execution
    result = graph.invoke(inputs, config)

    if not result.get("__interrupt__"):
        return result  # Completed without interrupt

    # Wait for human response
    deadline = datetime.now() + timedelta(hours=timeout_hours)

    while datetime.now() < deadline:
        # Check if human has provided input
        # (this would be implemented with your UI/API)
        human_input = check_for_human_input()  # Your implementation

        if human_input:
            # Resume with input
            return graph.invoke(
                Command(resume=human_input),
                config
            )

        time.sleep(60)  # Check every minute

    # Timeout - cancel workflow
    return {
        "status": "timeout",
        "message": f"No response within {timeout_hours} hours"
    }
```

### Pattern: Explicit Cancellation Node

```python
def approval_with_cancel(state: State) -> Command[Literal["approved", "cancelled"]]:
    """Approval with explicit cancel option."""

    decision = interrupt({
        "question": "Approve, reject, or cancel this workflow?",
        "options": ["approve", "reject", "cancel"],
        "details": state["action_details"]
    })

    if decision == "approve":
        return Command(goto="approved")
    elif decision == "cancel":
        return Command(goto="cancelled", update={"reason": "User cancelled"})
    else:  # reject
        return Command(goto="rejected", update={"reason": "User rejected"})
```

## Audit and Logging

Track all human interactions for compliance and debugging.

### Pattern: Audit Trail

```python
from datetime import datetime

def approval_with_audit(state: State):
    """Approval with full audit trail."""

    approved = interrupt({
        "action": "approve_transaction",
        "transaction": state["transaction"],
        "timestamp": datetime.now().isoformat()
    })

    # Log the approval decision
    audit_entry = {
        "timestamp": datetime.now().isoformat(),
        "action": "approval",
        "approved": approved,
        "transaction_id": state["transaction"]["id"],
        "user": state.get("reviewer_id", "unknown"),
        "decision": "approved" if approved else "rejected"
    }

    # Append to audit log
    audit_log = state.get("audit_log", [])
    audit_log.append(audit_entry)

    return {
        "approved": approved,
        "audit_log": audit_log
    }
```

### Pattern: Resume Metadata Tracking

```python
def track_resume_metadata(graph, config):
    """Track who resumed and when."""

    # Get current state
    state = graph.get_state(config)

    if state.tasks and state.tasks[0].interrupts:
        interrupt_info = state.tasks[0].interrupts[0]

        # Resume with metadata
        result = graph.invoke(
            Command(
                resume=True,
                update={
                    "resumed_by": "alice@example.com",
                    "resumed_at": datetime.now().isoformat(),
                    "interrupt_id": interrupt_info.id
                }
            ),
            config
        )

        return result
```

---

## Summary

- **Tool approval**: Interrupt before tool execution or inside tool functions
- **Multi-step approvals**: Chain interrupts for approval hierarchies
- **Subgraph interrupts**: Child graph interrupts propagate to parent
- **Parallel workflows**: Each parallel task can have independent interrupts
- **Complex state editing**: Use structured updates and iterative refinement
- **Timeouts**: Implement client-side timeout logic
- **Audit trails**: Track all human interactions for compliance

For basic interrupt patterns, see `interrupt-patterns.md`.
For debugging with static interrupts, see `static-interrupts.md`.
For working code examples, see the `examples/` directory.
