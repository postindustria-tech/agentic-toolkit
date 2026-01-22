"""
Thread Management Example

This example demonstrates thread isolation and multi-user management
using a simple customer support chatbot scenario.

Run this example:
    python examples/thread-management.py
"""

from typing import Annotated
from typing_extensions import TypedDict
from langgraph.graph import StateGraph, add_messages, START, END
from langgraph.checkpoint.memory import InMemorySaver


# Define state with message history
class SupportState(TypedDict):
    """State for customer support conversation."""
    messages: Annotated[list, add_messages]
    customer_name: str
    ticket_id: str


def greet_customer(state: SupportState) -> dict:
    """Greet the customer and acknowledge their message."""
    messages = state["messages"]
    last_message = messages[-1] if messages else None

    # Simple greeting logic
    if last_message and ("hello" in last_message.content.lower() or "hi" in last_message.content.lower()):
        response = f"Hello {state['customer_name']}! I'm here to help you with ticket #{state['ticket_id']}. How can I assist you today?"
    else:
        response = f"Thank you for contacting support, {state['customer_name']}. I see you're inquiring about ticket #{state['ticket_id']}. Let me help you with that."

    from langchain_core.messages import AIMessage
    return {"messages": [AIMessage(content=response)]}


def handle_query(state: SupportState) -> dict:
    """Handle customer query."""
    messages = state["messages"]
    last_message = messages[-1] if messages else None

    # Simulate simple query handling
    query = last_message.content.lower() if last_message else ""

    if "status" in query:
        response = f"Your ticket #{state['ticket_id']} is currently being processed. Our team is working on it."
    elif "cancel" in query:
        response = f"I understand you'd like to cancel. Let me help you with that for ticket #{state['ticket_id']}."
    elif "question" in query or "?" in query:
        response = f"That's a great question about ticket #{state['ticket_id']}! Let me find that information for you."
    else:
        response = f"I've noted your message regarding ticket #{state['ticket_id']}. Is there anything specific I can help you with?"

    from langchain_core.messages import AIMessage
    return {"messages": [AIMessage(content=response)]}


def build_support_graph():
    """Build customer support chatbot graph."""
    builder = StateGraph(SupportState)

    # Add nodes
    builder.add_node("greet", greet_customer)
    builder.add_node("handle", handle_query)

    # Simple flow: greet -> handle -> end
    builder.add_edge(START, "greet")
    builder.add_edge("greet", "handle")
    builder.add_edge("handle", END)

    # Compile with checkpointer
    checkpointer = InMemorySaver()
    return builder.compile(checkpointer=checkpointer)


def print_separator(title: str):
    """Print a visual separator."""
    print("\n" + "=" * 70)
    print(f"  {title}")
    print("=" * 70)


def print_conversation(customer_name: str, messages: list):
    """Pretty print a conversation."""
    print(f"\n💬 Conversation for {customer_name}:")
    print("-" * 70)
    for msg in messages:
        role = msg.type.upper() if hasattr(msg, 'type') else "UNKNOWN"
        content = msg.content if hasattr(msg, 'content') else str(msg)
        emoji = "👤" if "HUMAN" in role else "🤖"
        print(f"{emoji} {role}: {content}")


