"""
Example 04: Graph Factory Pattern for Reusable Components

This example demonstrates how to create reusable subgraph factories that can
be instantiated with different parameters/configurations.

Use Case: Content validation pipeline where we create multiple validation
subgraphs with different rules using a factory function.

Key Learning: Building component libraries with parametrized subgraph builders.
"""

from typing import TypedDict, Callable, Any
from langgraph.graph import StateGraph, START, END


# ============================================================================
# VALIDATION STATE SCHEMA
# ============================================================================

class ValidationState(TypedDict):
    """State schema for validation workflows."""
    content: str  # Content to validate
    is_valid: bool  # Validation result
    errors: list[str]  # Validation error messages


# ============================================================================
# VALIDATION FACTORY FUNCTION
# ============================================================================

def create_validator_subgraph(
    name: str,
    rules: list[Callable[[str], tuple[bool, str]]]
) -> Any:
    """
    Factory function to create parametrized validator subgraphs.

    This is the KEY PATTERN for reusable components: a function that
    accepts configuration parameters and returns a compiled graph.

    Args:
        name: Name of the validator (for logging)
        rules: List of validation functions that take content and return
               (is_valid, error_message) tuples

    Returns:
        Compiled StateGraph configured with the specified rules
    """

    def validate_content(state: ValidationState) -> dict:
        """
        Apply all validation rules to the content.

        This node is dynamically created based on the rules parameter.
        """
        content = state["content"]
        errors = []
        is_valid = True

        print(f"  → {name}: Validating content...")

        # Apply each rule
        for rule in rules:
            rule_valid, error_msg = rule(content)
            if not rule_valid:
                is_valid = False
                errors.append(error_msg)

        if is_valid:
            print(f"  → {name}: ✓ All checks passed")
        else:
            print(f"  → {name}: ✗ Found {len(errors)} issue(s)")

        return {
            "is_valid": is_valid,
            "errors": errors
        }

    # Create the subgraph with the validation logic
    subgraph = StateGraph(ValidationState)
    subgraph.add_node("validate", validate_content)
    subgraph.add_edge(START, "validate")
    subgraph.add_edge("validate", END)

    return subgraph.compile()


# ============================================================================
# VALIDATION RULE LIBRARY
# ============================================================================

def length_rule(min_length: int, max_length: int) -> Callable[[str], tuple[bool, str]]:
    """Create a length validation rule."""
    def validate(content: str) -> tuple[bool, str]:
        length = len(content)
        if length < min_length:
            return False, f"Content too short (min: {min_length}, got: {length})"
        if length > max_length:
            return False, f"Content too long (max: {max_length}, got: {length})"
        return True, ""
    return validate


def profanity_rule(forbidden_words: list[str]) -> Callable[[str], tuple[bool, str]]:
    """Create a profanity validation rule."""
    def validate(content: str) -> tuple[bool, str]:
        content_lower = content.lower()
        found_words = [word for word in forbidden_words if word in content_lower]
        if found_words:
            return False, f"Forbidden words found: {', '.join(found_words)}"
        return True, ""
    return validate


def format_rule(required_prefix: str) -> Callable[[str], tuple[bool, str]]:
    """Create a format validation rule."""
    def validate(content: str) -> tuple[bool, str]:
        if not content.startswith(required_prefix):
            return False, f"Must start with '{required_prefix}'"
        return True, ""
    return validate


# ============================================================================
# PARENT WORKFLOW
# ============================================================================

class ContentState(TypedDict):
    """State schema for the content workflow."""
    content: str
    validation_results: list[dict]  # Results from each validator


def prepare_content(state: ContentState) -> dict:
    """Initial preparation step."""
    print(f"Processing content: '{state['content'][:50]}...'")
    return {"validation_results": []}


def create_validation_wrapper(validator_name: str, validator_graph: Any):
    """
    Create a wrapper function for a validation subgraph.

    This bridges ContentState and ValidationState.
    """
    def run_validation(state: ContentState) -> dict:
        """Invoke validator and collect results."""
        # Transform to ValidationState
        validation_input = {
            "content": state["content"],
            "is_valid": True,
            "errors": []
        }

        # Run validator subgraph
        result = validator_graph.invoke(validation_input)

        # Collect results
        validation_result = {
            "validator": validator_name,
            "is_valid": result["is_valid"],
            "errors": result["errors"]
        }

        return {"validation_results": [validation_result]}

    return run_validation


