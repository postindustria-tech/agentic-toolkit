"""
Example 05: Complete Customer Support Multi-Agent System

This comprehensive example demonstrates ALL 4 core concepts from the epic:
1. Adding compiled graphs as nodes
2. Subgraph communication (shared and different schemas)
3. Parent-child state management
4. Reusable components (factory pattern)

Use Case: Customer support system with specialized subgraphs for intent
classification, knowledge retrieval, and response generation.
"""

from typing import TypedDict, Literal
from langgraph.graph import StateGraph, START, END, MessagesState
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage


# ============================================================================
# CONCEPT 4: Reusable Components - Intent Classifier Factory
# ============================================================================

def create_intent_classifier(intents: dict[str, list[str]]):
    """
    Factory function for creating intent classifier subgraphs.

    This demonstrates CONCEPT 4: Reusable components via factory pattern.

    Args:
        intents: Dictionary mapping intent names to trigger keywords

    Returns:
        Compiled StateGraph for intent classification
    """

    def classify_intent(state: MessagesState) -> dict:
        """Classify the intent of the last user message."""
        last_message = state["messages"][-1].content.lower()

        # Match intent based on keywords
        detected_intent = "general"
        for intent_name, keywords in intents.items():
            if any(keyword in last_message for keyword in keywords):
                detected_intent = intent_name
                break

        intent_message = SystemMessage(
            content=f"[Intent: {detected_intent}]"
        )

        print(f"  Intent Classifier → Detected: {detected_intent}")

        return {"messages": [intent_message]}

    # Create and compile subgraph
    subgraph = StateGraph(MessagesState)
    subgraph.add_node("classify", classify_intent)
    subgraph.add_edge(START, "classify")
    subgraph.add_edge("classify", END)

    return subgraph.compile()


# ============================================================================
# CONCEPT 3: Different Schema - Knowledge Retrieval Subgraph
# ============================================================================

class RetrievalState(TypedDict):
    """
    Different state schema for knowledge retrieval.

    This demonstrates CONCEPT 3: Parent-child state management
    with different schemas requiring transformation.
    """
    query: str  # Search query
    intent: str  # User intent
    results: list[str]  # Retrieved knowledge articles


def search_knowledge_base(state: RetrievalState) -> dict:
    """
    Search knowledge base based on intent and query.

    This subgraph has a completely different state schema.
    """
    intent = state["intent"]
    query = state["query"]

    # Mock knowledge base
    knowledge_base = {
        "billing": [
            "Billing: We charge on the 1st of each month",
            "Billing: You can update payment methods in Settings → Billing",
            "Billing: Refunds are processed within 5-7 business days"
        ],
        "technical": [
            "Technical: Try clearing your cache and cookies",
            "Technical: Ensure you're using the latest version",
            "Technical: Check the status page at status.example.com"
        ],
        "account": [
            "Account: Password can be reset at /forgot-password",
            "Account: Enable 2FA in Security Settings",
            "Account: Contact support to delete your account"
        ]
    }

    # Retrieve relevant articles
    results = knowledge_base.get(intent, [
        "General: Visit our help center at help.example.com",
        "General: Contact support at support@example.com"
    ])

    print(f"  Knowledge Retriever → Found {len(results)} articles for {intent}")

    return {"results": results}


def create_knowledge_retriever():
    """
    Create knowledge retrieval subgraph with different schema.

    This demonstrates CONCEPT 2: Subgraph communication with
    different schemas (RetrievalState vs MessagesState).
    """
    subgraph = StateGraph(RetrievalState)
    subgraph.add_node("search", search_knowledge_base)
    subgraph.add_edge(START, "search")
    subgraph.add_edge("search", END)

    return subgraph.compile()


# ============================================================================
# CONCEPT 2: Shared Schema - Response Generator Subgraph
# ============================================================================

def generate_response(state: MessagesState) -> dict:
    """
    Generate response based on conversation and knowledge.

    This demonstrates CONCEPT 2: Subgraph communication with
    shared schema (MessagesState).
    """
    # Extract knowledge articles from system messages
    knowledge_articles = []
    for msg in state["messages"]:
        if isinstance(msg, SystemMessage) and "[Knowledge:" in msg.content:
            articles_str = msg.content.split("[Knowledge:")[1].split("]")[0]
            knowledge_articles = articles_str.split("; ")

    # Generate response incorporating knowledge
    if knowledge_articles:
        response = "Here's what I found:\n\n"
        for i, article in enumerate(knowledge_articles, 1):
            response += f"{i}. {article}\n"
        response += "\nIs there anything else I can help you with?"
    else:
        response = "I'll be happy to help! Could you provide more details?"

    response_message = AIMessage(content=response)

    print(f"  Response Generator → Generated response with {len(knowledge_articles)} articles")

    return {"messages": [response_message]}


def create_response_generator():
    """
    Create response generator subgraph with shared schema.

    This demonstrates CONCEPT 2: Shared state schema communication.
    """
    subgraph = StateGraph(MessagesState)
    subgraph.add_node("generate", generate_response)
    subgraph.add_edge(START, "generate")
    subgraph.add_edge("generate", END)

    return subgraph.compile()


