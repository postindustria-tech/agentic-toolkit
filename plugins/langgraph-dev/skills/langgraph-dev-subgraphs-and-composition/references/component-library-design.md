# Component Library Design for LangGraph

## Introduction

### Why Build Component Libraries

Component libraries enable code reuse, maintainability, and standardization across LangGraph applications. By extracting common patterns into reusable components, teams can:

- **Reduce duplication**: Write validation, retrieval, or processing logic once
- **Ensure consistency**: Standardize behavior across multiple workflows
- **Accelerate development**: Assemble new graphs from proven components
- **Simplify testing**: Test components in isolation, then compose with confidence
- **Enable specialization**: Domain experts can build components for others to use

### When to Extract a Component

Extract a component when:

✅ The same graph pattern appears 3+ times
✅ The logic has clear input/output contracts
✅ The component has configurable parameters
✅ The behavior needs isolated testing
✅ Multiple teams need the same functionality

Keep inline when:

❌ Used only once or twice
❌ Highly coupled to specific application logic
❌ Configuration overhead exceeds duplication cost
❌ The pattern is still evolving rapidly

## Factory Pattern Deep Dive

### Basic Factory

The simplest reusable component is a function that returns a configured graph:

```python
from langgraph.graph import StateGraph
from typing import TypedDict

class BaseState(TypedDict):
    content: str
    validated: bool

def create_validator_graph(min_length: int = 10) -> StateGraph:
    """Factory function for validation graphs."""

    def validate_node(state: BaseState) -> dict:
        is_valid = len(state["content"]) >= min_length
        return {"validated": is_valid}

    graph = StateGraph(BaseState)
    graph.add_node("validate", validate_node)
    graph.set_entry_point("validate")
    graph.set_finish_point("validate")

    return graph.compile()

# Usage
validator = create_validator_graph(min_length=20)
result = validator.invoke({"content": "Test content here", "validated": False})
```

### Configuration Objects

For complex parameters, use structured configuration:

```python
from dataclasses import dataclass
from typing import Optional, List

@dataclass
class ValidatorConfig:
    """Configuration for validator graph components."""
    min_length: int = 10
    max_length: Optional[int] = None
    required_keywords: List[str] = None
    case_sensitive: bool = False

def create_validator_graph(config: ValidatorConfig) -> StateGraph:
    """Create validator with structured configuration."""

    def validate_node(state: BaseState) -> dict:
        content = state["content"]

        # Length validation
        if len(content) < config.min_length:
            return {"validated": False}
        if config.max_length and len(content) > config.max_length:
            return {"validated": False}

        # Keyword validation
        if config.required_keywords:
            search_content = content if config.case_sensitive else content.lower()
            keywords = config.required_keywords if config.case_sensitive else [k.lower() for k in config.required_keywords]
            if not all(kw in search_content for kw in keywords):
                return {"validated": False}

        return {"validated": True}

    graph = StateGraph(BaseState)
    graph.add_node("validate", validate_node)
    graph.set_entry_point("validate")
    graph.set_finish_point("validate")

    return graph.compile()

# Usage
config = ValidatorConfig(
    min_length=20,
    max_length=500,
    required_keywords=["important", "urgent"],
    case_sensitive=False
)
validator = create_validator_graph(config)
```

### Closure Pattern

Capture configuration in closures for dependency injection:

```python
from typing import Callable, Any

def create_processor_graph(
    preprocessor: Callable[[str], str],
    validator: Callable[[str], bool],
    postprocessor: Callable[[str], str]
) -> StateGraph:
    """Create processor graph with injected functions."""

    def preprocess_node(state: BaseState) -> dict:
        processed = preprocessor(state["content"])
        return {"content": processed}

    def validate_node(state: BaseState) -> dict:
        is_valid = validator(state["content"])
        return {"validated": is_valid}

    def postprocess_node(state: BaseState) -> dict:
        if state["validated"]:
            final = postprocessor(state["content"])
            return {"content": final}
        return {}

    graph = StateGraph(BaseState)
    graph.add_node("preprocess", preprocess_node)
    graph.add_node("validate", validate_node)
    graph.add_node("postprocess", postprocess_node)

    graph.set_entry_point("preprocess")
    graph.add_edge("preprocess", "validate")
    graph.add_conditional_edges(
        "validate",
        lambda s: "postprocess" if s["validated"] else "__end__"
    )
    graph.add_edge("postprocess", "__end__")

    return graph.compile()

# Usage with custom functions
processor = create_processor_graph(
    preprocessor=lambda s: s.strip().lower(),
    validator=lambda s: len(s) > 10,
    postprocessor=lambda s: s.upper()
)
```

