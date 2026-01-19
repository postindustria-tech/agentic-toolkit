---
name: testing-agentic-systems
description: This skill should be used when the user asks about "test LangGraph", "test agents", "mock LLM", "evaluation metrics", "test workflows", "unit test nodes", or needs guidance on testing LangGraph applications.
version: 0.6.0
---

# Testing Agentic Systems

Testing LLM-based systems requires different approaches than traditional software: mock LLMs for determinism, use evaluation metrics instead of assertions.

## Test Pyramid for Agentic Systems

```
E2E Tests (Real LLM, expensive, slow)
  ↓
Integration Tests (Mocked LLM, medium cost)
  ↓
Node Unit Tests (Fully mocked, fast)
  ↓
State/Schema Tests (No LLM, instant)
```

## State Schema Tests (Instant)

```python
from typing import TypedDict
from pydantic import BaseModel

# Option 1: TypedDict (lightweight, dict-like access)
class AgentStateDict(TypedDict):
    """Define state schema for the agent graph."""
    messages: list[str]
    intent: str
    confidence: float

# Option 2: Pydantic (recommended - validation, defaults, IDE support)
class AgentState(BaseModel):
    """Define state schema for the agent graph with validation."""
    messages: list[str]
    intent: str = ""
    confidence: float = 0.0

def test_state_structure_typeddict():
    """Verify TypedDict state accepts valid data."""
    state: AgentStateDict = {
        "messages": ["Hello"],
        "intent": "greeting",
        "confidence": 0.95
    }
    assert state["messages"] == ["Hello"]
    assert 0 <= state["confidence"] <= 1

def test_state_structure_pydantic():
    """Verify Pydantic state accepts valid data and validates."""
    state = AgentState(messages=["Hello"], intent="greeting", confidence=0.95)
    assert state.messages == ["Hello"]
    assert 0 <= state.confidence <= 1

    # Note: Pydantic BaseModel uses attribute access (state.messages)
    # LangGraph nodes receive Pydantic instances but graph output may be dict
    # For dict conversion: state.model_dump()
```

## Node Unit Tests (Mocked LLM)

Node unit tests call the Python node function directly, bypassing graph compilation.
This isolates node logic for fast, focused testing with mocked dependencies.

```python
import pytest
from typing import TypedDict
from langchain_core.language_models import FakeListChatModel
from src.nodes import classify_node  # Import the node being tested

# Use TypedDict for type safety (same pattern as State Schema Tests)
class AgentStateDict(TypedDict):
    messages: list[str]
    intent: str
    confidence: float

@pytest.fixture
def mock_llm(monkeypatch):
    """Mock LLM using LangChain's FakeListChatModel.

    The fixture handles patching internally - test functions just use the fixture.
    """
    fake_llm = FakeListChatModel(responses=["greeting"])
    monkeypatch.setattr('src.nodes.llm', fake_llm)
    return fake_llm

def test_classify_node(mock_llm):
    """Test node function directly with mocked LLM (bypasses graph compilation)."""
    # Use TypedDict for type safety (defined above, matches State Schema Tests)
    state: AgentStateDict = {"messages": ["Test input"], "intent": "", "confidence": 0.0}
    result = classify_node(state)

    assert result["intent"] == "greeting"
```

## Graph Integration Tests

```python
from unittest.mock import patch
from langchain_core.language_models import FakeListChatModel
from src.graph import create_graph  # Import your graph factory

def test_full_graph_execution():
    """Test workflow with all LLMs mocked."""
    with patch('src.nodes.llm', FakeListChatModel(responses=["Response"])):
        graph = create_graph()
        compiled = graph.compile()  # Required: compile before invoke
        result = compiled.invoke({"messages": ["Test"]})

        assert result["current_step"] == "complete"
        assert len(result["messages"]) > 0
```

## Evaluation Tests (Real LLM, Metrics)

```python
import pytest
import numpy as np
# Use langchain_openai (not deprecated langchain_community.embeddings.openai)
from langchain_openai import OpenAIEmbeddings
from src.logic.modules import generate_response  # Import your response generator

def semantic_similarity(expected: str, actual: str) -> float:
    """Compute cosine similarity using embeddings."""
    embeddings = OpenAIEmbeddings()
    expected_vec = embeddings.embed_query(expected)
    actual_vec = embeddings.embed_query(actual)

    # Cosine similarity with zero-vector protection
    norm_expected = np.linalg.norm(expected_vec)
    norm_actual = np.linalg.norm(actual_vec)
    if norm_expected == 0 or norm_actual == 0:
        return 0.0  # Cannot compute similarity for zero vectors

    dot_product = np.dot(expected_vec, actual_vec)
    return float(dot_product / (norm_expected * norm_actual))

@pytest.mark.slow
@pytest.mark.expensive
def test_response_quality():
    """Evaluate with real LLM using metrics (uses real LLM calls)."""
    response = generate_response("What's 2+2?")

    # Don't use exact assertions for LLM output
    assert "4" in response  # Check essential content
    assert len(response) < 500  # Reasonable length

    # Or use semantic similarity
    similarity = semantic_similarity(response, "The answer is 4")
    assert similarity > 0.8

# Note: Register custom markers in pytest.ini to avoid PytestUnknownMarkWarning:
# [pytest]
# markers =
#     slow: marks tests as slow (deselect with '-m "not slow"')
#     expensive: marks tests that incur API costs
```

