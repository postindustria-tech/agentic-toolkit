---
name: create-tests
description: Generate comprehensive test suite for LangGraph workflow with mocked LLMs
argument-hint: graph_file [--coverage=basic|comprehensive]
allowed-tools:
  - Read
  - Write
  - Grep
  - AskUserQuestion
  - Bash
---

# Create Test Suite for LangGraph

Generate comprehensive pytest tests for LangGraph workflows including state tests, node unit tests, and integration tests with mocked LLMs.

## Instructions for Claude

### 1. Analyze Target Graph

Read the graph file to identify:
- State schema (TypedDict definition)
- Node functions
- Edge connections
- Conditional routing logic

Use `Grep` to find:
- State class definition
- Node function definitions
- `workflow.add_node()` calls
- `workflow.add_edge()` and `workflow.add_conditional_edges()` calls

### 2. Gather Test Requirements

Ask user:
- Coverage level (basic or comprehensive)
- Whether to mock LLM calls (default: yes)
- Whether to generate integration tests (default: yes)

### 3. Generate Test Structure

Create:
```
tests/
├── __init__.py
├── conftest.py          # Fixtures
├── test_state.py        # State schema tests
├── test_nodes.py        # Node unit tests
├── test_graph.py        # Integration tests
└── fixtures/
    └── mock_data.py     # Test data
```

### 4. Generate conftest.py

```python
import pytest
from unittest.mock import Mock

@pytest.fixture
def mock_llm():
    \"\"\"Mock LLM for testing.\"\"\"
    mock = Mock()
    mock.invoke.return_value = Mock(content="Mocked response")
    return mock

@pytest.fixture
def sample_state():
    \"\"\"Sample state for testing.\"\"\"
    return {
        "messages": [],
        "current_step": "start"
    }
```

### 5. Generate test_state.py

```python
from src.state import {StateName}

def test_state_structure():
    \"\"\"Test state accepts valid data.\"\"\"
    state = {StateName}(
        messages=[],
        current_step="start"
    )
    assert isinstance(state["messages"], list)

def test_state_validation():
    \"\"\"Test state validation logic.\"\"\"
    # Add validation tests
```

### 6. Generate test_nodes.py

For each node, create:
```python
def test_{node_name}(mock_llm, monkeypatch, sample_state):
    \"\"\"Test {node_name} node with mocked LLM.\"\"\"
    monkeypatch.setattr('src.nodes.llm', mock_llm)

    result = {node_name}(sample_state)

    assert "expected_field" in result
    mock_llm.invoke.assert_called_once()
```

### 7. Generate test_graph.py

```python
from unittest.mock import patch

def test_full_graph_execution(mock_llm):
    \"\"\"Test complete workflow with mocked LLM.\"\"\"
    with patch('src.nodes.llm', mock_llm):
        graph = create_graph()
        result = graph.invoke({"messages": [], "current_step": ""})

        assert result["current_step"] == "complete"

def test_conditional_routing():
    \"\"\"Test routing logic.\"\"\"
    # Test different routing paths
```

### 8. Add pytest.ini

```ini
[pytest]
testpaths = tests
python_files = test_*.py
python_functions = test_*
markers =
    unit: Unit tests with mocked dependencies
    integration: Integration tests
    slow: Tests that use real LLM (expensive)
```

### 9. Output Summary

Show:
- Test files created
- Test coverage estimate
- How to run tests
- Next steps for adding more tests

## Example Usage

```
/langgraph-dev:create-tests src/graph.py --coverage=comprehensive
```

Refer to **testing-agentic-systems** skill for patterns.