### Type-Safe Factories

Use TypedDict for configuration validation:

```python
from typing import TypedDict, Literal, Optional

class GraphConfig(TypedDict, total=False):
    """Type-safe configuration for graph factory."""
    mode: Literal["strict", "lenient", "custom"]
    min_length: int
    max_retries: int
    timeout: Optional[float]

def create_typed_graph(config: GraphConfig) -> StateGraph:
    """Factory with type-checked configuration."""
    mode = config.get("mode", "lenient")
    min_length = config.get("min_length", 10)
    max_retries = config.get("max_retries", 3)

    # Implementation uses type-checked config
    # ...

    return graph.compile()

# Type checker ensures valid configuration
config: GraphConfig = {
    "mode": "strict",  # Only "strict", "lenient", "custom" allowed
    "min_length": 20,
    "max_retries": 5
}
```

## Registry Pattern

### Graph Registry

Central catalog for discovering and instantiating components:

```python
from typing import Dict, Callable, Any

class GraphRegistry:
    """Registry for graph component factories."""

    def __init__(self):
        self._factories: Dict[str, Callable[..., StateGraph]] = {}
        self._metadata: Dict[str, Dict[str, Any]] = {}

    def register(
        self,
        name: str,
        factory: Callable[..., StateGraph],
        description: str = "",
        version: str = "1.0.0",
        **metadata
    ) -> None:
        """Register a graph factory."""
        self._factories[name] = factory
        self._metadata[name] = {
            "description": description,
            "version": version,
            **metadata
        }

    def create(self, name: str, **kwargs) -> StateGraph:
        """Instantiate a registered graph."""
        if name not in self._factories:
            raise ValueError(f"Unknown graph: {name}")
        return self._factories[name](**kwargs)

    def list_available(self) -> List[str]:
        """List all registered graph names."""
        return list(self._factories.keys())

    def get_metadata(self, name: str) -> Dict[str, Any]:
        """Get metadata for a registered graph."""
        return self._metadata.get(name, {})

# Global registry instance
registry = GraphRegistry()

# Register components
registry.register(
    "validator",
    create_validator_graph,
    description="Validates content length and keywords",
    version="1.0.0",
    input_schema={"content": "str", "validated": "bool"},
    output_schema={"validated": "bool"}
)

# Usage
validator = registry.create("validator", min_length=20)
available = registry.list_available()  # ["validator", ...]
```

### Dynamic Loading

Load graphs by name with parameter validation:

```python
from typing import Protocol, runtime_checkable

@runtime_checkable
class GraphFactory(Protocol):
    """Protocol for graph factory functions."""
    def __call__(self, **kwargs) -> StateGraph: ...

class DynamicRegistry(GraphRegistry):
    """Registry with dynamic loading and validation."""

    def register_with_validation(
        self,
        name: str,
        factory: GraphFactory,
        required_params: List[str] = None,
        optional_params: List[str] = None,
        **metadata
    ) -> None:
        """Register factory with parameter schema."""
        self._factories[name] = factory
        self._metadata[name] = {
            "required_params": required_params or [],
            "optional_params": optional_params or [],
            **metadata
        }

    def create(self, name: str, **kwargs) -> StateGraph:
        """Create graph with parameter validation."""
        if name not in self._factories:
            raise ValueError(f"Unknown graph: {name}")

        metadata = self._metadata[name]
        required = set(metadata.get("required_params", []))
        provided = set(kwargs.keys())

        missing = required - provided
        if missing:
            raise ValueError(f"Missing required parameters: {missing}")

        return self._factories[name](**kwargs)

# Register with schema
registry = DynamicRegistry()
registry.register_with_validation(
    "validator",
    create_validator_graph,
    required_params=["config"],
    optional_params=["debug"],
    version="1.0.0"
)
```

### Versioning

Manage multiple versions of components:

