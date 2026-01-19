# Core Subgraph Composition Patterns

This reference provides comprehensive patterns for composing LangGraph applications using subgraphs. These patterns range from basic shared-state composition to advanced dynamic routing and parallel execution.

## Pattern Categories

- **Basic Patterns**: Foundation patterns for simple parent-child relationships
- **Intermediate Patterns**: State mapping, error handling, and multi-level hierarchies
- **Advanced Patterns**: Factory functions, registries, parallel execution, and conditional routing

## Basic Patterns

### Direct Subgraph with Shared State

When parent and child graphs share the same state schema (like `MessagesState`), you can add compiled subgraphs directly as nodes without any wrapper.

```python
from langgraph.graph import StateGraph, START, END, MessagesState
from langchain_core.messages import SystemMessage

def analyze_sentiment(state: MessagesState) -> MessagesState:
    """Analyze sentiment of the last message."""
    last_message = state["messages"][-1].content.lower()

    if "happy" in last_message or "great" in last_message:
        sentiment = "positive"
    elif "sad" in last_message or "bad" in last_message:
        sentiment = "negative"
    else:
        sentiment = "neutral"

    analysis_message = SystemMessage(content=f"[Sentiment Analysis: {sentiment}]")
    return {"messages": [analysis_message]}

def create_sentiment_subgraph():
    """Create the sentiment analysis subgraph."""
    subgraph = StateGraph(MessagesState)
    subgraph.add_node("analyze", analyze_sentiment)
    subgraph.add_edge(START, "analyze")
    subgraph.add_edge("analyze", END)
    return subgraph.compile()

# Use in parent graph
chatbot = StateGraph(MessagesState)
chatbot.add_node("sentiment", create_sentiment_subgraph())  # Direct usage
chatbot.add_node("respond", generate_response)
chatbot.add_edge(START, "sentiment")
chatbot.add_edge("sentiment", "respond")
chatbot.add_edge("respond", END)
```

**When to use**:
- Parent and child work with the same state keys
- Simple integration without transformation
- Chat-based multi-agent systems with MessagesState

### Simple State Transformation Wrapper

When parent and child have different state schemas, create a wrapper function that transforms state before and after invoking the subgraph.

```python
from typing import TypedDict

class DocumentState(TypedDict):
    text: str
    word_count: int
    processed: bool

class WorkflowState(TypedDict):
    documents: list[str]
    results: list[dict]

def create_document_processor_wrapper():
    """Wrapper bridges WorkflowState and DocumentState."""
    doc_processor = create_document_processor()  # Compiled subgraph

    def process_document_batch(state: WorkflowState) -> dict:
        """Process each document through subgraph."""
        results = []

        for doc_text in state["documents"]:
            # Transform to subgraph schema
            subgraph_input = {
                "text": doc_text,
                "word_count": 0,
                "processed": False
            }

            # Invoke subgraph
            subgraph_output = doc_processor.invoke(subgraph_input)

            # Transform back to parent schema
            results.append({
                "word_count": subgraph_output["word_count"],
                "processed": subgraph_output["processed"]
            })

        return {"results": results}

    return process_document_batch
```

**When to use**:
- Parent and child have different but straightforward schema mappings
- Batch processing where parent iterates over child invocations
- Simple field extraction and result aggregation

### Two-Level Hierarchy

Basic pattern for composing a parent graph that contains a child subgraph, forming a two-level hierarchy.

```python
from langgraph.graph import StateGraph, START, END, MessagesState

# Child Graph (Level 2)
def create_sentiment_subgraph():
    """Child graph that analyzes sentiment."""
    subgraph = StateGraph(MessagesState)
    subgraph.add_node("analyze", analyze_sentiment)
    subgraph.add_edge(START, "analyze")
    subgraph.add_edge("analyze", END)
    return subgraph.compile()

# Parent Graph (Level 1)
def create_chatbot():
    """Parent graph that uses sentiment subgraph."""
    sentiment_subgraph = create_sentiment_subgraph()

    chatbot = StateGraph(MessagesState)
    chatbot.add_node("sentiment", sentiment_subgraph)  # Add child as node
    chatbot.add_node("respond", generate_response)

    chatbot.add_edge(START, "sentiment")
    chatbot.add_edge("sentiment", "respond")
    chatbot.add_edge("respond", END)

    return chatbot.compile()

# State flows: Parent → Child → Parent
chatbot = create_chatbot()
result = chatbot.invoke({"messages": [HumanMessage(content="I'm happy!")]})
```

