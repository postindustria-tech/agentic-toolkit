# Test Schemas and Helpers

## Shared Models (tests/schemas.py)

All test Pydantic models live in `tests/schemas.py`. Import from there, do not
redefine in individual test files unless the model is test-specific.

```python
from tests.schemas import (
    RawText, Claims, MatchResult, ClaimResult,
    VerifyClaim, ExplorationResult, ClaimVerdict,
    SubInput, SubOutput,
)
```

### Helper functions in tests/schemas.py

```python
# Create a source node (no inputs)
a = _producer("name", OutputType)

# Create a consumer node (single-type inputs)
b = _consumer("name", InputType, OutputType)
```

## Throwaway Modules for construct_from_module Tests

Use `types.ModuleType` and attach @node functions as attributes:

```python
import types
mod = types.ModuleType("test_xyz_mod")

@node(outputs=Claims)
def my_fn(raw: RawText) -> Claims:
    return Claims(items=["a"])

mod.my_fn = my_fn
construct = construct_from_module(mod)
```

## Registry Cleanup

The `conftest.py` fixture `_cleanup_registries` runs after each test and clears
all registered scripted functions, tool factories, and conditions. No manual
cleanup needed.

## CLI Test Pattern (argparse.Namespace)

When testing `cmd_check`, construct a Namespace with ALL required fields:

```python
args = argparse.Namespace(
    target=str(pipeline_file),
    config=None,
    setup=None,
    known_vars=None,  # MUST include — added in neograph-0h3x
)
```

Missing fields cause `AttributeError` at runtime. When adding a new CLI
argument, grep for ALL existing `argparse.Namespace(` calls in test_cli.py
and add the new field.

## Monkeypatching lint()

When monkeypatching `lint` in CLI tests, the lambda must accept ALL keyword
arguments including newer ones:

```python
monkeypatch.setattr(lint_module, "lint",
    lambda construct, *, config=None, known_template_vars=None, template_resolver=None: [
        LintIssue(...)
    ]
)
```