```python
class VersionedRegistry(GraphRegistry):
    """Registry supporting multiple component versions."""

    def __init__(self):
        super().__init__()
        self._versions: Dict[str, Dict[str, Callable]] = {}

    def register(
        self,
        name: str,
        factory: Callable[..., StateGraph],
        version: str = "1.0.0",
        **metadata
    ) -> None:
        """Register a versioned graph factory."""
        if name not in self._versions:
            self._versions[name] = {}

        self._versions[name][version] = factory

        full_name = f"{name}@{version}"
        self._factories[full_name] = factory
        self._metadata[full_name] = {"version": version, **metadata}

        # Update latest pointer
        self._factories[name] = factory
        self._metadata[name] = {"version": version, "latest": True, **metadata}

    def create(self, name: str, version: Optional[str] = None, **kwargs) -> StateGraph:
        """Create graph with optional version specification."""
        if version:
            full_name = f"{name}@{version}"
            if full_name not in self._factories:
                raise ValueError(f"Unknown graph version: {full_name}")
            return self._factories[full_name](**kwargs)
        else:
            # Use latest version
            if name not in self._factories:
                raise ValueError(f"Unknown graph: {name}")
            return self._factories[name](**kwargs)

    def list_versions(self, name: str) -> List[str]:
        """List all versions of a component."""
        return list(self._versions.get(name, {}).keys())

# Usage
registry = VersionedRegistry()
registry.register("validator", create_validator_v1, version="1.0.0")
registry.register("validator", create_validator_v2, version="2.0.0")

# Create specific version
validator_v1 = registry.create("validator", version="1.0.0", min_length=10)
validator_latest = registry.create("validator", min_length=10)  # Uses v2.0.0
```

## Dependency Injection for Subgraphs

### Tool Injection

Pass tools and services to subgraphs at runtime:

```python
from typing import Protocol

class SearchTool(Protocol):
    """Protocol for search tools."""
    def search(self, query: str) -> List[str]: ...

def create_retrieval_graph(search_tool: SearchTool) -> StateGraph:
    """Create retrieval graph with injected search tool."""

    class RetrievalState(TypedDict):
        query: str
        results: List[str]

    def retrieve_node(state: RetrievalState) -> dict:
        results = search_tool.search(state["query"])
        return {"results": results}

    graph = StateGraph(RetrievalState)
    graph.add_node("retrieve", retrieve_node)
    graph.set_entry_point("retrieve")
    graph.set_finish_point("retrieve")

    return graph.compile()

# Inject different implementations
from my_tools import ElasticSearchTool, VectorDBTool

elastic_retrieval = create_retrieval_graph(ElasticSearchTool())
vector_retrieval = create_retrieval_graph(VectorDBTool())
```

### Model Injection

Configure LLM models per subgraph:

```python
from anthropic import Anthropic

def create_llm_graph(
    model: str = "claude-sonnet-4-5-20250929",
    temperature: float = 0.7,
    max_tokens: int = 1024
) -> StateGraph:
    """Create graph with configurable LLM."""

    client = Anthropic()

    class LLMState(TypedDict):
        prompt: str
        response: str

    def llm_node(state: LLMState) -> dict:
        message = client.messages.create(
            model=model,
            max_tokens=max_tokens,
            temperature=temperature,
            messages=[{"role": "user", "content": state["prompt"]}]
        )
        return {"response": message.content[0].text}

    graph = StateGraph(LLMState)
    graph.add_node("generate", llm_node)
    graph.set_entry_point("generate")
    graph.set_finish_point("generate")

    return graph.compile()

# Different models for different tasks
fast_graph = create_llm_graph(model="claude-3-haiku-20240307", temperature=0.3)
creative_graph = create_llm_graph(model="claude-opus-4-5-20251101", temperature=0.9)
```

### Config Injection

Runtime configuration for flexible behavior:

```python
class RuntimeConfig:
    """Runtime configuration holder."""
    def __init__(self, **kwargs):
        self._config = kwargs

    def get(self, key: str, default: Any = None) -> Any:
        return self._config.get(key, default)

def create_configurable_graph(config: RuntimeConfig) -> StateGraph:
    """Graph that reads runtime configuration."""

    def adaptive_node(state: BaseState) -> dict:
        # Behavior changes based on runtime config
        threshold = config.get("threshold", 0.8)
        mode = config.get("mode", "normal")

        # Use configuration to adapt behavior
        # ...

        return {"validated": True}

    graph = StateGraph(BaseState)
    graph.add_node("process", adaptive_node)
    graph.set_entry_point("process")
    graph.set_finish_point("process")

    return graph.compile()

# Different configs for different environments
dev_config = RuntimeConfig(threshold=0.5, mode="debug")
prod_config = RuntimeConfig(threshold=0.9, mode="strict")

dev_graph = create_configurable_graph(dev_config)
prod_graph = create_configurable_graph(prod_config)
```