**When to use**:
- Simple hierarchical decomposition of workflows
- Isolating specific functionality for reuse
- Testing child components independently

## Intermediate Patterns

### State Mapping with Field Renaming

Transform state between parent and child while renaming fields to match different naming conventions or structures.

```python
from typing import TypedDict

class ParentState(TypedDict):
    content: str  # Field name in parent
    validation_results: list[dict]

class ChildState(TypedDict):
    content: str  # Same name
    is_valid: bool
    errors: list[str]

def create_validation_wrapper(validator_graph):
    """Wrapper handles field extraction and renaming."""
    def run_validation(state: ParentState) -> dict:
        # Extract and rename fields for child
        validation_input = {
            "content": state["content"],  # Direct mapping
            "is_valid": True,
            "errors": []
        }

        # Invoke child
        result = validator_graph.invoke(validation_input)

        # Rename and package for parent
        validation_result = {
            "validator": "ContentValidator",
            "is_valid": result["is_valid"],  # Rename to nested structure
            "errors": result["errors"]
        }

        return {"validation_results": [validation_result]}

    return run_validation
```

**When to use**:
- Field names differ between parent and child
- Aggregating multiple validation results
- Nested result structures in parent

### Subgraph with Partial State Extraction

Extract only the fields needed by the subgraph, ignoring unnecessary parent state fields.

```python
from typing import TypedDict

class WorkflowState(TypedDict):
    documents: list[str]
    results: list[dict]
    total_words: int
    metadata: dict  # Not needed by subgraph

class DocumentState(TypedDict):
    text: str
    word_count: int

def create_document_processor_wrapper():
    """Extract only needed fields for subgraph."""
    doc_processor = create_document_processor()

    def process_batch(state: WorkflowState) -> dict:
        results = []
        total_words = 0

        for doc_text in state["documents"]:
            # PARTIAL EXTRACTION: Only extract 'text', ignore 'metadata'
            subgraph_input = {
                "text": doc_text,  # Extract only this field
                "word_count": 0
            }

            subgraph_output = doc_processor.invoke(subgraph_input)

            # Partial update: Only update 'results' and 'total_words'
            word_count = subgraph_output["word_count"]
            total_words += word_count

            results.append({"word_count": word_count})

        # Return partial state update (metadata unchanged)
        return {
            "results": results,
            "total_words": total_words
        }

    return process_batch
```

**When to use**:
- Parent has more state fields than child needs
- Reducing coupling between parent and child
- Performance optimization (smaller state payloads)

### Error Propagation from Child to Parent

Handle errors from child subgraphs and propagate them to parent with appropriate context.

```python
from typing import TypedDict

class ChildState(TypedDict):
    content: str
    is_valid: bool
    errors: list[str]

class ParentState(TypedDict):
    content: str
    status: str  # "success" or "failed"
    error_messages: list[str]

def create_validator_wrapper():
    """Wrapper propagates errors from child to parent."""
    validator = create_validator_subgraph()

    def validate_with_error_handling(state: ParentState) -> dict:
        try:
            # Invoke child subgraph
            result = validator.invoke({
                "content": state["content"],
                "is_valid": True,
                "errors": []
            })

            # Propagate errors from child to parent
            if not result["is_valid"]:
                return {
                    "status": "failed",
                    "error_messages": result["errors"]  # Propagate child errors
                }

            return {"status": "success", "error_messages": []}

        except Exception as e:
            # Handle subgraph exceptions
            return {
                "status": "failed",
                "error_messages": [f"Validation error: {str(e)}"]
            }

    return validate_with_error_handling
```

**When to use**:
- Robust error handling across graph boundaries
- Debugging multi-agent systems
- Graceful degradation when child fails

