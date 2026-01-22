# State Mapping Patterns for LangGraph Subgraphs

## Introduction

### What is State Mapping?

State mapping is the process of transforming state data between a parent graph and a subgraph when they use different state schemas. This is essential when:

- Subgraphs need to be reusable across different parent graphs
- Different domains require different data models
- You want to isolate subgraph concerns from parent graph details
- Legacy subgraphs need to integrate with new parent graphs

### When to Use Different Schemas vs Shared Schemas

**Use shared schemas when:**
- Parent and subgraph are tightly coupled
- They represent the same domain
- You want minimal overhead
- State structure is stable

**Use different schemas (requiring mapping) when:**
- Subgraph is reusable across multiple parents
- Subgraph represents a distinct domain
- You want to decouple implementations
- You need to adapt legacy components

### Overview of Transformation Patterns

State mapping involves two key transformations:
1. **Parent → Child (Input)**: Extract and transform parent state for subgraph execution
2. **Child → Parent (Output)**: Merge subgraph results back into parent state

---

## Basic Transformation Patterns

### 1. Field Extraction

Extract specific fields from parent state, discarding others.

```python
from typing import TypedDict

class ParentState(TypedDict):
    user_id: str
    query: str
    context: dict
    metadata: dict
    timestamp: str

class ChildState(TypedDict):
    query: str
    context: dict

def extract_fields(parent: ParentState) -> ChildState:
    """Extract only fields needed by child graph."""
    return {
        "query": parent["query"],
        "context": parent["context"]
    }
```

### 2. Field Renaming

Map fields with different names between schemas.

```python
class ParentState(TypedDict):
    user_message: str
    chat_history: list

class ChildState(TypedDict):
    input_text: str
    history: list

def rename_fields(parent: ParentState) -> ChildState:
    """Map parent field names to child field names."""
    return {
        "input_text": parent["user_message"],
        "history": parent["chat_history"]
    }
```

### 3. Type Conversion

Convert between compatible but different types.

```python
from datetime import datetime

class ParentState(TypedDict):
    timestamp: datetime  # datetime object
    count: str  # string number

class ChildState(TypedDict):
    timestamp: str  # ISO string
    count: int  # actual integer

def convert_types(parent: ParentState) -> ChildState:
    """Convert types between parent and child schemas."""
    return {
        "timestamp": parent["timestamp"].isoformat(),
        "count": int(parent["count"])
    }
```

### 4. Default Values

Handle missing or optional fields with defaults.

```python
from typing import Optional

class ParentState(TypedDict):
    query: str
    max_results: Optional[int]  # May be None

class ChildState(TypedDict):
    query: str
    max_results: int  # Required, never None

def with_defaults(parent: ParentState) -> ChildState:
    """Provide defaults for missing fields."""
    return {
        "query": parent["query"],
        "max_results": parent.get("max_results") or 10
    }
```

---

## Advanced Transformation Patterns

### 1. Nested State Flattening

Convert nested structures to flat state.

```python
class ParentState(TypedDict):
    user: dict  # {"id": "123", "name": "Alice", "email": "alice@example.com"}
    settings: dict  # {"theme": "dark", "language": "en"}

class ChildState(TypedDict):
    user_id: str
    user_name: str
    theme: str
    language: str

def flatten_nested(parent: ParentState) -> ChildState:
    """Flatten nested structures into flat fields."""
    return {
        "user_id": parent["user"]["id"],
        "user_name": parent["user"]["name"],
        "theme": parent["settings"]["theme"],
        "language": parent["settings"]["language"]
    }

# Reverse operation: nest flat state
def nest_flat(child: ChildState) -> dict:
    """Reconstruct nested structures from flat fields."""
    return {
        "user": {
            "id": child["user_id"],
            "name": child["user_name"]
        },
        "settings": {
            "theme": child["theme"],
            "language": child["language"]
        }
    }
```