## Component Composition Patterns

### Chaining

Sequential composition of components:

```python
def chain_graphs(*graphs: StateGraph) -> StateGraph:
    """Chain multiple graphs sequentially."""

    class ChainState(TypedDict):
        input: Any
        intermediate: List[Any]
        output: Any

    def create_chain_node(graph: StateGraph, idx: int) -> Callable:
        def node(state: ChainState) -> dict:
            input_data = state["input"] if idx == 0 else state["intermediate"][-1]
            result = graph.invoke(input_data)
            intermediate = state.get("intermediate", []) + [result]
            return {"intermediate": intermediate, "output": result}
        return node

    chain = StateGraph(ChainState)

    for idx, graph in enumerate(graphs):
        node_name = f"step_{idx}"
        chain.add_node(node_name, create_chain_node(graph, idx))

        if idx == 0:
            chain.set_entry_point(node_name)
        else:
            chain.add_edge(f"step_{idx-1}", node_name)

    chain.set_finish_point(f"step_{len(graphs)-1}")

    return chain.compile()

# Usage
preprocessor = create_validator_graph(min_length=5)
validator = create_validator_graph(min_length=10)
postprocessor = create_validator_graph(min_length=15)

pipeline = chain_graphs(preprocessor, validator, postprocessor)
```

### Parallel Composition

Run components in parallel and aggregate results:

```python
from typing import List
from concurrent.futures import ThreadPoolExecutor

def parallel_graphs(graphs: List[StateGraph], aggregator: Callable) -> StateGraph:
    """Run graphs in parallel and aggregate results."""

    class ParallelState(TypedDict):
        input: Any
        results: List[Any]
        output: Any

    def parallel_node(state: ParallelState) -> dict:
        with ThreadPoolExecutor() as executor:
            futures = [executor.submit(g.invoke, state["input"]) for g in graphs]
            results = [f.result() for f in futures]

        output = aggregator(results)
        return {"results": results, "output": output}

    graph = StateGraph(ParallelState)
    graph.add_node("parallel", parallel_node)
    graph.set_entry_point("parallel")
    graph.set_finish_point("parallel")

    return graph.compile()

# Usage - multiple validators in parallel
validators = [
    create_validator_graph(min_length=10),
    create_validator_graph(min_length=20),
    create_validator_graph(min_length=30)
]

parallel = parallel_graphs(
    validators,
    aggregator=lambda results: all(r["validated"] for r in results)
)
```

### Conditional Composition

Select components based on runtime conditions:

```python
def conditional_graph(
    condition: Callable[[Any], str],
    branches: Dict[str, StateGraph],
    default: Optional[StateGraph] = None
) -> StateGraph:
    """Route to different graphs based on condition."""

    class ConditionalState(TypedDict):
        input: Any
        branch: str
        output: Any

    def route_node(state: ConditionalState) -> dict:
        branch = condition(state["input"])
        return {"branch": branch}

    def create_branch_node(graph: StateGraph) -> Callable:
        def node(state: ConditionalState) -> dict:
            result = graph.invoke(state["input"])
            return {"output": result}
        return node

    main = StateGraph(ConditionalState)
    main.add_node("route", route_node)

    for branch_name, branch_graph in branches.items():
        main.add_node(branch_name, create_branch_node(branch_graph))
        main.add_edge(branch_name, "__end__")

    if default:
        main.add_node("default", create_branch_node(default))
        main.add_edge("default", "__end__")

    main.set_entry_point("route")

    # Conditional edges from router
    def router(state: ConditionalState) -> str:
        branch = state["branch"]
        if branch in branches:
            return branch
        return "default" if default else "__end__"

    main.add_conditional_edges("route", router)

    return main.compile()

# Usage
strict_validator = create_validator_graph(min_length=50)
lenient_validator = create_validator_graph(min_length=10)

conditional = conditional_graph(
    condition=lambda inp: "strict" if inp.get("mode") == "production" else "lenient",
    branches={"strict": strict_validator, "lenient": lenient_validator}
)
```