### Multi-Level Nesting

Create hierarchies of 3+ levels where children contain their own child subgraphs.

```python
from langgraph.graph import StateGraph, START, END, MessagesState
from langchain_core.messages import SystemMessage

# ============================================================================
# Level 3: Grandchild - Keyword Extractor
# ============================================================================

def extract_keywords(state: MessagesState) -> dict:
    """Extract keywords (Level 3 - deepest)."""
    last_message = state["messages"][-1].content.lower()
    words = last_message.split()
    keywords = [word for word in words if len(word) > 5][:3]

    keyword_message = SystemMessage(content=f"[Keywords: {', '.join(keywords)}]")
    return {"messages": [keyword_message]}

def create_keyword_extractor():
    """Create grandchild subgraph."""
    subgraph = StateGraph(MessagesState)
    subgraph.add_node("extract", extract_keywords)
    subgraph.add_edge(START, "extract")
    subgraph.add_edge("extract", END)
    return subgraph.compile()

# ============================================================================
# Level 2: Child - Topic Analyzer (contains grandchild)
# ============================================================================

def identify_topic(state: MessagesState) -> dict:
    """Identify topic (Level 2)."""
    last_message = state["messages"][-1].content.lower()
    topic = "AI" if "machine learning" in last_message else "General"
    topic_message = SystemMessage(content=f"[Topic: {topic}]")
    return {"messages": [topic_message]}

def create_topic_analyzer():
    """Create child subgraph that contains grandchild."""
    keyword_extractor = create_keyword_extractor()  # Nested grandchild

    subgraph = StateGraph(MessagesState)
    subgraph.add_node("identify", identify_topic)
    subgraph.add_node("extract_keywords", keyword_extractor)  # Add grandchild as node
    subgraph.add_edge(START, "identify")
    subgraph.add_edge("identify", "extract_keywords")
    subgraph.add_edge("extract_keywords", END)

    return subgraph.compile()

# ============================================================================
# Level 1: Parent - Research Coordinator
# ============================================================================

def create_research_coordinator():
    """Create parent that uses child (which uses grandchild)."""
    topic_analyzer = create_topic_analyzer()  # Child contains grandchild

    workflow = StateGraph(MessagesState)
    workflow.add_node("analyze", topic_analyzer)  # Add child as node
    workflow.add_node("plan", generate_research_plan)
    workflow.add_edge(START, "analyze")
    workflow.add_edge("analyze", "plan")
    workflow.add_edge("plan", END)

    return workflow.compile()

# State flows: Parent → Child → Grandchild → Child → Parent
```

**When to use**:
- Complex hierarchical agent architectures
- Specialized sub-agents with their own sub-components
- Deep domain decomposition

## Advanced Patterns

### Graph Factory Functions for Reusable Components

Use factory functions to create parametrized subgraphs with different configurations from the same template.

```python
from typing import TypedDict, Callable, Any
from langgraph.graph import StateGraph, START, END

class ValidationState(TypedDict):
    content: str
    is_valid: bool
    errors: list[str]

def create_validator_subgraph(
    name: str,
    rules: list[Callable[[str], tuple[bool, str]]]
) -> Any:
    """
    Factory function to create parametrized validator subgraphs.

    Args:
        name: Name of the validator
        rules: List of validation functions that return (is_valid, error_message)

    Returns:
        Compiled StateGraph configured with the specified rules
    """

    def validate_content(state: ValidationState) -> dict:
        """Apply all validation rules (dynamically created)."""
        errors = []
        is_valid = True

        for rule in rules:
            rule_valid, error_msg = rule(state["content"])
            if not rule_valid:
                is_valid = False
                errors.append(error_msg)

        print(f"  {name}: {'✓ PASS' if is_valid else '✗ FAIL'}")
        return {"is_valid": is_valid, "errors": errors}

    # Create subgraph with validation logic
    subgraph = StateGraph(ValidationState)
    subgraph.add_node("validate", validate_content)
    subgraph.add_edge(START, "validate")
    subgraph.add_edge("validate", END)

    return subgraph.compile()

# Example: Create multiple validators from same factory
def length_rule(min_len: int, max_len: int):
    """Rule factory for length validation."""
    def validate(content: str) -> tuple[bool, str]:
        length = len(content)
        if length < min_len or length > max_len:
            return False, f"Length must be {min_len}-{max_len}"
        return True, ""
    return validate

# Create different validators using factory pattern
length_validator = create_validator_subgraph("Length", [length_rule(10, 200)])
email_validator = create_validator_subgraph("Email", [email_format_rule()])
profanity_validator = create_validator_subgraph("Profanity", [profanity_rule()])
```