### 2. State Aggregation

Combine multiple fields into a single field.

```python
class ParentState(TypedDict):
    first_name: str
    last_name: str
    age: int
    city: str

class ChildState(TypedDict):
    full_name: str
    user_info: str

def aggregate_fields(parent: ParentState) -> ChildState:
    """Combine multiple fields into aggregated values."""
    return {
        "full_name": f"{parent['first_name']} {parent['last_name']}",
        "user_info": f"{parent['first_name']} {parent['last_name']}, {parent['age']}, {parent['city']}"
    }
```

### 3. Conditional Mapping

Apply different transformations based on state values.

```python
class ParentState(TypedDict):
    mode: str  # "simple" or "advanced"
    data: dict

class ChildState(TypedDict):
    processed_data: dict

def conditional_mapping(parent: ParentState) -> ChildState:
    """Apply different transformations based on mode."""
    if parent["mode"] == "simple":
        # Simple mode: extract subset of data
        processed = {
            "value": parent["data"].get("value", 0)
        }
    else:
        # Advanced mode: include full data with computed fields
        processed = {
            **parent["data"],
            "computed": parent["data"].get("value", 0) * 2
        }

    return {"processed_data": processed}
```

### 4. Batch Processing

Transform lists of items with per-item transformations.

```python
class ParentState(TypedDict):
    documents: list[dict]  # [{"id": "1", "text": "...", "meta": {...}}]

class ChildState(TypedDict):
    doc_ids: list[str]
    doc_texts: list[str]

def batch_transform(parent: ParentState) -> ChildState:
    """Transform list of items into separate lists."""
    return {
        "doc_ids": [doc["id"] for doc in parent["documents"]],
        "doc_texts": [doc["text"] for doc in parent["documents"]]
    }

# Reverse: reconstruct items from separate lists
def batch_reconstruct(child: ChildState) -> dict:
    """Reconstruct items from separate lists."""
    documents = [
        {"id": doc_id, "text": text}
        for doc_id, text in zip(child["doc_ids"], child["doc_texts"])
    ]
    return {"documents": documents}
```

---

## Bi-Directional Mapping

### Parent → Child: Input Transformation

```python
from langgraph.graph import StateGraph

class ParentState(TypedDict):
    user_query: str
    user_context: dict
    session_id: str
    results: list  # Will be populated by subgraph

class ChildState(TypedDict):
    query: str
    context: dict
    findings: list

def parent_to_child(parent: ParentState) -> ChildState:
    """Transform parent state for subgraph input."""
    return {
        "query": parent["user_query"],
        "context": parent["user_context"],
        "findings": []  # Initialize empty
    }

# Build subgraph
child_graph = StateGraph(ChildState)
# ... add nodes ...
child_compiled = child_graph.compile()

# Add subgraph to parent with input transformation
parent_graph = StateGraph(ParentState)
parent_graph.add_node(
    "research",
    lambda state: child_compiled.invoke(parent_to_child(state))
)
```

### Child → Parent: Output Transformation

```python
def child_to_parent(child_output: ChildState) -> dict:
    """Transform subgraph output for parent state update."""
    return {
        "results": child_output["findings"]
    }

# Combined transformation node
def research_node(state: ParentState) -> dict:
    """Execute subgraph and transform output."""
    # Transform input
    child_input = parent_to_child(state)

    # Execute subgraph
    child_output = child_compiled.invoke(child_input)

    # Transform output
    parent_update = child_to_parent(child_output)

    return parent_update
```

### Round-Trip Consistency

Ensure data integrity when transforming back and forth.

```python
def validate_round_trip(original: ParentState) -> bool:
    """Verify data isn't lost during transformations."""
    # Transform to child
    child = parent_to_child(original)

    # Transform back (partial, since child has different schema)
    # This validates that critical data is preserved

    # Check critical fields preserved
    return (
        child["query"] == original["user_query"] and
        child["context"] == original["user_context"]
    )

# Test round-trip consistency
test_state = {
    "user_query": "test query",
    "user_context": {"key": "value"},
    "session_id": "123",
    "results": []
}
assert validate_round_trip(test_state), "Round-trip validation failed"
```

