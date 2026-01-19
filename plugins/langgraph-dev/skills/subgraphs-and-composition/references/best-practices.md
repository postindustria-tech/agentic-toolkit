# Best Practices for Subgraph Composition

This reference provides detailed best practices for building modular, maintainable LangGraph applications using subgraphs. Each practice includes code examples showing both correct and incorrect approaches.

## Overview

Effective subgraph composition requires:
- Clear responsibility boundaries for each subgraph
- Minimal state coupling between parent and child
- Type safety through TypedDict schemas
- Graceful error handling across boundaries
- Independent testing of each component
- Clear documentation of state contracts
- Preference for shared schemas when possible
- Reusable components via factory functions

## 1. Define Clear Boundaries

**Principle**: Each subgraph should have a single, well-defined responsibility.

### ✓ GOOD: Single, focused responsibility

```python
def create_fraud_detector():
    """Subgraph that ONLY detects fraud."""
    subgraph = StateGraph(OrderState)
    subgraph.add_node("assess_risk", assess_fraud_risk)
    subgraph.add_node("calculate_score", calculate_fraud_score)
    subgraph.add_edge(START, "assess_risk")
    subgraph.add_edge("assess_risk", "calculate_score")
    subgraph.add_edge("calculate_score", END)
    return subgraph.compile()

def create_payment_processor():
    """Subgraph that ONLY processes payments."""
    subgraph = StateGraph(PaymentState)
    subgraph.add_node("process", process_payment_transaction)
    subgraph.add_edge(START, "process")
    subgraph.add_edge("process", END)
    return subgraph.compile()
```

**Why it works**:
- Each subgraph has one clear purpose
- Easy to test in isolation
- Can be reused in different contexts
- Changes to one don't affect the other

### ✗ BAD: Multiple unrelated responsibilities

```python
def create_order_handler():
    """ANTI-PATTERN: Does fraud, inventory, payment, and notifications."""
    subgraph = StateGraph(OrderState)
    subgraph.add_node("check_fraud", check_fraud)  # Fraud detection
    subgraph.add_node("check_inventory", check_inventory)  # Inventory management
    subgraph.add_node("process_payment", process_payment)  # Payment processing
    subgraph.add_node("send_email", send_email)  # Notification
    # This should be 4 separate subgraphs!
    return subgraph.compile()
```

**Why it fails**:
- Violates single responsibility principle
- Difficult to test specific functionality
- Cannot reuse fraud detection elsewhere
- Changes to inventory affect payment logic
- Hard to understand and maintain

**Guideline**: If you can describe a subgraph's purpose with "and", it should probably be split.

## 2. Minimize State Coupling

**Principle**: Only share state keys that are truly needed between parent and child.

### ✓ GOOD: Minimal state coupling with different schemas

```python
class PaymentState(TypedDict):
    """Only the fields needed for payment processing."""
    amount: float
    customer_id: str
    transaction_id: str
    success: bool

def create_payment_wrapper():
    """Wrapper extracts only needed fields."""
    processor = create_payment_processor()

    def process_payment(state: OrderState) -> dict:
        # Extract ONLY what's needed
        result = processor.invoke({
            "amount": state["total_amount"],
            "customer_id": state["customer_id"],
            "transaction_id": "",
            "success": False
        })

        # Return ONLY what parent needs
        return {"payment_successful": result["success"]}

    return process_payment
```

**Why it works**:
- Payment subgraph doesn't see order items, fraud scores, etc.
- Reduces coupling and improves reusability
- Payment can be used in non-order contexts
- Clear contract: amount + customer_id → success

### ✗ BAD: Sharing entire state schema unnecessarily

```python
class PaymentState(OrderState):  # Inherits ALL fields from OrderState
    """ANTI-PATTERN: Payment subgraph doesn't need order items, fraud score, etc."""
    pass

# Now payment subgraph has access to everything, creating tight coupling
# This makes it impossible to reuse the payment subgraph elsewhere
```

**Why it fails**:
- Payment depends on entire OrderState (items, fraud_score, inventory, etc.)
- Cannot reuse for subscription payments, refunds, etc.
- Changes to OrderState affect payment subgraph
- Violates information hiding principle

**Guideline**: Treat state fields like function parameters—only pass what's needed.

## 3. Use Type Safety

**Principle**: Leverage TypedDict for compile-time state contract validation.

### ✓ GOOD: Explicit type definitions with TypedDict

