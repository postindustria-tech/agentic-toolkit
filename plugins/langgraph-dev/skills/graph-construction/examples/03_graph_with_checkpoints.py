"""
Graph with Checkpointing (Persistence and Resumption)

This example demonstrates:
- InMemorySaver for state persistence
- Thread ID for conversation continuity
- Resuming workflows from checkpoints
- Stateful multi-turn interactions

Note: InMemorySaver is for testing only. For production, use PostgresSaver
from langgraph-checkpoint-postgres.
"""

from typing import TypedDict, List
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import InMemorySaver


# ============================================================================
# State Definition
# ============================================================================

class ConversationState(TypedDict):
    """
    State for multi-turn conversation.

    Fields:
        messages: List of conversation messages
        user_name: Name of the user (persisted across turns)
        turn_count: Number of turns in conversation
    """
    messages: List[str]
    user_name: str
    turn_count: int


# ============================================================================
# Node Functions
# ============================================================================

def greet_user(state: ConversationState) -> dict:
    """
    Greet user based on whether it's first or subsequent turn.

    Demonstrates how checkpointing enables stateful behavior.
    """
    if state["turn_count"] == 0:
        # First turn - ask for name
        greeting = "Hello! What's your name?"
        return {
            "messages": state["messages"] + [greeting],
            "turn_count": 1
        }
    else:
        # Subsequent turns - use stored name
        greeting = f"Welcome back, {state['user_name']}!"
        return {
            "messages": state["messages"] + [greeting],
            "turn_count": state["turn_count"] + 1
        }


def process_input(state: ConversationState) -> dict:
    """
    Process user input.

    On first turn, extracts and stores user name.
    On subsequent turns, echoes message.
    """
    last_message = state["messages"][-1] if state["messages"] else ""

    if state["turn_count"] == 1:
        # Extract name from first user message (simple approach)
        # In production, would use NLP or structured input
        user_name = last_message.strip()
        response = f"Nice to meet you, {user_name}!"
        return {
            "messages": state["messages"] + [response],
            "user_name": user_name,
            "turn_count": state["turn_count"] + 1
        }
    else:
        # Echo message for subsequent turns
        response = f"You said: {last_message}"
        return {
            "messages": state["messages"] + [response],
            "turn_count": state["turn_count"] + 1
        }


# ============================================================================
# Graph Construction
# ============================================================================

def create_stateful_graph():
    """
    Build graph with checkpointing enabled.

    Checkpointing allows:
    - State persistence across invocations
    - Multi-turn conversations
    - Workflow resumption after interrupts
    """
    workflow = StateGraph(ConversationState)

    # Add nodes
    workflow.add_node("greet", greet_user)
    workflow.add_node("process", process_input)

    # Add edges
    workflow.add_edge(START, "greet")
    workflow.add_edge("greet", "process")
    workflow.add_edge("process", END)

    # Compile with checkpointer
    # InMemorySaver is for testing - use PostgresSaver for production
    checkpointer = InMemorySaver()
    return workflow.compile(checkpointer=checkpointer)


# ============================================================================
# Example Usage
# ============================================================================

if __name__ == "__main__":
    app = create_stateful_graph()

    # Thread ID is required for checkpoint persistence
    # Same thread_id = same conversation
    config = {"configurable": {"thread_id": "conversation-1"}}

    print("=" * 70)
    print("Checkpoint Demo: Multi-Turn Conversation")
    print("=" * 70)

    # Turn 1: Initial greeting
    print("\n--- Turn 1: Initial Interaction ---")
    initial_state = {
        "messages": [],
        "user_name": "",
        "turn_count": 0
    }
    result = app.invoke(initial_state, config)
    print(f"Bot: {result['messages'][-1]}")  # Show last message

    # Turn 2: User provides name
    print("\n--- Turn 2: User Provides Name ---")
    print("User: Alice")
    result = app.invoke({
        "messages": result["messages"] + ["Alice"],
        "user_name": result["user_name"],
        "turn_count": result["turn_count"]
    }, config)
    print(f"Bot: {result['messages'][-1]}")
    print(f"[State] User name stored: {result['user_name']}")

    # Turn 3: Resume conversation (demonstrates persistence)
    print("\n--- Turn 3: Resume Conversation ---")
    print("User: Hello again!")
    result = app.invoke({
        "messages": result["messages"] + ["Hello again!"],
        "user_name": result["user_name"],
        "turn_count": result["turn_count"]
    }, config)
    print(f"Bot: {result['messages'][-1]}")
    print(f"[State] Turn count: {result['turn_count']}")
    print(f"[State] User name persisted: {result['user_name']}")

    # Demonstrate new thread (separate conversation)
    print("\n" + "=" * 70)
    print("New Thread: Fresh Conversation")
    print("=" * 70)
    config_new = {"configurable": {"thread_id": "conversation-2"}}

    print("\n--- New Conversation (Different Thread ID) ---")
    result_new = app.invoke(initial_state, config_new)
    print(f"Bot: {result_new['messages'][-1]}")
    print(f"[State] Turn count: {result_new['turn_count']} (reset)")
    print(f"[State] User name: '{result_new['user_name']}' (empty)")

    print("\n" + "=" * 70)
    print("✓ Checkpointing executed successfully")
    print("=" * 70)
    print("\nKey Concepts Demonstrated:")
    print("  1. InMemorySaver for state persistence")
    print("  2. Thread ID for conversation continuity")
    print("  3. State carries over between invocations")
    print("  4. Different threads = independent conversations")
    print("  5. Production would use PostgresSaver (from langgraph-checkpoint-postgres)")
    print("\nNote: This example uses InMemorySaver for testing.")
    print("For production, install: pip install langgraph-checkpoint-postgres")
    print("Then use: PostgresSaver.from_conn_string(conn_string)")
