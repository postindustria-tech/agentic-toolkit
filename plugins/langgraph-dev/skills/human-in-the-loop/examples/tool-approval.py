"""
Tool Approval Example

This example demonstrates using interrupts inside tool functions to
request approval before executing critical operations.

Run this example:
    python examples/tool-approval.py
"""

from typing import TypedDict, Annotated
import uuid

from langchain_core.tools import tool
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.constants import START
from langgraph.graph import StateGraph, add_messages
from langgraph.prebuilt import ToolNode
from langgraph.types import interrupt, Command


# Define the graph state
class State(TypedDict):
    """State schema with messages for tool calling."""
    messages: Annotated[list, add_messages]


# Define tools with interrupt-based approval

@tool
def read_file(filename: str) -> str:
    """Read a file from the filesystem. Safe operation, no approval needed."""
    print(f"\n📖 Reading file: {filename}")
    # Simulate file reading
    return f"Contents of {filename}: [file data here]"


@tool
def delete_file(filename: str) -> str:
    """
    Delete a file from the filesystem.

    This is a destructive operation that requires human approval.
    """
    print(f"\n⚠️ Destructive operation requested: delete_file({filename})")
    print("   Requesting approval...")

    # Pause for approval
    approved = interrupt({
        "action": "delete_file",
        "filename": filename,
        "question": f"Approve deletion of '{filename}'?",
        "warning": "This action cannot be undone."
    })

    if approved:
        print(f"✅ Approved! Deleting {filename}...")
        # Simulate deletion
        return f"Successfully deleted {filename}"
    else:
        print(f"❌ Rejected! Keeping {filename}")
        return f"Deletion of {filename} was cancelled by user."


@tool
def send_email(recipient: str, subject: str, body: str) -> str:
    """
    Send an email. Requires approval to prevent spam.
    """
    print(f"\n📧 Email operation requested")
    print(f"   To: {recipient}")
    print(f"   Subject: {subject}")
    print("   Requesting approval...")

    # Pause for approval with email details
    approved = interrupt({
        "action": "send_email",
        "recipient": recipient,
        "subject": subject,
        "body_preview": body[:100] + "..." if len(body) > 100 else body,
        "question": "Approve sending this email?"
    })

    if approved:
        print(f"✅ Approved! Sending email to {recipient}...")
        # Simulate sending
        return f"Email sent successfully to {recipient}"
    else:
        print(f"❌ Rejected! Email not sent")
        return f"Email to {recipient} was cancelled by user."


# Tool list
tools = [read_file, delete_file, send_email]


def create_tool_calling_agent():
    """Create a simple tool-calling workflow."""
    builder = StateGraph(State)

    # Tool node
    tool_node = ToolNode(tools)
    builder.add_node("tools", tool_node)

    def should_continue(state: State) -> str:
        """Check if we should continue or end."""
        messages = state["messages"]
        last_message = messages[-1]

        # If the last message has tool calls, execute them
        if hasattr(last_message, "tool_calls") and last_message.tool_calls:
            return "tools"
        else:
            return "end"

    # Simple agent node that just routes to tools
    def agent(state: State):
        """Placeholder agent - in real scenario, this would call an LLM."""
        # For this example, we'll simulate tool calls directly
        return state

    builder.add_node("agent", agent)
    builder.add_edge(START, "agent")
    builder.add_conditional_edges(
        "agent",
        should_continue,
        {"tools": "tools", "end": "__end__"}
    )
    builder.add_edge("tools", "agent")

    # Compile with checkpointer (required for interrupts in tools)
    checkpointer = InMemorySaver()
    return builder.compile(checkpointer=checkpointer)


