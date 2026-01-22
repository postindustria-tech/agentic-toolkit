"""
Conditional Routing in LangGraph

This example demonstrates:
- Conditional edges for branching logic
- Router functions that determine next node
- Different execution paths based on state
- Explicit path mapping in add_conditional_edges

No external dependencies required (uses built-in LangGraph only).
"""

from typing import TypedDict, Literal
from langgraph.graph import StateGraph, START, END


# ============================================================================
# State Definition
# ============================================================================

class WorkflowState(TypedDict):
    """
    State for conditional routing workflow.

    Fields:
        input: User input to process
        category: Classified category (question/command/unknown)
        confidence: Confidence score (0.0 to 1.0)
        result: Final processing result
    """
    input: str
    category: str
    confidence: float
    result: str


# ============================================================================
# Node Functions
# ============================================================================

def classify_input(state: WorkflowState) -> dict:
    """
    Classify input into categories.

    Simple rule-based classification:
    - Questions end with "?"
    - Commands start with action verbs
    - Everything else is unknown
    """
    text = state["input"].lower()

    if "?" in text:
        return {
            "category": "question",
            "confidence": 0.9
        }
    elif any(text.startswith(cmd) for cmd in ["run", "execute", "start", "stop"]):
        return {
            "category": "command",
            "confidence": 0.85
        }
    else:
        return {
            "category": "unknown",
            "confidence": 0.5
        }


def handle_question(state: WorkflowState) -> dict:
    """
    Process question inputs.

    In production, would query knowledge base or use LLM.
    """
    result = f"Answering question: {state['input']}"
    return {"result": result}


def handle_command(state: WorkflowState) -> dict:
    """
    Process command inputs.

    In production, would execute actual commands.
    """
    result = f"Executing command: {state['input']}"
    return {"result": result}


def handle_unknown(state: WorkflowState) -> dict:
    """
    Process unknown inputs.

    Provides fallback for unrecognized input types.
    """
    result = f"Unknown input type: {state['input']}"
    return {"result": result}


def verify_high_confidence(state: WorkflowState) -> dict:
    """
    Verify high-confidence classifications.

    Additional validation for confident classifications.
    """
    result = f"[Verified] {state['result']}"
    return {"result": result}


def request_clarification(state: WorkflowState) -> dict:
    """
    Request clarification for low-confidence classifications.

    In production, would prompt user for more information.
    """
    result = f"[Needs Clarification] {state['result']}"
    return {"result": result}


# ============================================================================
# Routing Functions
# ============================================================================

# Type alias for routing destinations (improves type safety)
CategoryRoute = Literal["question", "command", "unknown"]

def route_by_category(state: WorkflowState) -> CategoryRoute:
    """
    Route to appropriate handler based on category.

    Router functions:
    - Accept state as input
    - Return string matching a key in path_map
    - Should have clear, documented routing logic
    """
    category = state["category"]

    # Validate routing decision
    if category not in ("question", "command", "unknown"):
        return "unknown"  # Safe fallback

    return category  # type: ignore


ConfidenceRoute = Literal["verify", "clarify"]

def route_by_confidence(state: WorkflowState) -> ConfidenceRoute:
    """
    Route based on confidence score.

    High confidence (>0.8) → verify
    Low confidence (≤0.8) → clarify
    """
    if state["confidence"] > 0.8:
        return "verify"
    return "clarify"


# ============================================================================
# Graph Construction
# ============================================================================

def create_routing_graph():
    """
    Build graph with conditional routing.

    Flow:
    1. Classify input
    2. Route to handler (question/command/unknown)
    3. Route to verification (verify/clarify)
    4. End
    """
    workflow = StateGraph(WorkflowState)

    # Add nodes
    workflow.add_node("classify", classify_input)
    workflow.add_node("handle_question", handle_question)
    workflow.add_node("handle_command", handle_command)
    workflow.add_node("handle_unknown", handle_unknown)
    workflow.add_node("verify", verify_high_confidence)
    workflow.add_node("clarify", request_clarification)

    # Linear edge to classifier
    workflow.add_edge(START, "classify")

    # Conditional edge: route by category
    workflow.add_conditional_edges(
        "classify",
        route_by_category,
        {
            "question": "handle_question",
            "command": "handle_command",
            "unknown": "handle_unknown"
        }
    )

    # All handlers route to confidence check
    workflow.add_conditional_edges(
        "handle_question",
        route_by_confidence,
        {"verify": "verify", "clarify": "clarify"}
    )
    workflow.add_conditional_edges(
        "handle_command",
        route_by_confidence,
        {"verify": "verify", "clarify": "clarify"}
    )
    workflow.add_conditional_edges(
        "handle_unknown",
        route_by_confidence,
        {"verify": "verify", "clarify": "clarify"}
    )

    # Final edges to END
    workflow.add_edge("verify", END)
    workflow.add_edge("clarify", END)

    return workflow.compile()


# ============================================================================
# Example Usage
# ============================================================================

if __name__ == "__main__":
    app = create_routing_graph()

    test_cases = [
        ("What is LangGraph?", "question", "verify"),
        ("Run the tests", "command", "verify"),
        ("Hello there", "unknown", "clarify"),
        ("How do I use this?", "question", "verify"),
    ]

    for idx, (input_text, expected_category, expected_route) in enumerate(test_cases, 1):
        print("=" * 70)
        print(f"Test Case {idx}: {input_text}")
        print("=" * 70)

        result = app.invoke({
            "input": input_text,
            "category": "",
            "confidence": 0.0,
            "result": ""
        })

        print(f"\nInput:      {result['input']}")
        print(f"Category:   {result['category']} (expected: {expected_category})")
        print(f"Confidence: {result['confidence']:.2f}")
        print(f"Route:      {'verify' if result['confidence'] > 0.8 else 'clarify'} (expected: {expected_route})")
        print(f"Result:     {result['result']}")
        print()

    print("=" * 70)
    print("✓ Conditional routing executed successfully")
    print("=" * 70)
    print("\nKey Concepts Demonstrated:")
    print("  1. Conditional edges with router functions")
    print("  2. Multiple branching points in workflow")
    print("  3. Type-safe routing with Literal types")
    print("  4. Explicit path_map for clarity")
    print("  5. Validation in router functions (safe fallbacks)")
