"""
Basic Approval Workflow Example

This example demonstrates a simple approval gate pattern where the graph
pauses before a critical action to request human approval.

Run this example:
    python examples/approval-workflow.py
"""

from typing import Literal, TypedDict
import uuid

from langgraph.checkpoint.memory import InMemorySaver
from langgraph.constants import START, END
from langgraph.graph import StateGraph
from langgraph.types import interrupt, Command


# Define the graph state
class State(TypedDict):
    """State schema for the approval workflow."""
    action_description: str
    approved: bool
    result: str


def prepare_action(state: State) -> State:
    """Prepare the action that will require approval."""
    print(f"Preparing action: {state['action_description']}")
    return state


def approval_gate(state: State) -> Command[Literal["execute", "cancel"]]:
    """
    Human approval gate.

    Pauses the graph to request approval. Based on the decision,
    routes to either execute the action or cancel it.
    """
    print("\n🚦 Approval Required!")
    print(f"Action: {state['action_description']}")
    print("Waiting for human decision...")

    # Pause and request approval
    approved = interrupt({
        "question": "Do you approve this action?",
        "action": state["action_description"],
        "warning": "This action will be executed immediately if approved."
    })

    # Route based on approval decision
    if approved:
        print("✅ Action approved!")
        return Command(goto="execute", update={"approved": True})
    else:
        print("❌ Action rejected!")
        return Command(goto="cancel", update={"approved": False})


def execute_action(state: State) -> State:
    """Execute the approved action."""
    print(f"\n⚡ Executing: {state['action_description']}")
    return {"result": "Action completed successfully!"}


def cancel_action(state: State) -> State:
    """Cancel the action."""
    print(f"\n🛑 Cancelled: {state['action_description']}")
    return {"result": "Action was cancelled by user."}


# Build the graph
def build_approval_workflow():
    """Build the approval workflow graph."""
    builder = StateGraph(State)

    # Add nodes
    builder.add_node("prepare", prepare_action)
    builder.add_node("approval", approval_gate)
    builder.add_node("execute", execute_action)
    builder.add_node("cancel", cancel_action)

    # Define edges
    builder.add_edge(START, "prepare")
    builder.add_edge("prepare", "approval")
    # Conditional edges handled by Command in approval_gate
    builder.add_edge("execute", END)
    builder.add_edge("cancel", END)

    # Compile with checkpointer (required for interrupts)
    checkpointer = InMemorySaver()
    return builder.compile(checkpointer=checkpointer)


def main():
    """Run the approval workflow example."""
    graph = build_approval_workflow()

    # Create a unique thread ID for this execution
    thread_id = f"approval-{uuid.uuid4()}"
    config = {"configurable": {"thread_id": thread_id}}

    print("=" * 60)
    print("APPROVAL WORKFLOW EXAMPLE")
    print("=" * 60)

    # Initial run - will hit the interrupt
    print("\n[1] Initial execution - running until approval gate...")
    result = graph.invoke({
        "action_description": "Delete all temporary files older than 30 days",
        "approved": False,
        "result": ""
    }, config=config)

    # Check if we hit an interrupt
    if "__interrupt__" in result:
        print(f"\n📋 Interrupt Info:")
        interrupt_info = result["__interrupt__"][0]
        print(f"   Question: {interrupt_info.value['question']}")
        print(f"   Action: {interrupt_info.value['action']}")
        print(f"   Warning: {interrupt_info.value['warning']}")

        # Simulate human decision
        print("\n[2] Resuming with approval decision...")
        user_decision = True  # Change to False to reject

        print(f"   Human Decision: {'APPROVE' if user_decision else 'REJECT'}")

        # Resume the graph with the decision
        final_result = graph.invoke(
            Command(resume=user_decision),
            config=config
        )

        print(f"\n🎯 Final Result: {final_result['result']}")
        print(f"   Approved: {final_result['approved']}")
    else:
        print("\n❗ No interrupt encountered (unexpected)")

    print("\n" + "=" * 60)


if __name__ == "__main__":
    main()