## Testing and Validation

### Unit Testing Components

Test components in isolation:

```python
import pytest

def test_validator_factory():
    """Test validator component factory."""
    # Arrange
    config = ValidatorConfig(min_length=10, required_keywords=["test"])
    validator = create_validator_graph(config)

    # Act
    result = validator.invoke({
        "content": "This is a test message",
        "validated": False
    })

    # Assert
    assert result["validated"] is True

def test_validator_rejects_short_content():
    """Test validator rejects content below threshold."""
    validator = create_validator_graph(ValidatorConfig(min_length=100))

    result = validator.invoke({
        "content": "Short",
        "validated": False
    })

    assert result["validated"] is False

def test_validator_requires_keywords():
    """Test keyword validation."""
    validator = create_validator_graph(
        ValidatorConfig(required_keywords=["urgent", "important"])
    )

    result = validator.invoke({
        "content": "This is urgent but not critical",
        "validated": False
    })

    assert result["validated"] is False  # Missing "important"
```

### Integration Testing

Test composed graphs:

```python
def test_chained_validators():
    """Test multiple validators in sequence."""
    # Create chain
    chain = chain_graphs(
        create_validator_graph(ValidatorConfig(min_length=10)),
        create_validator_graph(ValidatorConfig(min_length=20)),
        create_validator_graph(ValidatorConfig(required_keywords=["test"]))
    )

    # Test valid input
    result = chain.invoke({
        "input": {"content": "This is a test message with sufficient length", "validated": False}
    })
    assert result["output"]["validated"] is True

def test_parallel_validators():
    """Test parallel validation."""
    parallel = parallel_graphs(
        [
            create_validator_graph(ValidatorConfig(min_length=10)),
            create_validator_graph(ValidatorConfig(max_length=100))
        ],
        aggregator=lambda results: all(r["validated"] for r in results)
    )

    result = parallel.invoke({
        "input": {"content": "Valid length message", "validated": False}
    })
    assert result["output"] is True
```

### Configuration Validation

Validate component parameters:

```python
def test_config_validation():
    """Test configuration validation."""
    with pytest.raises(ValueError):
        # Invalid configuration should raise
        config = ValidatorConfig(min_length=-1)  # Negative length invalid
        validator = create_validator_graph(config)

def test_registry_parameter_validation():
    """Test registry validates required parameters."""
    registry = DynamicRegistry()
    registry.register_with_validation(
        "validator",
        create_validator_graph,
        required_params=["config"]
    )

    with pytest.raises(ValueError, match="Missing required parameters"):
        registry.create("validator")  # Missing config

    # Valid call
    validator = registry.create("validator", config=ValidatorConfig())
    assert validator is not None
```

### Mock Dependencies

Test with mock services:

```python
from unittest.mock import Mock

def test_retrieval_with_mock_tool():
    """Test retrieval graph with mocked search tool."""
    # Create mock
    mock_search = Mock(spec=SearchTool)
    mock_search.search.return_value = ["result1", "result2"]

    # Create graph with mock
    retrieval = create_retrieval_graph(mock_search)

    # Test
    result = retrieval.invoke({"query": "test query", "results": []})

    # Verify
    assert result["results"] == ["result1", "result2"]
    mock_search.search.assert_called_once_with("test query")
```

## Documentation and Discoverability

### Component Contracts

Document input/output state clearly:

```python
def create_validator_graph(config: ValidatorConfig) -> StateGraph:
    """
    Create a content validator graph component.

    Input State:
        content (str): The content to validate
        validated (bool): Previous validation state (will be overwritten)

    Output State:
        validated (bool): True if content passes all validation rules

    Configuration:
        min_length (int): Minimum required content length (default: 10)
        max_length (Optional[int]): Maximum allowed content length (default: None)
        required_keywords (List[str]): Keywords that must appear (default: None)
        case_sensitive (bool): Whether keyword matching is case-sensitive (default: False)

    Example:
        >>> config = ValidatorConfig(min_length=20, required_keywords=["important"])
        >>> validator = create_validator_graph(config)
        >>> result = validator.invoke({"content": "This is important message", "validated": False})
        >>> print(result["validated"])
        True

    Returns:
        Compiled StateGraph ready for execution
    """
    # Implementation...
```

