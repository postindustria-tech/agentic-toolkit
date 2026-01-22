---
name: subgraphs-and-composition-in-langgraph
description: This skill should be used when the user asks about "subgraphs", "nested graphs", "graph composition", "compiled graph as node", "graph reuse", "compose graphs", "parent-child state", "state mapping", "modular workflows", "reusable components", "factory pattern for graphs", "graph component library", or needs guidance on composing complex LangGraph applications from reusable subgraph components.
version: 0.1.0
---

# Subgraphs and Composition in LangGraph

## Purpose

This skill provides guidance on building modular LangGraph applications through subgraph composition. Subgraphs enable you to create reusable, independently testable workflow components that can be composed into complex multi-agent systems with clear boundaries and explicit state contracts.

## Compatibility

This skill is compatible with **LangGraph 1.x** (tested with v1.0.6, January 2026).

## When to Use This Skill

Use this skill when:
- Building large multi-agent systems that benefit from modular decomposition
- Creating reusable workflow components across multiple applications
- Managing complex state relationships between parent and child workflows
- Isolating specific functionality for independent testing and optimization
- Scaling teams working on different parts of a workflow system
- Implementing hierarchical agent architectures with specialized sub-agents

## Core Concepts

### 1. Subgraph as Node

A compiled `StateGraph` can be added as a node to another graph. Compiled graphs are callable, making them valid node functions:

```python
from langgraph.graph import StateGraph, START, END, MessagesState

def create_sentiment_subgraph():
    subgraph = StateGraph(MessagesState)
    subgraph.add_node("analyze", analyze_sentiment)
    subgraph.add_edge(START, "analyze")
    subgraph.add_edge("analyze", END)
    return subgraph.compile()

# Add compiled subgraph as a node
chatbot = StateGraph(MessagesState)
chatbot.add_node("sentiment", create_sentiment_subgraph())
chatbot.add_edge(START, "sentiment")
chatbot.add_edge("sentiment", "respond")
chatbot.add_edge("respond", END)
```

### 2. Shared State Schema Communication

Parent and child graphs can share the same state schema for seamless communication:

```python
from langgraph.graph import MessagesState
from langchain_core.messages import SystemMessage

def analyze_sentiment(state: MessagesState) -> dict:
    last_message = state["messages"][-1].content.lower()
    sentiment = "positive" if "happy" in last_message else "neutral"
    return {"messages": [SystemMessage(content=f"[Sentiment: {sentiment}]")]}

# Both parent and child use MessagesState - no transformation needed
subgraph = StateGraph(MessagesState)
subgraph.add_node("analyze", analyze_sentiment)

parent = StateGraph(MessagesState)
parent.add_node("sentiment", subgraph.compile())  # Direct usage
```

### 3. Different State Schema Communication

Parent and child graphs with different schemas require explicit state mapping through a wrapper function:

```python
from typing import TypedDict

class DocumentState(TypedDict):
    text: str
    word_count: int

class WorkflowState(TypedDict):
    documents: list[str]
    results: list[dict]

def create_document_processor_wrapper():
    doc_processor = create_document_processor()

    def process_batch(state: WorkflowState) -> dict:
        results = []
        for doc_text in state["documents"]:
            # Transform: WorkflowState → DocumentState
            subgraph_input = {"text": doc_text, "word_count": 0}
            subgraph_output = doc_processor.invoke(subgraph_input)
            # Transform back: DocumentState → WorkflowState
            results.append({"word_count": subgraph_output["word_count"]})
        return {"results": results}

    return process_batch
```

### 4. Reusable Graph Components

Factory patterns create parametrized subgraphs for reusable component libraries:

```python
from typing import Callable
from langgraph.graph import StateGraph, START, END

def create_validator_subgraph(name: str, rules: list[Callable]):
    """Factory function creates validators with different rules."""
    def validate(state: ValidationState) -> dict:
        errors = []
        for rule in rules:
            valid, error_msg = rule(state["content"])
            if not valid:
                errors.append(error_msg)
        return {"is_valid": not errors, "errors": errors}

    subgraph = StateGraph(ValidationState)
    subgraph.add_node("validate", validate)
    subgraph.add_edge(START, "validate")
    subgraph.add_edge("validate", END)
    return subgraph.compile()

# Create multiple validators from same factory
length_validator = create_validator_subgraph("Length", [length_rule(10, 200)])
email_validator = create_validator_subgraph("Email", [email_format_rule()])
```

## Quick Start Example

```python
from langgraph.graph import StateGraph, START, END, MessagesState
from langchain_core.messages import SystemMessage, HumanMessage

# Create subgraph
def analyze_sentiment(state: MessagesState) -> dict:
    last_message = state["messages"][-1].content.lower()
    sentiment = "positive" if "happy" in last_message else "neutral"
    return {"messages": [SystemMessage(content=f"[Sentiment: {sentiment}]")]}

def create_sentiment_subgraph():
    subgraph = StateGraph(MessagesState)
    subgraph.add_node("analyze", analyze_sentiment)
    subgraph.add_edge(START, "analyze")
    subgraph.add_edge("analyze", END)
    return subgraph.compile()

# Use in parent graph
chatbot = StateGraph(MessagesState)
chatbot.add_node("sentiment", create_sentiment_subgraph())
chatbot.add_node("respond", lambda s: {"messages": [HumanMessage(content="Thanks!")]})
chatbot.add_edge(START, "sentiment")
chatbot.add_edge("sentiment", "respond")
chatbot.add_edge("respond", END)

# Execute
result = chatbot.compile().invoke({"messages": [HumanMessage(content="I'm happy!")]})
```