```python
from typing import TypedDict

class DocumentState(TypedDict):
    """Subgraph state with explicit types."""
    text: str
    word_count: int
    processed: bool

class WorkflowState(TypedDict):
    """Parent state with explicit types."""
    documents: list[str]
    results: list[dict]
    total_words: int

def process_document(state: DocumentState) -> dict:
    """Type hints ensure correct state usage."""
    # Editor/IDE will catch type errors
    return {
        "word_count": len(state["text"].split()),
        "processed": True
    }

# Type checker (mypy) validates:
# - All required fields present
# - Field types match
# - Return type matches state schema
```

**Why it works**:
- Catches type errors before runtime
- IDE autocomplete and type checking
- Self-documenting code
- Refactoring safety

### ✗ BAD: Using plain dict without types

```python
def process_document(state: dict) -> dict:
    """No type safety - errors only at runtime."""
    # Typo "txt" instead of "text" - won't catch until runtime
    return {
        "word_count": len(state["txt"].split()),  # KeyError at runtime!
        "processed": True
    }
```

**Why it fails**:
- No compile-time validation
- No IDE autocomplete
- Typos caught only at runtime
- Hard to understand state structure

**Guideline**: Always use TypedDict for state schemas. Enable mypy for type checking.

## 4. Handle Errors Gracefully

**Principle**: Subgraph errors should propagate to parent with context.

### ✓ GOOD: Graceful error handling with context

```python
class OrderState(TypedDict):
    order_id: str
    status: str
    error_messages: list[str]

def create_payment_wrapper():
    """Wrapper handles errors gracefully."""
    processor = create_payment_processor()

    def process_payment(state: OrderState) -> dict:
        try:
            result = processor.invoke({
                "amount": state["total_amount"],
                "customer_id": state["customer_id"],
                "transaction_id": "",
                "success": False,
                "error_message": ""
            })

            if not result["success"]:
                # Propagate error with context
                return {
                    "status": "failed",
                    "error_messages": [
                        f"Payment failed for order {state['order_id']}: {result['error_message']}"
                    ]
                }

            return {"status": "completed", "error_messages": []}

        except Exception as e:
            # Handle subgraph exceptions with context
            return {
                "status": "failed",
                "error_messages": [f"Payment processing error: {str(e)}"]
            }

    return process_payment
```

**Why it works**:
- Errors include order_id for debugging
- Parent can react to failures (retry, notify user)
- Exception handling prevents crashes
- Error messages are actionable

### ✗ BAD: No error handling or context

```python
def create_payment_wrapper():
    """ANTI-PATTERN: No error handling."""
    processor = create_payment_processor()

    def process_payment(state: OrderState) -> dict:
        # If processor.invoke() raises exception, entire workflow crashes
        result = processor.invoke({
            "amount": state["total_amount"],
            "customer_id": state["customer_id"],
            "transaction_id": "",
            "success": False
        })

        # If payment fails, workflow continues with stale state
        return {}  # What if result["success"] is False?

    return process_payment
```

**Why it fails**:
- Exceptions crash entire workflow
- Failed payments not detected
- No actionable error messages
- Debugging is difficult

**Guideline**: Always wrap subgraph invocations in try-except. Add context (IDs, step names) to error messages.

## 5. Test Subgraphs Independently

**Principle**: Each subgraph should be testable in isolation before integration.

### ✓ GOOD: Independent unit tests for each subgraph

```python
def test_fraud_detector():
    """Unit test for fraud detector subgraph."""
    detector = create_fraud_detector(rules={"max_amount": 500})

    # Test 1: Normal order (should pass)
    result = detector.invoke({
        "order_id": "TEST-001",
        "customer_id": "CUST-001",
        "items": [{"product_id": "PROD-001", "quantity": 2}],
        "total_amount": 200,
        "status": "pending",
        "fraud_score": 0.0
    })

    assert result["fraud_score"] < 0.5, "Normal order should pass fraud check"
    assert result["status"] == "inventory_check", "Should proceed to inventory"

def test_inventory_checker():
    """Unit test for inventory checker subgraph."""
    checker = create_inventory_checker()

    result = checker.invoke({
        "product_ids": ["PROD-001", "PROD-002"],
        "quantities": {"PROD-001": 10, "PROD-002": 5},
        "availability": {},
        "all_available": False
    })

    assert result["all_available"] == True, "Should have available inventory"

def test_payment_processor():
    """Unit test for payment processor subgraph."""
    processor = create_payment_processor()

    result = processor.invoke({
        "amount": 100.00,
        "customer_id": "CUST-001",
        "payment_method": "credit_card",
        "transaction_id": "",
        "success": False,
        "error_message": ""
    })

    assert result["success"] == True, "Payment should succeed"
    assert result["transaction_id"] != "", "Should have transaction ID"

# Each subgraph can be tested independently without running the full workflow
```