---

## Edge Cases and Error Handling

### 1. Missing Required Fields

```python
class ParentState(TypedDict):
    query: str
    context: dict  # Optional in practice

class ChildState(TypedDict):
    query: str
    context: dict  # Required

def safe_field_extraction(parent: ParentState) -> ChildState:
    """Handle missing required fields with validation."""
    if "query" not in parent:
        raise ValueError("Required field 'query' missing from parent state")

    # Provide default for optional parent field that's required in child
    context = parent.get("context", {})
    if not context:
        context = {"default": True}

    return {
        "query": parent["query"],
        "context": context
    }
```

### 2. Type Mismatches

```python
def safe_type_conversion(parent: ParentState) -> ChildState:
    """Handle type conversion with error handling."""
    try:
        count = int(parent["count"])
    except (ValueError, TypeError) as e:
        # Log error and use default
        print(f"Warning: Failed to convert count: {e}")
        count = 0

    try:
        timestamp = parent["timestamp"].isoformat()
    except (AttributeError, TypeError) as e:
        # Use current time as fallback
        print(f"Warning: Invalid timestamp: {e}")
        timestamp = datetime.now().isoformat()

    return {
        "count": count,
        "timestamp": timestamp
    }
```

### 3. State Version Compatibility

```python
class ParentStateV1(TypedDict):
    query: str

class ParentStateV2(TypedDict):
    query: str
    enhanced_mode: bool  # New field in V2

class ChildState(TypedDict):
    query: str
    use_enhancement: bool

def version_aware_mapping(parent: dict) -> ChildState:
    """Handle different parent state versions."""
    # Detect version
    has_enhanced_mode = "enhanced_mode" in parent

    return {
        "query": parent["query"],
        "use_enhancement": parent.get("enhanced_mode", False)
    }
```

### 4. Large State Objects

```python
from typing import Any

def efficient_large_state_mapping(parent: ParentState) -> ChildState:
    """Handle large state objects efficiently."""
    # ❌ BAD: Deep copying large objects unnecessarily
    # child = {
    #     "data": copy.deepcopy(parent["large_data"])
    # }

    # ✅ GOOD: Reference shared data when possible
    # Only copy if child will modify the data
    child = {
        "query": parent["query"],
        "data_ref": parent["large_data"]  # Reference, not copy
    }

    return child

# If child needs to modify data, copy only what's needed
def efficient_selective_copy(parent: ParentState) -> ChildState:
    """Copy only fields that will be modified."""
    return {
        "query": parent["query"],
        "items": parent["large_list"][:10]  # Copy only first 10 items
    }
```

---

## Best Practices

### 1. Minimize Transformation Complexity

```python
# ❌ BAD: Complex, hard-to-maintain transformation
def complex_transform(parent: ParentState) -> ChildState:
    data = parent["data"]
    processed = {}
    for key, value in data.items():
        if isinstance(value, dict):
            for k, v in value.items():
                processed[f"{key}_{k}"] = v
        else:
            processed[key] = value
    return {"data": processed}

# ✅ GOOD: Simple, clear transformation with helper
def flatten_dict(data: dict, prefix: str = "") -> dict:
    """Helper to flatten nested dictionary."""
    result = {}
    for key, value in data.items():
        new_key = f"{prefix}_{key}" if prefix else key
        if isinstance(value, dict):
            result.update(flatten_dict(value, new_key))
        else:
            result[new_key] = value
    return result

def simple_transform(parent: ParentState) -> ChildState:
    """Simple transformation using helper."""
    return {"data": flatten_dict(parent["data"])}
```

### 2. Validate Transformed State

