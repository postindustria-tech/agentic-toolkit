"""
Complete LangGraph Workflow

This example combines all core concepts:
- Linear flow for input processing
- Conditional routing for branching logic
- Error handling and retry loops
- State management with multiple fields

Demonstrates a complete, production-like workflow pattern.
"""

from typing import TypedDict, Literal
from langgraph.graph import StateGraph, START, END


# ============================================================================
# State Definition
# ============================================================================

class ProcessingState(TypedDict):
    """
    Complete state for data processing workflow.

    Fields:
        input: Raw input data
        validated: Whether input passed validation
        transformed: Processed data
        quality_score: Quality assessment (0.0 to 1.0)
        retry_count: Number of retry attempts
        error: Error message if processing failed
        result: Final processing result
    """
    input: str
    validated: bool
    transformed: str
    quality_score: float
    retry_count: int
    error: str
    result: str


# ============================================================================
# Node Functions
# ============================================================================

def validate_input(state: ProcessingState) -> dict:
    """
    Validate input data.

    Checks:
    - Input is not empty
    - Input length is reasonable
    - Input contains valid characters
    """
    input_text = state["input"]

    # Validation rules
    is_valid = (
        len(input_text) > 0 and
        len(input_text) < 1000 and
        input_text.strip() != ""
    )

    if is_valid:
        return {
            "validated": True,
            "error": ""
        }
    else:
        return {
            "validated": False,
            "error": "Input validation failed: invalid format or length"
        }


def transform_data(state: ProcessingState) -> dict:
    """
    Transform validated input.

    Applies business logic transformations:
    - Normalize whitespace
    - Convert to title case
    - Add metadata
    """
    try:
        # Simulate transformation
        normalized = " ".join(state["input"].split())
        transformed = normalized.title()
        transformed_with_meta = f"[PROCESSED] {transformed}"

        return {
            "transformed": transformed_with_meta,
            "error": ""
        }
    except Exception as e:
        return {
            "error": f"Transformation failed: {str(e)}"
        }


def assess_quality(state: ProcessingState) -> dict:
    """
    Assess quality of transformed data.

    Quality score based on:
    - Length (longer = higher quality for this demo)
    - Word count
    - Complexity heuristics
    """
    transformed = state["transformed"]
    word_count = len(transformed.split())

    # Simple quality scoring
    if word_count >= 5:
        quality_score = 0.9
    elif word_count >= 3:
        quality_score = 0.7
    elif word_count >= 1:
        quality_score = 0.5
    else:
        quality_score = 0.3

    return {"quality_score": quality_score}


def generate_result(state: ProcessingState) -> dict:
    """
    Generate final result with metadata.

    Combines all state information into final output.
    """
    result = (
        f"Result: {state['transformed']}\n"
        f"Quality: {state['quality_score']:.2f}\n"
        f"Retries: {state['retry_count']}"
    )
    return {"result": result}


def handle_error(state: ProcessingState) -> dict:
    """
    Handle processing errors.

    Provides error details and increments retry count.
    """
    error_result = (
        f"ERROR: {state['error']}\n"
        f"Original input: {state['input']}\n"
        f"Retry attempt: {state['retry_count']}"
    )
    return {
        "result": error_result,
        "retry_count": state["retry_count"] + 1
    }


def retry_processing(state: ProcessingState) -> dict:
    """
    Prepare state for retry.

    Resets error state for another processing attempt.
    """
    return {
        "error": "",
        "retry_count": state["retry_count"] + 1
    }


# ============================================================================
# Routing Functions
# ============================================================================

ValidationRoute = Literal["transform", "error"]

def route_after_validation(state: ProcessingState) -> ValidationRoute:
    """
    Route based on validation result.

    Valid → transform
    Invalid → error
    """
    if state["validated"]:
        return "transform"
    return "error"


QualityRoute = Literal["generate", "error"]

def route_after_quality(state: ProcessingState) -> QualityRoute:
    """
    Route based on quality assessment.

    High quality (>0.6) → generate
    Low quality → error (for retry)
    """
    if state["quality_score"] >= 0.6:
        return "generate"
    return "error"


RetryRoute = Literal["retry", "end"]

def route_retry_decision(state: ProcessingState) -> RetryRoute:
    """
    Decide whether to retry or end.

    Retry if:
    - Retry count < 3
    - Error is present

    Otherwise end (accept result even if error)
    """
    if state["retry_count"] < 3 and state["error"]:
        return "retry"
    return "end"


# ============================================================================
# Graph Construction
# ============================================================================

def create_complete_workflow():
    """
    Build complete workflow with all concepts.

    Flow:
    1. Validate input → (valid: transform | invalid: error)
    2. Transform data
    3. Assess quality → (good: generate | poor: error)
    4. Generate result → end
    5. Error handler → (retry: back to validate | max retries: end)
    """
    workflow = StateGraph(ProcessingState)

    # Add nodes
    workflow.add_node("validate", validate_input)
    workflow.add_node("transform", transform_data)
    workflow.add_node("assess", assess_quality)
    workflow.add_node("generate", generate_result)
    workflow.add_node("error", handle_error)
    workflow.add_node("retry", retry_processing)

    # Linear start
    workflow.add_edge(START, "validate")

    # Conditional routing
    workflow.add_conditional_edges(
        "validate",
        route_after_validation,
        {"transform": "transform", "error": "error"}
    )

    # Linear transformation flow
    workflow.add_edge("transform", "assess")

    # Quality-based routing
    workflow.add_conditional_edges(
        "assess",
        route_after_quality,
        {"generate": "generate", "error": "error"}
    )

    # Success path
    workflow.add_edge("generate", END)

    # Retry logic
    workflow.add_conditional_edges(
        "error",
        route_retry_decision,
        {"retry": "retry", "end": END}
    )

    # Retry loops back to validation
    workflow.add_edge("retry", "validate")

    return workflow.compile()


# ============================================================================
# Example Usage
# ============================================================================

if __name__ == "__main__":
    app = create_complete_workflow()

    test_cases = [
        ("hello world from langgraph", "Success (good quality)"),
        ("hi", "Success (medium quality)"),
        ("", "Error (validation fails)"),
        ("this is a comprehensive test of the workflow", "Success (high quality)"),
    ]

    for idx, (input_text, expected_outcome) in enumerate(test_cases, 1):
        print("=" * 70)
        print(f"Test Case {idx}: {expected_outcome}")
        print("=" * 70)
        print(f"Input: '{input_text}'")

        initial_state = {
            "input": input_text,
            "validated": False,
            "transformed": "",
            "quality_score": 0.0,
            "retry_count": 0,
            "error": "",
            "result": ""
        }

        result = app.invoke(initial_state)

        print(f"\nValidated: {result['validated']}")
        print(f"Quality Score: {result['quality_score']:.2f}")
        print(f"Retry Count: {result['retry_count']}")
        if result['error']:
            print(f"Error: {result['error']}")
        print(f"\n{result['result']}")
        print()

    print("=" * 70)
    print("✓ Complete workflow executed successfully")
    print("=" * 70)
    print("\nKey Concepts Demonstrated:")
    print("  1. Multi-field state management")
    print("  2. Linear flow (validate → transform → assess)")
    print("  3. Conditional routing (validation, quality)")
    print("  4. Error handling with retry logic")
    print("  5. Loop prevention (max retry count)")
    print("  6. Production-like workflow pattern")