### Usage Examples

Provide executable examples:

```python
# examples/validator_usage.py

"""
Examples of using the validator component library.
"""

from component_library import create_validator_graph, ValidatorConfig

# Example 1: Basic length validation
def example_basic_validation():
    config = ValidatorConfig(min_length=10)
    validator = create_validator_graph(config)

    result = validator.invoke({
        "content": "Short",
        "validated": False
    })
    print(f"Valid: {result['validated']}")  # False

# Example 2: Keyword validation
def example_keyword_validation():
    config = ValidatorConfig(
        min_length=5,
        required_keywords=["urgent", "important"],
        case_sensitive=False
    )
    validator = create_validator_graph(config)

    result = validator.invoke({
        "content": "This is URGENT and IMPORTANT",
        "validated": False
    })
    print(f"Valid: {result['validated']}")  # True

# Example 3: Complex validation
def example_complex_validation():
    config = ValidatorConfig(
        min_length=20,
        max_length=200,
        required_keywords=["action", "required"],
        case_sensitive=True
    )
    validator = create_validator_graph(config)

    result = validator.invoke({
        "content": "Immediate action required for this task",
        "validated": False
    })
    print(f"Valid: {result['validated']}")  # True
```

## Versioning Strategies

### Semantic Versioning

Version components with semantic versioning:

```
MAJOR.MINOR.PATCH

MAJOR: Incompatible state schema changes
MINOR: New features, backward compatible
PATCH: Bug fixes, backward compatible
```

Example:
```python
# v1.0.0 - Initial release
def create_validator_v1(min_length: int) -> StateGraph:
    """Validator v1.0.0 - basic length validation."""
    # Simple implementation
    pass

# v1.1.0 - Added keyword validation (backward compatible)
def create_validator_v1_1(min_length: int, keywords: List[str] = None) -> StateGraph:
    """Validator v1.1.0 - added keyword support."""
    # Enhanced implementation
    pass

# v2.0.0 - Changed state schema (breaking change)
def create_validator_v2(config: ValidatorConfig) -> StateGraph:
    """Validator v2.0.0 - configuration object (BREAKING)."""
    # New implementation with different API
    pass
```

### Migration Guides

Document upgrade paths:

```markdown
# Migration Guide: Validator v1 → v2

## Breaking Changes

### Configuration API
**v1.x:**
```python
validator = create_validator_graph(min_length=10, keywords=["test"])
```

**v2.x:**
```python
config = ValidatorConfig(min_length=10, required_keywords=["test"])
validator = create_validator_graph(config)
```

### State Schema
**v1.x:**
- Input: `{"text": str, "valid": bool}`
- Output: `{"valid": bool}`

**v2.x:**
- Input: `{"content": str, "validated": bool}`
- Output: `{"validated": bool}`

## Migration Steps

1. Update imports:
   ```python
   from component_library import create_validator_graph, ValidatorConfig
   ```

2. Replace direct parameters with config object:
   ```python
   # Before
   validator = create_validator_graph(min_length=20, keywords=["test"])

   # After
   config = ValidatorConfig(min_length=20, required_keywords=["test"])
   validator = create_validator_graph(config)
   ```

3. Update state field names:
   ```python
   # Before
   result = validator.invoke({"text": content, "valid": False})
   is_valid = result["valid"]

   # After
   result = validator.invoke({"content": content, "validated": False})
   is_valid = result["validated"]
   ```
```

## Complete Example: Building a Validator Component Library

This example demonstrates a production-ready validator component library based on example 04:

```python
# validator_library.py

"""
Validator Component Library for LangGraph
Provides reusable validation components with factory pattern.
"""

from typing import TypedDict, List, Optional, Callable, Any
from dataclasses import dataclass
from langgraph.graph import StateGraph

# ============================================================================
# Configuration
# ============================================================================

@dataclass
class ValidatorConfig:
    """Configuration for validator components."""
    min_length: int = 10
    max_length: Optional[int] = None
    required_keywords: Optional[List[str]] = None
    case_sensitive: bool = False
    custom_validator: Optional[Callable[[str], bool]] = None

# ============================================================================
# State Schema
# ============================================================================

class ValidationState(TypedDict):
    """State schema for validation graphs."""
    content: str
    validated: bool
    errors: List[str]

# ============================================================================
# Component Factory
# ============================================================================

def create_validator_graph(config: ValidatorConfig) -> StateGraph:
    """
    Create a configurable content validator graph.

    Args:
        config: Validator configuration

    Returns:
        Compiled validation graph
    """

    def validate_node(state: ValidationState) -> dict:
        """Perform validation checks."""
        content = state["content"]
        errors = []

        # Length validation
        if len(content) < config.min_length:
            errors.append(f"Content too short (min: {config.min_length})")

        if config.max_length and len(content) > config.max_length:
            errors.append(f"Content too long (max: {config.max_length})")

        # Keyword validation
        if config.required_keywords:
            search_content = content if config.case_sensitive else content.lower()
            keywords = (
                config.required_keywords
                if config.case_sensitive
                else [k.lower() for k in config.required_keywords]
            )

            missing = [kw for kw in keywords if kw not in search_content]
            if missing:
                errors.append(f"Missing required keywords: {missing}")

        # Custom validation
        if config.custom_validator and not config.custom_validator(content):
            errors.append("Custom validation failed")

        is_valid = len(errors) == 0
        return {"validated": is_valid, "errors": errors}

    graph = StateGraph(ValidationState)
    graph.add_node("validate", validate_node)
    graph.set_entry_point("validate")
    graph.set_finish_point("validate")

    return graph.compile()

# ============================================================================
# Registry
# ============================================================================

class ValidatorRegistry:
    """Registry for validator components."""

    def __init__(self):
        self._configs: dict[str, ValidatorConfig] = {}

    def register(self, name: str, config: ValidatorConfig) -> None:
        """Register a named validator configuration."""
        self._configs[name] = config

    def create(self, name: str) -> StateGraph:
        """Create a validator by registered name."""
        if name not in self._configs:
            raise ValueError(f"Unknown validator: {name}")
        return create_validator_graph(self._configs[name])

    def list_available(self) -> List[str]:
        """List all registered validators."""
        return list(self._configs.keys())

# Global registry instance
registry = ValidatorRegistry()

# Pre-register common validators
registry.register("strict", ValidatorConfig(min_length=50, max_length=500))
registry.register("lenient", ValidatorConfig(min_length=5))
registry.register("email", ValidatorConfig(
    min_length=5,
    custom_validator=lambda s: "@" in s and "." in s
))

# ============================================================================
# Usage Examples
# ============================================================================

if __name__ == "__main__":
    # Example 1: Direct factory usage
    config = ValidatorConfig(
        min_length=20,
        required_keywords=["important", "action"],
        case_sensitive=False
    )
    validator = create_validator_graph(config)

    result = validator.invoke({
        "content": "This is an important action item",
        "validated": False,
        "errors": []
    })
    print(f"Valid: {result['validated']}, Errors: {result['errors']}")

    # Example 2: Registry usage
    strict_validator = registry.create("strict")
    result = strict_validator.invoke({
        "content": "Short",
        "validated": False,
        "errors": []
    })
    print(f"Valid: {result['validated']}, Errors: {result['errors']}")

    # Example 3: Custom validator
    def no_profanity(text: str) -> bool:
        banned_words = ["spam", "hack"]
        return not any(word in text.lower() for word in banned_words)

    config = ValidatorConfig(
        min_length=10,
        custom_validator=no_profanity
    )
    safe_validator = create_validator_graph(config)

    result = safe_validator.invoke({
        "content": "This is a spam message",
        "validated": False,
        "errors": []
    })
    print(f"Valid: {result['validated']}, Errors: {result['errors']}")
```

## Summary

Building reusable component libraries for LangGraph requires:

1. **Factory Pattern**: Parameterized graph creation with type-safe configuration
2. **Registry Pattern**: Central catalog for discovery and instantiation
3. **Dependency Injection**: Runtime configuration of tools, models, and services
4. **Composition**: Chain, parallel, and conditional graph assembly
5. **Testing**: Unit, integration, and mock-based validation
6. **Documentation**: Clear contracts, examples, and migration guides
7. **Versioning**: Semantic versioning with backward compatibility

These patterns enable teams to build maintainable, testable, and discoverable graph components that accelerate development while ensuring consistency across applications.