```python
from pydantic import BaseModel, ValidationError

class ChildStateModel(BaseModel):
    query: str
    count: int
    timestamp: str

def validated_transform(parent: ParentState) -> ChildState:
    """Validate transformed state before returning."""
    transformed = {
        "query": parent["query"],
        "count": int(parent["count"]),
        "timestamp": parent["timestamp"].isoformat()
    }

    # Validate with Pydantic
    try:
        ChildStateModel(**transformed)
    except ValidationError as e:
        raise ValueError(f"Transformation produced invalid state: {e}")

    return transformed
```

### 3. Document Transformation Logic

```python
def transform_user_state(parent: ParentState) -> ChildState:
    """
    Transform parent user state to child processing state.

    Transformations applied:
    - user_message → input_text: Direct field rename
    - chat_history → history: Direct field rename, preserves list order
    - timestamp: Converts datetime to ISO 8601 string
    - max_results: Defaults to 10 if not provided

    Args:
        parent: Parent state with user interaction data

    Returns:
        Child state ready for processing subgraph

    Raises:
        ValueError: If required fields are missing
    """
    if "user_message" not in parent:
        raise ValueError("user_message is required")

    return {
        "input_text": parent["user_message"],
        "history": parent.get("chat_history", []),
        "timestamp": parent.get("timestamp", datetime.now()).isoformat(),
        "max_results": parent.get("max_results", 10)
    }
```

### 4. Test Transformations Independently

```python
import pytest

def test_basic_transformation():
    """Test basic field extraction and renaming."""
    parent = {
        "user_message": "hello",
        "chat_history": [{"role": "user", "content": "hi"}],
        "session_id": "123"
    }

    child = transform_user_state(parent)

    assert child["input_text"] == "hello"
    assert len(child["history"]) == 1
    assert "timestamp" in child
    assert child["max_results"] == 10

def test_transformation_with_defaults():
    """Test default value handling."""
    parent = {"user_message": "hello"}
    child = transform_user_state(parent)

    assert child["history"] == []
    assert child["max_results"] == 10

def test_transformation_validation():
    """Test that invalid input raises errors."""
    with pytest.raises(ValueError):
        transform_user_state({})  # Missing required field
```

### 5. Use Factory Functions for Reusable Transformers

```python
from typing import Callable

def create_field_mapper(
    field_mapping: dict[str, str],
    defaults: dict[str, Any] = None
) -> Callable[[dict], dict]:
    """
    Factory to create field mapping transformers.

    Args:
        field_mapping: {child_field: parent_field} mapping
        defaults: Default values for optional fields

    Returns:
        Transformation function
    """
    defaults = defaults or {}

    def mapper(parent: dict) -> dict:
        result = {}
        for child_field, parent_field in field_mapping.items():
            if parent_field in parent:
                result[child_field] = parent[parent_field]
            elif child_field in defaults:
                result[child_field] = defaults[child_field]
            else:
                raise ValueError(f"Required field {parent_field} not found")
        return result

    return mapper

# Create reusable transformers
user_to_processor = create_field_mapper(
    field_mapping={
        "input_text": "user_message",
        "history": "chat_history"
    },
    defaults={"history": [], "max_results": 10}
)

# Use transformer
child_state = user_to_processor(parent_state)
```

---

## Common Pitfalls

### 1. Over-Complex Transformations

```python
# ❌ BAD: Transformation does too much
def kitchen_sink_transform(parent: ParentState) -> ChildState:
    # Extracts fields
    # Validates data
    # Calls external services
    # Performs business logic
    # ...100 lines later...
    return child_state

# ✅ GOOD: Transformation only transforms
def clean_transform(parent: ParentState) -> ChildState:
    """Only transform data structure, no business logic."""
    return {
        "query": parent["user_query"],
        "context": parent["user_context"]
    }

# Put business logic in graph nodes
def validation_node(state: ChildState) -> dict:
    """Separate node for validation logic."""
    # Validation logic here
    return state
```