**When to use**:
- Building component libraries for reuse across projects
- Parametrizing behavior while maintaining same graph structure
- Reducing boilerplate for similar subgraphs

### Graph Registry Pattern for Dynamic Composition

Implement a registry to manage and dynamically compose subgraph components at runtime.

```python
from typing import Dict, Any, Callable
from langgraph.graph import StateGraph

class SubgraphRegistry:
    """Registry for managing reusable subgraph components."""

    def __init__(self):
        self._factories: Dict[str, Callable] = {}
        self._instances: Dict[str, Any] = {}

    def register(self, name: str, factory: Callable):
        """Register a subgraph factory function."""
        self._factories[name] = factory

    def get(self, name: str, **kwargs) -> Any:
        """Get or create a subgraph instance."""
        cache_key = f"{name}:{str(kwargs)}"

        if cache_key not in self._instances:
            if name not in self._factories:
                raise ValueError(f"Subgraph '{name}' not registered")
            self._instances[cache_key] = self._factories[name](**kwargs)

        return self._instances[cache_key]

# Create global registry
registry = SubgraphRegistry()

# Register subgraph factories
registry.register("validator", create_validator_subgraph)
registry.register("intent_classifier", create_intent_classifier)
registry.register("knowledge_retriever", create_knowledge_retriever)

# Use registry to compose workflows dynamically
def create_dynamic_workflow(components: list[str]):
    """Build workflow from registered components."""
    workflow = StateGraph(MessagesState)

    # Get subgraphs from registry
    if "intent" in components:
        intent_classifier = registry.get("intent_classifier", intents={
            "billing": ["bill", "payment"],
            "technical": ["error", "bug"]
        })
        workflow.add_node("intent", intent_classifier)

    if "validation" in components:
        validator = registry.get("validator", name="Content", rules=[length_rule(10, 200)])
        workflow.add_node("validate", validator)

    return workflow.compile()

# Dynamic composition based on configuration
workflow = create_dynamic_workflow(["intent", "validation"])
```

**When to use**:
- Configuration-driven workflow composition
- Plugin-based architectures
- Runtime workflow customization

### Parallel Subgraphs with Independent Schemas

Execute multiple subgraphs in parallel, each with their own state schema, then merge results.

```python
from typing import TypedDict, Literal
from langgraph.graph import StateGraph, START, END

# Parent state
class OrderState(TypedDict):
    order_id: str
    fraud_score: float
    inventory_available: bool
    status: str

# Independent schemas for parallel subgraphs
class FraudState(TypedDict):
    order_id: str
    total_amount: float
    fraud_score: float

class InventoryState(TypedDict):
    product_ids: list[str]
    quantities: dict[str, int]
    all_available: bool

# Wrappers for parallel execution
def create_fraud_wrapper():
    """Wrapper for fraud detection subgraph."""
    fraud_detector = create_fraud_detector()

    def check_fraud(state: OrderState) -> dict:
        result = fraud_detector.invoke({
            "order_id": state["order_id"],
            "total_amount": 1000.0,
            "fraud_score": 0.0
        })
        return {"fraud_score": result["fraud_score"]}

    return check_fraud

def create_inventory_wrapper():
    """Wrapper for inventory checking subgraph."""
    inventory_checker = create_inventory_checker()

    def check_inventory(state: OrderState) -> dict:
        result = inventory_checker.invoke({
            "product_ids": ["PROD-001"],
            "quantities": {"PROD-001": 1},
            "all_available": False
        })
        return {"inventory_available": result["all_available"]}

    return check_inventory

# Build graph with parallel subgraphs
def create_order_processor():
    """Parallel fraud and inventory checks."""
    processor = StateGraph(OrderState)

    processor.add_node("fraud", create_fraud_wrapper())
    processor.add_node("inventory", create_inventory_wrapper())
    processor.add_node("decide", decide_order_status)

    # Both run in parallel from START
    processor.add_edge(START, "fraud")
    processor.add_edge(START, "inventory")

    # Both must complete before decide
    processor.add_edge("fraud", "decide")
    processor.add_edge("inventory", "decide")
    processor.add_edge("decide", END)

    return processor.compile()
```