**Why it works**:
- Fast feedback on individual components
- Easier to identify which component failed
- Can test edge cases thoroughly
- Refactoring safety

### ✗ BAD: Only integration tests

```python
def test_entire_workflow():
    """ANTI-PATTERN: Only testing the full workflow."""
    workflow = create_order_processor()

    result = workflow.invoke({
        "order_id": "TEST-001",
        # ... full state ...
    })

    # If this fails, which subgraph caused it?
    # Fraud? Inventory? Payment? Hard to tell!
    assert result["status"] == "completed"
```

**Why it fails**:
- Slow (runs entire workflow)
- Hard to identify root cause
- Cannot test subgraph edge cases easily
- Coupling between tests and workflow structure

**Guideline**: Write unit tests for each subgraph before integration tests. Test edge cases at the subgraph level.

## 6. Document State Contracts

**Principle**: Clearly specify input/output state requirements for each subgraph.

### ✓ GOOD: Clear documentation of state contracts

```python
def create_knowledge_retriever():
    """
    Create knowledge retrieval subgraph.

    STATE CONTRACT:
    ---------------
    Input State (RetrievalState):
        - query: str - The search query
        - intent: str - User intent (billing, technical, account, general)
        - results: list[str] - Empty list (will be populated)

    Output State (RetrievalState):
        - query: str - Unchanged
        - intent: str - Unchanged
        - results: list[str] - Retrieved knowledge articles

    BEHAVIOR:
    ---------
    Searches knowledge base based on intent and returns relevant articles.
    Returns 2-3 articles for known intents, generic help for unknown.

    DEPENDENCIES:
    -------------
    None (mock knowledge base embedded in subgraph)

    EXAMPLE:
    --------
    >>> retriever = create_knowledge_retriever()
    >>> result = retriever.invoke({
    ...     "query": "How do I get a refund?",
    ...     "intent": "billing",
    ...     "results": []
    ... })
    >>> assert len(result["results"]) > 0
    >>> assert "Billing" in result["results"][0]
    """
    subgraph = StateGraph(RetrievalState)
    subgraph.add_node("search", search_knowledge_base)
    subgraph.add_edge(START, "search")
    subgraph.add_edge("search", END)
    return subgraph.compile()
```

**Why it works**:
- Clear input/output contract
- Example usage included
- Dependencies documented
- Behavior specified

### ✗ BAD: No documentation

```python
def create_knowledge_retriever():
    """Create knowledge retriever."""  # What does this do?
    subgraph = StateGraph(RetrievalState)
    subgraph.add_node("search", search_knowledge_base)
    subgraph.add_edge(START, "search")
    subgraph.add_edge("search", END)
    return subgraph.compile()

# Questions:
# - What fields are required in input state?
# - What fields are modified in output?
# - What is the expected behavior?
# - Are there external dependencies?
```

**Why it fails**:
- Users must read implementation to understand usage
- No contract enforcement
- Hard to maintain
- Integration errors common

**Guideline**: Document state contracts in factory function docstrings. Include input, output, behavior, dependencies, and an example.

## 7. Prefer Shared Schema When Possible

**Principle**: Shared schemas reduce boilerplate and transformation logic. Use different schemas only when necessary for clear separation of concerns.

### When to Use Shared Schema (MessagesState)

```python
# ✓ GOOD: All subgraphs work with messages - use shared schema
def create_intent_classifier():
    """Classifier uses MessagesState - no transformation needed."""
    subgraph = StateGraph(MessagesState)
    subgraph.add_node("classify", classify_intent)
    return subgraph.compile()

def create_response_generator():
    """Generator uses MessagesState - no transformation needed."""
    subgraph = StateGraph(MessagesState)
    subgraph.add_node("generate", generate_response)
    return subgraph.compile()

# Parent uses MessagesState too - seamless composition
chatbot = StateGraph(MessagesState)
chatbot.add_node("classify", create_intent_classifier())  # Direct usage
chatbot.add_node("respond", create_response_generator())  # Direct usage
```

**Benefits**:
- No wrapper functions needed
- No state transformation overhead
- Less boilerplate code
- Easier to understand

### When to Use Different Schema

```python
# ✓ GOOD: Payment logic doesn't need messages - use different schema
class PaymentState(TypedDict):
    """Focused schema for payment processing."""
    amount: float
    customer_id: str
    success: bool

def create_payment_processor():
    """Payment doesn't work with messages - different schema makes sense."""
    subgraph = StateGraph(PaymentState)
    subgraph.add_node("process", process_payment)
    return subgraph.compile()
```