### 2. Loss of Data During Mapping

```python
# ❌ BAD: Data lost during transformation
class ParentState(TypedDict):
    user_id: str
    query: str
    important_metadata: dict  # Lost!

class ChildState(TypedDict):
    query: str

def lossy_transform(parent: ParentState) -> ChildState:
    return {"query": parent["query"]}
    # user_id and important_metadata are lost!

# ✅ GOOD: Preserve needed data or explicitly document loss
class ChildState(TypedDict):
    query: str
    metadata: dict  # Preserved

def preserving_transform(parent: ParentState) -> ChildState:
    """
    Transform parent to child.

    Note: user_id is intentionally not passed to child as it's not
    needed for processing and is maintained in parent state.
    """
    return {
        "query": parent["query"],
        "metadata": parent["important_metadata"]
    }
```

### 3. Performance Issues with Large States

```python
import copy

# ❌ BAD: Unnecessary deep copying
def slow_transform(parent: ParentState) -> ChildState:
    return {
        "data": copy.deepcopy(parent["large_data"])  # Slow!
    }

# ✅ GOOD: Reference when possible, shallow copy when needed
def fast_transform(parent: ParentState) -> ChildState:
    return {
        "data": parent["large_data"]  # Reference if read-only
    }

# If modification is needed, copy only what changes
def selective_copy_transform(parent: ParentState) -> ChildState:
    return {
        "data": parent["large_data"].copy()  # Shallow copy
    }
```

### 4. Missing Error Handling

```python
# ❌ BAD: No error handling
def fragile_transform(parent: ParentState) -> ChildState:
    return {
        "count": int(parent["count"]),  # May raise ValueError
        "timestamp": parent["timestamp"].isoformat()  # May raise AttributeError
    }

# ✅ GOOD: Explicit error handling
def robust_transform(parent: ParentState) -> ChildState:
    """Transform with comprehensive error handling."""
    # Validate required fields
    if "count" not in parent:
        raise ValueError("Missing required field: count")

    # Safe type conversion
    try:
        count = int(parent["count"])
    except (ValueError, TypeError) as e:
        raise ValueError(f"Invalid count value: {e}")

    # Safe method call
    try:
        timestamp = parent["timestamp"].isoformat()
    except AttributeError as e:
        raise ValueError(f"Invalid timestamp object: {e}")

    return {
        "count": count,
        "timestamp": timestamp
    }
```

---

## Complete Examples

### Example 1: E-Commerce Order Processing

```python
from typing import TypedDict, Literal
from langgraph.graph import StateGraph, END

# Parent graph: Order management system
class OrderState(TypedDict):
    order_id: str
    customer_email: str
    items: list[dict]  # [{"sku": "...", "qty": 1, "price": 9.99}]
    total_amount: float
    payment_status: Literal["pending", "completed", "failed"]
    shipping_address: dict
    processed: bool

# Child graph: Payment processing
class PaymentState(TypedDict):
    transaction_id: str
    amount: float
    customer_email: str
    status: Literal["processing", "success", "failed"]
    error_message: str

# Transformations
def order_to_payment(order: OrderState) -> PaymentState:
    """Extract payment-relevant data from order."""
    return {
        "transaction_id": f"txn_{order['order_id']}",
        "amount": order["total_amount"],
        "customer_email": order["customer_email"],
        "status": "processing",
        "error_message": ""
    }

def payment_to_order(payment: PaymentState) -> dict:
    """Update order with payment results."""
    status_map = {
        "success": "completed",
        "failed": "failed",
        "processing": "pending"
    }
    return {
        "payment_status": status_map[payment["status"]],
        "processed": payment["status"] == "success"
    }

# Build payment subgraph
payment_graph = StateGraph(PaymentState)

def process_payment(state: PaymentState) -> dict:
    """Simulate payment processing."""
    # Payment logic here
    if state["amount"] > 0:
        return {"status": "success"}
    return {"status": "failed", "error_message": "Invalid amount"}

payment_graph.add_node("process", process_payment)
payment_graph.set_entry_point("process")
payment_graph.add_edge("process", END)
payment_compiled = payment_graph.compile()

# Build parent order graph
order_graph = StateGraph(OrderState)

def handle_payment(state: OrderState) -> dict:
    """Execute payment subgraph with state mapping."""
    payment_input = order_to_payment(state)
    payment_output = payment_compiled.invoke(payment_input)
    return payment_to_order(payment_output)

order_graph.add_node("payment", handle_payment)
order_graph.set_entry_point("payment")
order_graph.add_edge("payment", END)
order_compiled = order_graph.compile()

# Execute
order = {
    "order_id": "ORD123",
    "customer_email": "customer@example.com",
    "items": [{"sku": "WIDGET", "qty": 2, "price": 9.99}],
    "total_amount": 19.98,
    "payment_status": "pending",
    "shipping_address": {"street": "123 Main St"},
    "processed": False
}

result = order_compiled.invoke(order)
print(f"Payment status: {result['payment_status']}")
print(f"Order processed: {result['processed']}")
```