## Mocking Strategies

### Mock LLM Calls

```python
import pytest
from langchain_core.language_models import FakeListChatModel, GenericFakeChatModel
from langchain_core.messages import AIMessage
from itertools import cycle

@pytest.fixture
def mock_llm(monkeypatch):
    """Mock LLM directly using LangChain's built-in fake models."""
    fake_llm = FakeListChatModel(responses=["mocked response"])
    monkeypatch.setattr('src.nodes.llm', fake_llm)
    return fake_llm

@pytest.fixture
def mock_llm_with_streaming():
    """Use GenericFakeChatModel for testing streaming responses.

    Note: Use cycle() for infinite iteration (repeats indefinitely).
    Use iter() for finite iteration (exhausts after returning all items once).
    """
    messages = cycle([AIMessage(content="streamed response")])
    return GenericFakeChatModel(messages=messages)

@pytest.fixture
def mock_llm_with_messages():
    """Use FakeMessagesListChatModel for full message objects.

    Use this when you need messages with metadata, tool_calls,
    or additional_kwargs beyond just content.
    """
    from langchain_core.language_models import FakeMessagesListChatModel
    responses = [
        AIMessage(content="First response", additional_kwargs={"custom": "data"}),
        AIMessage(content="Second response"),
    ]
    return FakeMessagesListChatModel(responses=responses)
```

### Mock Tools

```python
import pytest
from langchain_core.tools import tool
from unittest.mock import patch

@pytest.fixture
def mock_search_tool():
    """Mock a LangGraph tool for testing."""
    @tool
    def search(query: str) -> str:
        """Search for information."""
        return "Mocked search results"
    return search

def test_agent_with_mocked_tool(mock_search_tool, monkeypatch):
    """Test agent using mocked tool."""
    monkeypatch.setattr('src.agents.tools.search', mock_search_tool)

    # Example: invoke agent that uses the search tool
    from src.agents import create_agent
    agent = create_agent()
    result = agent.invoke({"query": "test search"})

    assert "Mocked search results" in str(result.get("output", ""))
```

## Golden Dataset Testing

```python
# Import your project's classifier (example path - adjust to your project)
from src.logic.modules import IntentClassifier

GOLDEN_EXAMPLES = [
    ("What's the weather?", "weather_query"),
    ("Set a reminder", "reminder_create"),
]

def test_classification_regression():
    """Ensure no regression on known examples."""
    classifier = IntentClassifier()  # Replace with your classifier or load from checkpoint

    errors = []
    for text, expected_intent in GOLDEN_EXAMPLES:
        result = classifier(text=text)
        # Note: Adjust attribute access based on your classifier's return type
        # e.g., result.intent, result.category, result["intent"], etc.
        if result.intent != expected_intent:
            errors.append(f"{text} -> {result.intent} (expected {expected_intent})")

    error_msg = "\n".join(errors)
    assert not errors, f"Regressions:\n{error_msg}"
```

## Best Practices

1. **Fast tests with mocks** - Run frequently during development
2. **E2E tests sparingly** - Expensive, use for critical flows
3. **Use metrics not assertions** - For LLM outputs
4. **Version test data** - Track golden examples with code
5. **Track token usage** - Monitor costs in expensive tests

## Documentation References

- [LangGraph Testing Guide](https://docs.langchain.com/oss/python/langgraph/test) - Official testing documentation for nodes and graphs
- [How to evaluate a graph](https://docs.langchain.com/langsmith/evaluate-graph) - Official guide for evaluating LangGraph applications with LangSmith
- [Evaluate a complex agent](https://docs.langchain.com/langsmith/evaluate-complex-agent) - Advanced evaluation patterns for multi-step agents
- [LangGraph Overview](https://docs.langchain.com/oss/python/langgraph/overview) - Core LangGraph concepts and API reference
- [LangSmith Evaluation](https://docs.langchain.com/langsmith/evaluation) - Comprehensive guide to evaluating LLM applications
- **Project CLAUDE.md**: See "Testing Strategy for Agentic Systems" section