**When different schemas make sense**:
- Subgraph domain is fundamentally different (payment vs chat)
- Subgraph is reusable across non-message contexts
- Reducing coupling is more important than reducing boilerplate

**Guideline**: Start with shared schema. Only introduce different schemas when there's a clear separation of concerns.

## 8. Use Factory Functions for Reusability

**Principle**: Create parametrized subgraph builders for configuration and flexibility.

### ✓ GOOD: Factory function for configurable subgraphs

```python
def create_validator_subgraph(
    name: str,
    rules: list[Callable[[str], tuple[bool, str]]]
):
    """
    Factory function creates validators with different rules.

    This enables building a library of reusable validation components.
    """
    def validate_content(state: ValidationState) -> dict:
        errors = []
        is_valid = True

        for rule in rules:
            rule_valid, error_msg = rule(state["content"])
            if not rule_valid:
                is_valid = False
                errors.append(error_msg)

        return {"is_valid": is_valid, "errors": errors}

    subgraph = StateGraph(ValidationState)
    subgraph.add_node("validate", validate_content)
    subgraph.add_edge(START, "validate")
    subgraph.add_edge("validate", END)

    return subgraph.compile()

# Create multiple validators from same factory
length_validator = create_validator_subgraph("Length", [length_rule(10, 200)])
email_validator = create_validator_subgraph("Email", [email_format_rule()])
profanity_validator = create_validator_subgraph("Profanity", [profanity_rule()])

# Same factory, different configurations = reusable component library
```

**Why it works**:
- One factory creates many validators
- Configuration injection (rules parameter)
- Reusable across projects
- Easy to add new validators

### ✗ BAD: Hardcoded validators

```python
def create_length_validator():
    """ANTI-PATTERN: Hardcoded length validator."""
    def validate_content(state: ValidationState) -> dict:
        errors = []
        is_valid = len(state["content"]) >= 10 and len(state["content"]) <= 200
        if not is_valid:
            errors.append("Length must be 10-200")
        return {"is_valid": is_valid, "errors": errors}

    subgraph = StateGraph(ValidationState)
    subgraph.add_node("validate", validate_content)
    return subgraph.compile()

def create_email_validator():
    """ANTI-PATTERN: Almost identical structure, but duplicated."""
    def validate_content(state: ValidationState) -> dict:
        errors = []
        is_valid = "@" in state["content"]
        if not is_valid:
            errors.append("Invalid email")
        return {"is_valid": is_valid, "errors": errors}

    subgraph = StateGraph(ValidationState)
    subgraph.add_node("validate", validate_content)
    return subgraph.compile()

# Lots of duplication! What if we need to change ValidationState?
```

**Why it fails**:
- Code duplication across validators
- Cannot configure min/max length
- Hard to maintain (change one, change all)
- No reusability

**Guideline**: When creating multiple similar subgraphs, extract a factory function with parameters.

## Summary Checklist

When creating a subgraph, verify:

- [ ] **Clear Boundary**: Single, well-defined responsibility
- [ ] **Minimal Coupling**: Only shares needed state fields
- [ ] **Type Safety**: Uses TypedDict for state schema
- [ ] **Error Handling**: Wraps invocations in try-except with context
- [ ] **Independent Tests**: Has unit tests separate from integration tests
- [ ] **Documented Contract**: Input/output state and behavior documented
- [ ] **Schema Choice**: Uses shared schema unless different schema needed for separation
- [ ] **Reusability**: Uses factory function if multiple similar subgraphs needed

## Common Anti-Patterns to Avoid

1. **God Subgraph**: One subgraph doing fraud, inventory, payment, and notifications
2. **State Leakage**: Passing entire parent state when child only needs 2 fields
3. **Type Blindness**: Using `dict` instead of TypedDict
4. **Silent Failures**: Not handling exceptions or checking for errors
5. **Integration-Only Testing**: Only testing full workflow, no subgraph unit tests
6. **Undocumented Contracts**: No state contract documentation
7. **Premature Abstraction**: Different schemas when shared would work fine
8. **Copy-Paste Factories**: Duplicating similar subgraphs instead of parametrizing

## Related Resources

- **SKILL.md**: Quick reference and core concepts
- **core-patterns.md**: Pattern catalog with code examples
- **complete-examples.md**: Full production-ready systems
- **state-mapping-patterns.md**: State transformation techniques
- **component-library-design.md**: Component architecture patterns