def summarize_validation(state: ContentState) -> dict:
    """Summarize all validation results."""
    all_valid = all(r["is_valid"] for r in state["validation_results"])

    print("\n--- Validation Summary ---")
    for result in state["validation_results"]:
        status = "✓ PASS" if result["is_valid"] else "✗ FAIL"
        print(f"{result['validator']}: {status}")
        for error in result["errors"]:
            print(f"  - {error}")

    print(f"\nOverall Result: {'✓ VALID' if all_valid else '✗ INVALID'}")

    return {}


def create_content_workflow():
    """
    Create the main content workflow that uses multiple validators.

    This demonstrates using the factory pattern to create reusable validators.
    """
    # Create different validators using the factory pattern
    # Each validator is a separate subgraph with its own rules

    # Validator 1: Length validator
    length_validator = create_validator_subgraph(
        name="LengthValidator",
        rules=[
            length_rule(min_length=10, max_length=200)
        ]
    )

    # Validator 2: Profanity validator
    profanity_validator = create_validator_subgraph(
        name="ProfanityValidator",
        rules=[
            profanity_rule(forbidden_words=["spam", "inappropriate", "offensive"])
        ]
    )

    # Validator 3: Format validator
    format_validator = create_validator_subgraph(
        name="FormatValidator",
        rules=[
            format_rule(required_prefix="Content:")
        ]
    )

    # Create main workflow
    workflow = StateGraph(ContentState)

    # Add nodes
    workflow.add_node("prepare", prepare_content)
    workflow.add_node(
        "check_length",
        create_validation_wrapper("LengthValidator", length_validator)
    )
    workflow.add_node(
        "check_profanity",
        create_validation_wrapper("ProfanityValidator", profanity_validator)
    )
    workflow.add_node(
        "check_format",
        create_validation_wrapper("FormatValidator", format_validator)
    )
    workflow.add_node("summarize", summarize_validation)

    # Define flow - run validators in sequence
    workflow.add_edge(START, "prepare")
    workflow.add_edge("prepare", "check_length")
    workflow.add_edge("check_length", "check_profanity")
    workflow.add_edge("check_profanity", "check_format")
    workflow.add_edge("check_format", "summarize")
    workflow.add_edge("summarize", END)

    return workflow.compile()


# ============================================================================
# MAIN EXECUTION
# ============================================================================

def main():
    """Run the content workflow with example inputs."""
    workflow = create_content_workflow()

    # Example 1: Valid content
    print("=" * 70)
    print("Example 1: Valid Content")
    print("=" * 70)

    workflow.invoke({
        "content": "Content: This is a perfectly valid piece of content that meets all requirements.",
        "validation_results": []
    })

    # Example 2: Content too short
    print("\n\n" + "=" * 70)
    print("Example 2: Content Too Short")
    print("=" * 70)

    workflow.invoke({
        "content": "Content: Short",
        "validation_results": []
    })

    # Example 3: Missing required prefix
    print("\n\n" + "=" * 70)
    print("Example 3: Missing Required Prefix")
    print("=" * 70)

    workflow.invoke({
        "content": "This content is missing the required prefix.",
        "validation_results": []
    })

    # Example 4: Contains profanity
    print("\n\n" + "=" * 70)
    print("Example 4: Contains Forbidden Words")
    print("=" * 70)

    workflow.invoke({
        "content": "Content: This is spam content with inappropriate material.",
        "validation_results": []
    })

    print("\n" + "=" * 70)
    print("✓ Example completed successfully")
    print("=" * 70)
    print("\nKey Observation:")
    print("  The factory pattern allowed us to create 3 different validators")
    print("  from the same create_validator_subgraph() function by passing")
    print("  different rules. This enables building reusable component libraries.")


if __name__ == "__main__":
    main()