### Example 2: Multi-Stage Document Analysis

```python
from typing import TypedDict, Literal
from langgraph.graph import StateGraph, END

# Parent graph: Document processing pipeline
class DocumentState(TypedDict):
    doc_id: str
    raw_text: str
    language: str
    sections: list[dict]  # Will be populated by section extraction
    summary: str  # Will be populated by summarization
    entities: list[str]  # Will be populated by NER
    metadata: dict

# Child graph 1: Section extraction
class SectionState(TypedDict):
    text: str
    sections: list[dict]

def doc_to_section(doc: DocumentState) -> SectionState:
    """Extract text for section analysis."""
    return {
        "text": doc["raw_text"],
        "sections": []
    }

def section_to_doc(section: SectionState) -> dict:
    """Merge section results back."""
    return {"sections": section["sections"]}

# Child graph 2: Summarization (depends on sections)
class SummaryState(TypedDict):
    sections: list[dict]
    summary: str

def doc_to_summary(doc: DocumentState) -> SummaryState:
    """Extract sections for summarization."""
    return {
        "sections": doc["sections"],
        "summary": ""
    }

def summary_to_doc(summary: SummaryState) -> dict:
    """Add summary to document."""
    return {"summary": summary["summary"]}

# Build subgraphs
section_graph = StateGraph(SectionState)

def extract_sections(state: SectionState) -> dict:
    """Simulate section extraction."""
    sections = [
        {"title": "Introduction", "text": state["text"][:100]},
        {"title": "Body", "text": state["text"][100:200]}
    ]
    return {"sections": sections}

section_graph.add_node("extract", extract_sections)
section_graph.set_entry_point("extract")
section_graph.add_edge("extract", END)
section_compiled = section_graph.compile()

summary_graph = StateGraph(SummaryState)

def create_summary(state: SummaryState) -> dict:
    """Simulate summarization."""
    summary = f"Document has {len(state['sections'])} sections"
    return {"summary": summary}

summary_graph.add_node("summarize", create_summary)
summary_graph.set_entry_point("summarize")
summary_graph.add_edge("summarize", END)
summary_compiled = summary_graph.compile()

# Build parent graph with sequential subgraphs
doc_graph = StateGraph(DocumentState)

def section_node(state: DocumentState) -> dict:
    """Extract sections subgraph."""
    section_input = doc_to_section(state)
    section_output = section_compiled.invoke(section_input)
    return section_to_doc(section_output)

def summary_node(state: DocumentState) -> dict:
    """Summarization subgraph."""
    summary_input = doc_to_summary(state)
    summary_output = summary_compiled.invoke(summary_input)
    return summary_to_doc(summary_output)

doc_graph.add_node("sections", section_node)
doc_graph.add_node("summary", summary_node)
doc_graph.set_entry_point("sections")
doc_graph.add_edge("sections", "summary")
doc_graph.add_edge("summary", END)
doc_compiled = doc_graph.compile()

# Execute
document = {
    "doc_id": "DOC001",
    "raw_text": "Long document text here..." * 20,
    "language": "en",
    "sections": [],
    "summary": "",
    "entities": [],
    "metadata": {"source": "upload"}
}

result = doc_compiled.invoke(document)
print(f"Extracted {len(result['sections'])} sections")
print(f"Summary: {result['summary']}")
```