# ============================================================================
# CONCEPT 1 & 3: Parent Graph with State Mapping
# ============================================================================

class SupportState(MessagesState):
    """
    Parent state schema extending MessagesState.

    Allows sharing messages with subgraphs while adding parent-specific fields.
    """
    session_id: str
    intent: str


def initialize_session(state: SupportState) -> dict:
    """Initialize support session."""
    print(f"→ Support System: Initialized session {state['session_id']}")
    return {}


def create_retrieval_wrapper():
    """
    Create wrapper for knowledge retrieval subgraph.

    This demonstrates CONCEPT 3: State mapping between different schemas.
    The wrapper bridges SupportState and RetrievalState.
    """
    retriever = create_knowledge_retriever()

    def retrieve_knowledge(state: SupportState) -> dict:
        """
        Wrapper that handles state transformation.

        CONCEPT 3: Transform parent state → subgraph state → parent state.
        """
        # Extract intent from system messages
        intent = "general"
        for msg in reversed(state["messages"]):
            if isinstance(msg, SystemMessage) and "[Intent:" in msg.content:
                intent = msg.content.split("[Intent:")[1].split("]")[0].strip()
                break

        # Get query from last user message
        query = state["messages"][-1].content

        # STEP 1: Transform to RetrievalState
        retrieval_input = {
            "query": query,
            "intent": intent,
            "results": []
        }

        # STEP 2: Invoke subgraph
        retrieval_output = retriever.invoke(retrieval_input)

        # STEP 3: Transform back to SupportState
        knowledge_message = SystemMessage(
            content=f"[Knowledge: {'; '.join(retrieval_output['results'])}]"
        )

        return {
            "messages": [knowledge_message],
            "intent": intent
        }

    return retrieve_knowledge


def create_support_system():
    """
    Create the main customer support system.

    This demonstrates CONCEPT 1: Adding compiled graphs as nodes.
    """
    # Create all subgraphs
    intent_classifier = create_intent_classifier(intents={
        "billing": ["bill", "payment", "charge", "refund", "invoice"],
        "technical": ["error", "bug", "not working", "broken", "issue"],
        "account": ["password", "login", "sign in", "account", "profile"]
    })

    response_generator = create_response_generator()
    knowledge_wrapper = create_retrieval_wrapper()

    # Create parent graph
    system = StateGraph(SupportState)

    # CONCEPT 1: Add compiled graphs as nodes
    system.add_node("init", initialize_session)
    system.add_node("classify", intent_classifier)  # Subgraph with shared schema
    system.add_node("retrieve", knowledge_wrapper)  # Wrapper for different schema
    system.add_node("respond", response_generator)  # Subgraph with shared schema

    # Define workflow
    system.add_edge(START, "init")
    system.add_edge("init", "classify")
    system.add_edge("classify", "retrieve")
    system.add_edge("retrieve", "respond")
    system.add_edge("respond", END)

    return system.compile()


# ============================================================================
# MAIN EXECUTION
# ============================================================================

def main():
    """Run the customer support system with example queries."""
    system = create_support_system()

    # Example 1: Billing question
    print("=" * 70)
    print("Example 1: Billing Question")
    print("=" * 70)

    result1 = system.invoke({
        "messages": [HumanMessage(content="How do I get a refund for my last payment?")],
        "session_id": "session-001",
        "intent": ""
    })

    print("\n--- Conversation ---")
    for msg in result1["messages"]:
        if isinstance(msg, (HumanMessage, AIMessage)):
            print(f"{msg.__class__.__name__}: {msg.content}")

    # Example 2: Technical issue
    print("\n\n" + "=" * 70)
    print("Example 2: Technical Issue")
    print("=" * 70)

    result2 = system.invoke({
        "messages": [HumanMessage(content="The app is not working and showing errors")],
        "session_id": "session-002",
        "intent": ""
    })

    print("\n--- Conversation ---")
    for msg in result2["messages"]:
        if isinstance(msg, (HumanMessage, AIMessage)):
            print(f"{msg.__class__.__name__}: {msg.content}")

    # Example 3: Account question
    print("\n\n" + "=" * 70)
    print("Example 3: Account Question")
    print("=" * 70)

    result3 = system.invoke({
        "messages": [HumanMessage(content="I forgot my password and can't login")],
        "session_id": "session-003",
        "intent": ""
    })

    print("\n--- Conversation ---")
    for msg in result3["messages"]:
        if isinstance(msg, (HumanMessage, AIMessage)):
            print(f"{msg.__class__.__name__}: {msg.content}")

    print("\n" + "=" * 70)
    print("✓ Example completed successfully")
    print("=" * 70)
    print("\n🎯 All 4 Epic Concepts Demonstrated:")
    print("  1. ✓ Adding compiled graphs as nodes (3 subgraphs)")
    print("  2. ✓ Subgraph communication (shared & different schemas)")
    print("  3. ✓ Parent-child state management (retrieval wrapper)")
    print("  4. ✓ Reusable components (intent classifier factory)")


if __name__ == "__main__":
    main()