**When to use**:
- Independent validations or checks
- Performance optimization through parallelization
- Fan-out/fan-in patterns

### Conditional Subgraph Routing

Route workflow to different subgraphs based on state conditions.

```python
from typing import Literal
from langgraph.graph import StateGraph, START, END

class OrderState(TypedDict):
    order_id: str
    fraud_score: float
    inventory_available: bool
    payment_successful: bool
    status: str

def create_order_processor():
    """Conditional routing to different subgraphs based on state."""
    # Create subgraphs
    fraud_detector = create_fraud_detector()
    inventory_wrapper = create_inventory_wrapper()
    payment_wrapper = create_payment_wrapper()
    notifier = create_notification_dispatcher()

    processor = StateGraph(OrderState)

    # Add nodes
    processor.add_node("init", initialize_order)
    processor.add_node("fraud", fraud_detector)
    processor.add_node("inventory", inventory_wrapper)
    processor.add_node("payment", payment_wrapper)
    processor.add_node("notify", notifier)

    # Conditional routing functions
    def route_after_fraud(state: OrderState) -> Literal["inventory", "notify"]:
        """Route based on fraud check result."""
        if state["status"] == "inventory_check":
            return "inventory"  # Passed fraud check
        return "notify"  # Failed fraud check

    def route_after_inventory(state: OrderState) -> Literal["payment", "notify"]:
        """Route based on inventory check result."""
        if state["status"] == "payment":
            return "payment"  # Inventory available
        return "notify"  # Inventory unavailable

    def route_after_payment(state: OrderState) -> Literal["notify"]:
        """Always proceed to notifications."""
        return "notify"

    # Build graph with conditional edges
    processor.add_edge(START, "init")
    processor.add_edge("init", "fraud")

    # Conditional routing to different subgraphs
    processor.add_conditional_edges("fraud", route_after_fraud)
    processor.add_conditional_edges("inventory", route_after_inventory)
    processor.add_conditional_edges("payment", route_after_payment)

    processor.add_edge("notify", END)

    return processor.compile()
```

**When to use**:
- Workflows with branching logic
- Different processing paths based on validation results
- Early exit patterns

## Pattern Selection Guide

| Use Case | Recommended Pattern |
|----------|---------------------|
| Same state schema | Direct Subgraph with Shared State |
| Different schemas, simple mapping | Simple State Transformation Wrapper |
| Field name differences | State Mapping with Field Renaming |
| Large parent state, small child needs | Partial State Extraction |
| Robust error handling | Error Propagation Pattern |
| Deep hierarchies | Multi-Level Nesting |
| Reusable components | Factory Functions |
| Runtime composition | Registry Pattern |
| Independent parallel tasks | Parallel Subgraphs |
| Branching workflows | Conditional Routing |

## Best Practices

1. **Start simple**: Use shared state when possible before adding transformation complexity
2. **Minimize coupling**: Extract only needed fields in wrappers
3. **Type safety**: Leverage TypedDict for schema validation
4. **Error handling**: Always propagate errors with context
5. **Independent testing**: Test each subgraph in isolation
6. **Document contracts**: Clearly specify input/output state requirements
7. **Prefer factories**: Create parametrized builders for reusable components

## Related Resources

- **SKILL.md**: Core concepts and quick reference
- **complete-examples.md**: Full runnable multi-agent systems
- **best-practices.md**: Detailed best practices and anti-patterns
- **state-mapping-patterns.md**: State transformation techniques
- **component-library-design.md**: Component architecture patterns