### Example 3: Conditional Transformation Based on State

```python
from typing import TypedDict, Literal
from langgraph.graph import StateGraph, END

# Parent graph: Request router
class RequestState(TypedDict):
    request_type: Literal["simple", "complex"]
    query: str
    context: dict
    result: str

# Child graph 1: Simple processing
class SimpleState(TypedDict):
    query: str
    result: str

# Child graph 2: Complex processing
class ComplexState(TypedDict):
    query: str
    context: dict
    intermediate_results: list[str]
    result: str

# Conditional transformations
def request_to_processor(request: RequestState) -> dict:
    """Route to different subgraph based on request type."""
    if request["request_type"] == "simple":
        return {
            "type": "simple",
            "state": {
                "query": request["query"],
                "result": ""
            }
        }
    else:
        return {
            "type": "complex",
            "state": {
                "query": request["query"],
                "context": request["context"],
                "intermediate_results": [],
                "result": ""
            }
        }

def processor_to_request(processor_output: dict, output_type: str) -> dict:
    """Merge results back regardless of which subgraph ran."""
    if output_type == "simple":
        return {"result": processor_output["result"]}
    else:
        return {"result": processor_output["result"]}

# Build subgraphs
simple_graph = StateGraph(SimpleState)
simple_graph.add_node("process", lambda s: {"result": f"Simple: {s['query']}"})
simple_graph.set_entry_point("process")
simple_graph.add_edge("process", END)
simple_compiled = simple_graph.compile()

complex_graph = StateGraph(ComplexState)
complex_graph.add_node("process", lambda s: {
    "intermediate_results": ["step1", "step2"],
    "result": f"Complex: {s['query']} with {s['context']}"
})
complex_graph.set_entry_point("process")
complex_graph.add_edge("process", END)
complex_compiled = complex_graph.compile()

# Parent graph with conditional routing
request_graph = StateGraph(RequestState)

def route_and_process(state: RequestState) -> dict:
    """Conditionally transform and execute appropriate subgraph."""
    routing = request_to_processor(state)

    if routing["type"] == "simple":
        output = simple_compiled.invoke(routing["state"])
    else:
        output = complex_compiled.invoke(routing["state"])

    return processor_to_request(output, routing["type"])

request_graph.add_node("process", route_and_process)
request_graph.set_entry_point("process")
request_graph.add_edge("process", END)
request_compiled = request_graph.compile()

# Test both paths
simple_request = {
    "request_type": "simple",
    "query": "hello",
    "context": {},
    "result": ""
}
print(request_compiled.invoke(simple_request)["result"])

complex_request = {
    "request_type": "complex",
    "query": "hello",
    "context": {"key": "value"},
    "result": ""
}
print(request_compiled.invoke(complex_request)["result"])
```

---

## Related Documentation

- **Main Skill Guide**: `/langgraph-dev/skills/subgraphs-and-composition/SKILL.md`
- **Basic Examples**: `/langgraph-dev/skills/subgraphs-and-composition/examples/01-basic-subgraph.py`
- **State Schemas Example**: `/langgraph-dev/skills/subgraphs-and-composition/examples/02-different-state-schemas.py`
- **LangGraph Guide**: `/.claude/rules/frameworks/langgraph-guide.md`