def main():
    """Run the tool approval example."""
    graph = create_tool_calling_agent()

    # Create a unique thread ID for this execution
    thread_id = f"tool-approval-{uuid.uuid4()}"
    config = {"configurable": {"thread_id": thread_id}}

    print("=" * 60)
    print("TOOL APPROVAL EXAMPLE")
    print("=" * 60)
    print("\nThis example demonstrates interrupts inside tool functions.")

    # Test 1: Safe operation (read_file) - no approval needed
    print("\n" + "=" * 60)
    print("TEST 1: Safe operation (read_file)")
    print("=" * 60)

    from langchain_core.messages import HumanMessage, AIMessage

    messages = [
        HumanMessage(content="Read the config file"),
        AIMessage(
            content="",
            tool_calls=[{
                "name": "read_file",
                "args": {"filename": "config.json"},
                "id": "call_1"
            }]
        )
    ]

    result = graph.invoke({"messages": messages}, config=config)

    if "__interrupt__" in result:
        print("\n❗ Unexpected interrupt for safe operation")
    else:
        print("\n✅ Safe operation completed without approval")
        print(f"   Result: {result['messages'][-1].content}")

    # Test 2: Destructive operation (delete_file) - requires approval
    print("\n" + "=" * 60)
    print("TEST 2: Destructive operation (delete_file)")
    print("=" * 60)

    thread_id_2 = f"tool-approval-{uuid.uuid4()}"
    config_2 = {"configurable": {"thread_id": thread_id_2}}

    messages_2 = [
        HumanMessage(content="Delete old_data.csv"),
        AIMessage(
            content="",
            tool_calls=[{
                "name": "delete_file",
                "args": {"filename": "old_data.csv"},
                "id": "call_2"
            }]
        )
    ]

    result = graph.invoke({"messages": messages_2}, config=config_2)

    if "__interrupt__" in result:
        print(f"\n📋 Interrupt Info:")
        interrupt_info = result["__interrupt__"][0]
        print(f"   Action: {interrupt_info.value['action']}")
        print(f"   Filename: {interrupt_info.value['filename']}")
        print(f"   Question: {interrupt_info.value['question']}")
        print(f"   Warning: {interrupt_info.value['warning']}")

        # Simulate approval
        print("\n[Decision] Approving deletion...")
        final_result = graph.invoke(
            Command(resume=True),
            config=config_2
        )

        print(f"\n✅ Operation completed!")
        print(f"   Result: {final_result['messages'][-1].content}")
    else:
        print("\n❗ Expected interrupt for destructive operation")

    # Test 3: Rejection scenario
    print("\n" + "=" * 60)
    print("TEST 3: Rejection scenario (send_email)")
    print("=" * 60)

    thread_id_3 = f"tool-approval-{uuid.uuid4()}"
    config_3 = {"configurable": {"thread_id": thread_id_3}}

    messages_3 = [
        HumanMessage(content="Send email to team"),
        AIMessage(
            content="",
            tool_calls=[{
                "name": "send_email",
                "args": {
                    "recipient": "team@example.com",
                    "subject": "Important Update",
                    "body": "Please review the latest changes..."
                },
                "id": "call_3"
            }]
        )
    ]

    result = graph.invoke({"messages": messages_3}, config=config_3)

    if "__interrupt__" in result:
        print(f"\n📋 Interrupt Info:")
        interrupt_info = result["__interrupt__"][0]
        print(f"   Action: {interrupt_info.value['action']}")
        print(f"   Recipient: {interrupt_info.value['recipient']}")
        print(f"   Subject: {interrupt_info.value['subject']}")

        # Simulate rejection
        print("\n[Decision] Rejecting email send...")
        final_result = graph.invoke(
            Command(resume=False),
            config=config_3
        )

        print(f"\n🛑 Operation cancelled!")
        print(f"   Result: {final_result['messages'][-1].content}")
    else:
        print("\n❗ Expected interrupt for email operation")

    print("\n" + "=" * 60)
    print("\n✅ All tests completed!")
    print("\nKey Takeaway: Interrupts work inside tool functions,")
    print("allowing fine-grained control over tool execution.")
    print("=" * 60)


if __name__ == "__main__":
    main()
