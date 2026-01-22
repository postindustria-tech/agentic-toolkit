# Architecture Patterns and System Design

This reference demonstrates how all 4 core subgraph composition concepts work together in a production-ready multi-agent system.

## Customer Support Multi-Agent System

This comprehensive architecture demonstrates all 4 core concepts in one cohesive workflow:

1. **Adding compiled graphs as nodes** - 3 subgraphs integrated into parent
2. **Subgraph communication** - Both shared schema (MessagesState) and different schema (RetrievalState)
3. **Parent-child state management** - State transformation wrapper for knowledge retrieval
4. **Reusable components** - Factory pattern for intent classifier

### System Architecture

```
Customer Support System (SupportState)
├── Intent Classifier (MessagesState - shared)
│   └── Classifies user intent: billing, technical, account
├── Knowledge Retriever (RetrievalState - different schema)
│   └── Fetches relevant articles based on intent
└── Response Generator (MessagesState - shared)
    └── Generates response using retrieved knowledge
```

### State Flow

```
User Message
    ↓
[Intent Classifier] → MessagesState with [Intent: billing]
    ↓
[Knowledge Retriever Wrapper]
    ├─ Extract: SupportState → RetrievalState
    ├─ Invoke: subgraph with {query, intent, results}
    └─ Transform: RetrievalState → SupportState
    ↓
[Response Generator] → MessagesState with AIMessage
    ↓
Final Response
```

## Key Implementation Patterns

### Pattern 1: Factory Function for Reusable Components

Create parametrized subgraph factories for component libraries:

```python
def create_intent_classifier(intents: dict[str, list[str]]):
    """Factory accepts configuration for flexible reuse."""
    def classify_intent(state: MessagesState) -> dict:
        last_message = state["messages"][-1].content.lower()

        # Match against configured intents
        detected_intent = "general"
        for intent_name, keywords in intents.items():
            if any(keyword in last_message for keyword in keywords):
                detected_intent = intent_name
                break

        return {"messages": [SystemMessage(content=f"[Intent: {detected_intent}]")]}

    subgraph = StateGraph(MessagesState)
    subgraph.add_node("classify", classify_intent)
    subgraph.add_edge(START, "classify")
    subgraph.add_edge("classify", END)
    return subgraph.compile()

# Usage: Create multiple classifiers from same factory
english_classifier = create_intent_classifier(intents={
    "billing": ["bill", "payment", "refund"],
    "technical": ["error", "bug", "broken"]
})

spanish_classifier = create_intent_classifier(intents={
    "billing": ["factura", "pago"],
    "technical": ["error", "problema"]
})
```

### Pattern 2: State Transformation Wrapper (Critical Pattern)

When parent and child have different schemas, create wrapper function that transforms state:

```python
# Different schemas require transformation
class SupportState(MessagesState):
    session_id: str
    intent: str

class RetrievalState(TypedDict):
    query: str
    intent: str
    results: list[str]

def create_retrieval_wrapper():
    """Wrapper bridges SupportState ↔ RetrievalState."""
    retriever = create_knowledge_retriever()  # Uses RetrievalState

    def retrieve_knowledge(state: SupportState) -> dict:
        """Three-step transformation process."""

        # STEP 1: Extract from parent state
        intent = extract_intent_from_messages(state["messages"])
        query = state["messages"][-1].content

        # STEP 2: Transform to child schema and invoke
        retrieval_input = {"query": query, "intent": intent, "results": []}
        retrieval_output = retriever.invoke(retrieval_input)

        # STEP 3: Transform back to parent schema
        knowledge_msg = SystemMessage(
            content=f"[Knowledge: {'; '.join(retrieval_output['results'])}]"
        )
        return {"messages": [knowledge_msg], "intent": intent}

    return retrieve_knowledge
```

**Key Technique**: The wrapper handles the complete transformation lifecycle: extract → transform → invoke → transform back → merge.

### Pattern 3: Composing Subgraphs with Mixed Schemas

Assemble parent graph using both shared schema and different schema subgraphs:

```python
def create_support_system():
    """Assemble multi-agent system with 3 subgraphs."""
    # Create subgraphs with different patterns
    intent_classifier = create_intent_classifier(intents={...})  # Shared schema
    response_generator = create_response_generator()  # Shared schema
    knowledge_wrapper = create_retrieval_wrapper()  # Wrapper for different schema

    # Assemble parent graph
    system = StateGraph(SupportState)
    system.add_node("classify", intent_classifier)  # Direct - shared schema
    system.add_node("retrieve", knowledge_wrapper)  # Wrapper - different schema
    system.add_node("respond", response_generator)  # Direct - shared schema

    # Define flow
    system.add_edge(START, "classify")
    system.add_edge("classify", "retrieve")
    system.add_edge("retrieve", "respond")
    system.add_edge("respond", END)

    return system.compile()
```

## Working Example

For the **complete, runnable implementation** of this architecture, see:
- **`examples/05_complete_support_system.py`** (~250 lines)
- **`examples/README.md`** for setup instructions and execution guide

### Running the Example

```bash
cd langgraph-dev/skills/subgraphs-and-composition/test-env
uv run python ../examples/05_complete_support_system.py
```

### Expected Output

```
→ Support System: Initialized session session-001
  Intent Classifier → Detected: billing
  Knowledge Retriever → Found 3 articles for billing
  Response Generator → Generated response

--- Conversation ---
HumanMessage: How do I get a refund?
AIMessage: Here's what I found:

1. Billing: We charge on the 1st of each month
2. Billing: You can update payment methods in Settings → Billing
3. Billing: Refunds are processed within 5-7 business days

Is there anything else I can help you with?
```

## Architectural Insights

### When to Use Each Pattern

| Scenario | Pattern | Example from System |
|----------|---------|---------------------|
| Same schema, simple integration | Direct subgraph | Intent classifier, Response generator |
| Different schemas | Wrapper with transformation | Knowledge retriever |
| Multiple similar components | Factory function | Intent classifier factory |
| Multiple coordination steps | Parent orchestrator | Main support system |

### Design Principles Demonstrated

1. **Single Responsibility**: Each subgraph has one clear purpose
2. **State Isolation**: Subgraphs only access fields they need
3. **Reusability**: Factory pattern enables component libraries
4. **Explicit Contracts**: Type annotations clarify state transformations
5. **Composability**: Mix shared/different schemas in same parent

### Extending the Architecture

**Add More Intents**:
```python
intent_classifier = create_intent_classifier(intents={
    "billing": ["bill", "payment", "charge", "refund"],
    "technical": ["error", "bug", "not working"],
    "account": ["password", "login", "sign in"],
    "sales": ["pricing", "upgrade", "plan"],  # New
    "feedback": ["suggestion", "complaint"]    # New
})
```

**Add Another Subgraph**:
```python
# Create sentiment analyzer (shared MessagesState)
sentiment_analyzer = create_sentiment_analyzer()

# Insert into flow
system.add_node("sentiment", sentiment_analyzer)
system.add_edge(START, "sentiment")
system.add_edge("sentiment", "classify")
```

**Track Conversation Metrics**:
```python
class SupportState(MessagesState):
    session_id: str
    intent: str
    conversation_count: int  # New field
    sentiment: str           # New field
```

## Production Considerations

1. **Error Handling**: Wrap subgraph invocations in try-except blocks
2. **Logging**: Add structured logging at each node for debugging
3. **Metrics**: Track latency, success rate, intent distribution
4. **Testing**: Test each subgraph independently (unit) before integration
5. **Scalability**: Cache compiled subgraphs for repeated invocations
6. **Configuration**: Externalize intents and knowledge base to config files

## Related Examples

- **examples/01_basic_subgraph_shared_state.py** - Simple shared schema pattern
- **examples/02_subgraph_different_schema.py** - State transformation basics
- **examples/04_graph_factory_pattern.py** - Factory pattern deep dive
- **examples/05_complete_support_system.py** - **This architecture implemented**
- **examples/06_order_processing_validation.py** - Production testing patterns

## Related References

- **`references/core-patterns.md`** - 11 composition patterns catalog
- **`references/best-practices.md`** - Code quality and design guidelines
- **`references/state-mapping-patterns.md`** - Advanced state transformation techniques
- **`references/component-library-design.md`** - Factory and registry patterns
