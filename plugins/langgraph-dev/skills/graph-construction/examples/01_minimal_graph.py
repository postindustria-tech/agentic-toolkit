"""
Minimal LangGraph Workflow

This example demonstrates the simplest possible LangGraph workflow:
- State definition with TypedDict
- Node functions that transform state
- Linear edges connecting nodes
- Graph compilation and execution

No external dependencies required (uses built-in LangGraph only).
"""

from typing import TypedDict
from langgraph.graph import StateGraph, START, END


# ============================================================================
# State Definition
# ============================================================================

class MinimalState(TypedDict):
    """
    State for minimal workflow.

    Fields:
        input: Original user input
        processed: Processed version of input
        count: Number of processing steps completed
    """
    input: str
    processed: str
    count: int


# ============================================================================
# Node Functions
# ============================================================================

def parse_input(state: MinimalState) -> dict:
    """
    Parse input by converting to uppercase.

    Node functions should:
    - Accept state as input
    - Return dict with state updates
    - Not mutate state directly
    """
    processed = state["input"].upper()
    return {
        "processed": processed,
        "count": state["count"] + 1
    }


def transform_data(state: MinimalState) -> dict:
    """
    Transform data by adding a prefix.

    This demonstrates chaining multiple transformations.
    """
    transformed = f"TRANSFORMED: {state['processed']}"
    return {
        "processed": transformed,
        "count": state["count"] + 1
    }


def generate_output(state: MinimalState) -> dict:
    """
    Generate final output.

    The last node in the workflow prepares the final result.
    """
    output = f"{state['processed']} (Steps: {state['count']})"
    return {
        "processed": output,
        "count": state["count"] + 1
    }


# ============================================================================
# Graph Construction
# ============================================================================

def create_minimal_graph():
    """
    Build a minimal linear workflow.

    Steps:
    1. Create StateGraph with state schema
    2. Add nodes with their functions
    3. Add edges to define flow
    4. Compile to executable app
    """
    # Step 1: Create graph with state schema
    workflow = StateGraph(MinimalState)

    # Step 2: Add nodes
    workflow.add_node("parse", parse_input)
    workflow.add_node("transform", transform_data)
    workflow.add_node("output", generate_output)

    # Step 3: Add edges (linear flow)
    workflow.add_edge(START, "parse")
    workflow.add_edge("parse", "transform")
    workflow.add_edge("transform", "output")
    workflow.add_edge("output", END)

    # Step 4: Compile to executable
    return workflow.compile()


# ============================================================================
# Example Usage
# ============================================================================

if __name__ == "__main__":
    app = create_minimal_graph()

    # Test Case 1: Simple input
    print("=" * 70)
    print("Test Case 1: Simple Input")
    print("=" * 70)
    initial_state = {
        "input": "hello world",
        "processed": "",
        "count": 0
    }
    result = app.invoke(initial_state)
    print(f"\nInput:  {result['input']}")
    print(f"Output: {result['processed']}")
    print(f"Steps:  {result['count']}")

    # Test Case 2: Different input
    print("\n" + "=" * 70)
    print("Test Case 2: Different Input")
    print("=" * 70)
    initial_state = {
        "input": "langgraph is powerful",
        "processed": "",
        "count": 0
    }
    result = app.invoke(initial_state)
    print(f"\nInput:  {result['input']}")
    print(f"Output: {result['processed']}")
    print(f"Steps:  {result['count']}")

    print("\n" + "=" * 70)
    print("✓ Minimal graph executed successfully")
    print("=" * 70)
    print("\nKey Concepts Demonstrated:")
    print("  1. TypedDict state definition")
    print("  2. Node functions return state updates (not mutations)")
    print("  3. Linear edge flow (START → node1 → node2 → node3 → END)")
    print("  4. Graph compilation and invocation")