def main():
    """Demonstrate thread isolation with multiple customers."""
    print_separator("THREAD MANAGEMENT & ISOLATION EXAMPLE")

    # Build graph
    graph = build_support_graph()

    # =========================================================================
    # SCENARIO: Three customers contact support simultaneously
    # =========================================================================

    print("\n📋 Scenario: Three customers contact support")
    print("   - Alice (ticket #1001)")
    print("   - Bob (ticket #1002)")
    print("   - Carol (ticket #1003)")
    print("\n   Each customer has their own isolated conversation thread.")

    # =========================================================================
    # CUSTOMER A: Alice
    # =========================================================================

    print_separator("CUSTOMER A: ALICE")

    # Create unique thread for Alice
    config_alice = {"configurable": {"thread_id": "customer-alice-session-1"}}

    print("\n🔵 Turn 1: Alice starts conversation")
    from langchain_core.messages import HumanMessage
    result_alice_1 = graph.invoke(
        {
            "messages": [HumanMessage(content="Hello, I need help")],
            "customer_name": "Alice",
            "ticket_id": "1001"
        },
        config_alice
    )
    print_conversation("Alice", result_alice_1["messages"])

    print("\n🔵 Turn 2: Alice asks about status")
    result_alice_2 = graph.invoke(
        {
            "messages": [HumanMessage(content="What's the status of my ticket?")],
            "customer_name": "Alice",
            "ticket_id": "1001"
        },
        config_alice
    )
    print_conversation("Alice", result_alice_2["messages"])

    # =========================================================================
    # CUSTOMER B: Bob (interleaved with Alice)
    # =========================================================================

    print_separator("CUSTOMER B: BOB")

    # Create unique thread for Bob
    config_bob = {"configurable": {"thread_id": "customer-bob-session-1"}}

    print("\n🟢 Turn 1: Bob starts conversation")
    result_bob_1 = graph.invoke(
        {
            "messages": [HumanMessage(content="Hi there")],
            "customer_name": "Bob",
            "ticket_id": "1002"
        },
        config_bob
    )
    print_conversation("Bob", result_bob_1["messages"])

    # =========================================================================
    # CUSTOMER C: Carol
    # =========================================================================

    print_separator("CUSTOMER C: CAROL")

    # Create unique thread for Carol
    config_carol = {"configurable": {"thread_id": "customer-carol-session-1"}}

    print("\n🟣 Turn 1: Carol starts conversation")
    result_carol_1 = graph.invoke(
        {
            "messages": [HumanMessage(content="I have a question about my order")],
            "customer_name": "Carol",
            "ticket_id": "1003"
        },
        config_carol
    )
    print_conversation("Carol", result_carol_1["messages"])

    # =========================================================================
    # CONTINUE BOB'S CONVERSATION (after Carol)
    # =========================================================================

    print_separator("BACK TO BOB")

    print("\n🟢 Turn 2: Bob continues (after Carol interrupted)")
    result_bob_2 = graph.invoke(
        {
            "messages": [HumanMessage(content="Can I cancel my order?")],
            "customer_name": "Bob",
            "ticket_id": "1002"
        },
        config_bob
    )
    print_conversation("Bob", result_bob_2["messages"])

    # =========================================================================
    # DEMONSTRATE THREAD ISOLATION
    # =========================================================================

    print_separator("THREAD ISOLATION VERIFICATION")

    print("\n🔍 Verifying thread isolation...")

    # Get final state for each customer
    state_alice = graph.get_state(config_alice)
    state_bob = graph.get_state(config_bob)
    state_carol = graph.get_state(config_carol)

    # Check Alice's state
    print("\n✅ Alice's Thread (customer-alice-session-1):")
    print(f"   Customer name: {state_alice.values['customer_name']}")
    print(f"   Ticket ID: {state_alice.values['ticket_id']}")
    print(f"   Total messages: {len(state_alice.values['messages'])}")
    print(f"   Last message: {state_alice.values['messages'][-1].content[:50]}...")

    # Check Bob's state
    print("\n✅ Bob's Thread (customer-bob-session-1):")
    print(f"   Customer name: {state_bob.values['customer_name']}")
    print(f"   Ticket ID: {state_bob.values['ticket_id']}")
    print(f"   Total messages: {len(state_bob.values['messages'])}")
    print(f"   Last message: {state_bob.values['messages'][-1].content[:50]}...")

    # Check Carol's state
    print("\n✅ Carol's Thread (customer-carol-session-1):")
    print(f"   Customer name: {state_carol.values['customer_name']}")
    print(f"   Ticket ID: {state_carol.values['ticket_id']}")
    print(f"   Total messages: {len(state_carol.values['messages'])}")
    print(f"   Last message: {state_carol.values['messages'][-1].content[:50]}...")

    # =========================================================================
    # VERIFY NO CROSS-CONTAMINATION
    # =========================================================================

    print("\n🔍 Verifying no cross-contamination:")

    alice_ticket = state_alice.values['ticket_id']
    bob_ticket = state_bob.values['ticket_id']
    carol_ticket = state_carol.values['ticket_id']

    # Check Alice's messages don't contain other tickets
    alice_messages_text = " ".join(msg.content for msg in state_alice.values['messages'])
    if bob_ticket not in alice_messages_text and carol_ticket not in alice_messages_text:
        print(f"   ✅ Alice's thread isolated (no mention of tickets {bob_ticket} or {carol_ticket})")
    else:
        print(f"   ❌ Alice's thread contaminated!")

    # Check Bob's messages don't contain other tickets
    bob_messages_text = " ".join(msg.content for msg in state_bob.values['messages'])
    if alice_ticket not in bob_messages_text and carol_ticket not in bob_messages_text:
        print(f"   ✅ Bob's thread isolated (no mention of tickets {alice_ticket} or {carol_ticket})")
    else:
        print(f"   ❌ Bob's thread contaminated!")

    # Check Carol's messages don't contain other tickets
    carol_messages_text = " ".join(msg.content for msg in state_carol.values['messages'])
    if alice_ticket not in carol_messages_text and bob_ticket not in carol_messages_text:
        print(f"   ✅ Carol's thread isolated (no mention of tickets {alice_ticket} or {bob_ticket})")
    else:
        print(f"   ❌ Carol's thread contaminated!")

    # =========================================================================
    # DEMONSTRATE THREAD HISTORY
    # =========================================================================

    print_separator("THREAD HISTORY")

    print("\n📚 Alice's conversation history:")
    alice_history = list(graph.get_state_history(config_alice))
    print(f"   Total checkpoints: {len(alice_history)}")
    for i, snapshot in enumerate(reversed(alice_history)):
        step = snapshot.metadata.get('step', 0) if snapshot.metadata else 0
        msg_count = len(snapshot.values.get('messages', []))
        print(f"   [{i}] Step {step}: {msg_count} messages")

    print("\n📚 Bob's conversation history:")
    bob_history = list(graph.get_state_history(config_bob))
    print(f"   Total checkpoints: {len(bob_history)}")
    for i, snapshot in enumerate(reversed(bob_history)):
        step = snapshot.metadata.get('step', 0) if snapshot.metadata else 0
        msg_count = len(snapshot.values.get('messages', []))
        print(f"   [{i}] Step {step}: {msg_count} messages")

    # =========================================================================
    # SUMMARY
    # =========================================================================

    print_separator("SUMMARY")

    print("\n✅ Thread Management Demonstrated:")
    print("   ✓ Three independent customer threads created")
    print("   ✓ Conversations interleaved without interference")
    print("   ✓ Each thread maintains isolated state")
    print("   ✓ No cross-contamination between threads")
    print("   ✓ Each thread has independent checkpoint history")
    print("\n💡 Key Takeaway:")
    print("   Different thread_ids = Complete isolation")
    print("   Same thread_id = Shared conversation history")
    print()


if __name__ == "__main__":
    main()