## Subgraph Composition Patterns

For comprehensive patterns with complete code examples, see:

| Pattern Category | Description | Reference |
|-----------------|-------------|-----------|
| **Basic Patterns** | Direct subgraph, simple transformation, two-level hierarchy | `references/core-patterns.md` |
| **Intermediate Patterns** | Field renaming, partial extraction, error propagation, multi-level nesting | `references/core-patterns.md` |
| **Advanced Patterns** | Factory functions, registry, parallel execution, conditional routing | `references/core-patterns.md` |

### Pattern Selection Guide

- **Same state schema** → Direct subgraph with shared state
- **Different schemas, simple mapping** → Simple transformation wrapper
- **Field name differences** → State mapping with field renaming
- **Large parent state, small child needs** → Partial state extraction
- **Robust error handling** → Error propagation pattern
- **Deep hierarchies** → Multi-level nesting
- **Reusable components** → Factory functions
- **Runtime composition** → Registry pattern
- **Independent parallel tasks** → Parallel subgraphs
- **Branching workflows** → Conditional routing

See `references/core-patterns.md` for detailed implementations of all patterns.

## Working Examples

Complete, runnable examples demonstrating all concepts:

### Example Files

1. **`examples/01_basic_subgraph_shared_state.py`** (~170 lines)
   - Direct composition with `MessagesState`
   - Sentiment analysis subgraph integrated into chatbot
   - ✅ Execution verified (exit code 0)

2. **`examples/02_subgraph_different_schema.py`** (~180 lines)
   - State transformation wrapper for different schemas
   - Document processing with `DocumentState` vs `WorkflowState`
   - ✅ Execution verified (exit code 0)

3. **`examples/03_multi_level_nesting.py`** (~190 lines)
   - Three-level hierarchy (parent → child → grandchild)
   - State propagation through multiple levels
   - ✅ Execution verified (exit code 0)

4. **`examples/04_graph_factory_pattern.py`** (~240 lines)
   - Reusable subgraph factories with parameters
   - Validator creation with configurable rules
   - ✅ Execution verified (exit code 0)

5. **`examples/05_complete_support_system.py`** (~250 lines)
   - **Production-ready customer support system**
   - Demonstrates all 4 core concepts in one system
   - Intent classification, knowledge retrieval, response generation
   - ✅ Execution verified (exit code 0)

6. **`examples/06_order_processing_validation.py`** (~380 lines)
   - **Production-like system with unit and integration tests**
   - E-commerce order processing with fraud detection
   - Demonstrates validation and testing strategies
   - ✅ Execution verified (exit code 0, all tests passed)

### Running Examples

```bash
# Set up test environment
cd langgraph-dev/skills/subgraphs-and-composition
uv init --no-readme --no-workspace test-env
cd test-env
uv add langgraph langchain-core

# Run any example
uv run python ../examples/01_basic_subgraph_shared_state.py
```

For detailed documentation of the complete customer support example, see `references/complete-examples.md`.

## Best Practices

For detailed best practices with code examples, see `references/best-practices.md`:

1. **Define Clear Boundaries** - Each subgraph has single, well-defined responsibility
2. **Minimize State Coupling** - Only share state keys that are truly needed
3. **Use Type Safety** - Leverage TypedDict for compile-time validation
4. **Handle Errors Gracefully** - Propagate errors with context to parent
5. **Test Subgraphs Independently** - Unit test each component before integration
6. **Document State Contracts** - Clearly specify input/output requirements
7. **Prefer Shared Schema** - Use shared state when possible to reduce boilerplate
8. **Use Factory Functions** - Create parametrized builders for reusable components

### Quick Best Practice Checklist

When creating a subgraph, verify:
- [ ] Single, well-defined responsibility
- [ ] Only shares needed state fields
- [ ] Uses TypedDict for state schema
- [ ] Wraps invocations in try-except with context
- [ ] Has unit tests separate from integration tests
- [ ] Input/output state and behavior documented
- [ ] Uses shared schema unless different schema needed
- [ ] Uses factory function if multiple similar subgraphs

## Troubleshooting

### Common Issues

**Subgraph not executing**:
- Verify parent graph routes to subgraph node
- Check graph connectivity and entry point

**State not propagating**:
- Verify wrapper returns subgraph output
- Check returned keys match parent schema

**Type errors at boundary**:
- Verify transformation maps all required fields
- Use explicit type conversion in wrapper

**Infinite loops**:
- Add loop counters to state at all levels
- Implement exit conditions in both parent and child

For detailed troubleshooting, see LangGraph documentation.

## References and Additional Resources

### Reference Files

For comprehensive guidance, consult these reference documents:

- **`references/core-patterns.md`** - Complete pattern catalog with 11 patterns (Basic, Intermediate, Advanced)
- **`references/complete-examples.md`** - Full customer support system demonstrating all 4 concepts
- **`references/best-practices.md`** - Detailed best practices with good/bad code examples
- **`references/state-mapping-patterns.md`** - State transformation techniques and edge cases
- **`references/component-library-design.md`** - Component architecture and registry patterns

### External Resources

- **LangGraph Official Documentation**:
  - [Subgraphs Guide](https://docs.langchain.com/oss/python/langgraph/use-subgraphs)

- **Related Skills**:
  - `graph-construction-in-langgraph`: Foundation patterns for building graphs
  - `state-management-in-langgraph`: State schemas, reducers, and immutability
  - `multi-agent-supervisor-in-langgraph`: Coordinating specialized agents
  - `parallel-execution-in-langgraph`: Fan-out/fan-in patterns
