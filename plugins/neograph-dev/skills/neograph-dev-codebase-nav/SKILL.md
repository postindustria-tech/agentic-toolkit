---
name: neograph-dev-codebase-nav
description: >
  This skill should be used when the user needs to "find where something
  lives", "import from the right module", "check the import path", "understand
  which layer owns this", "check deferred import budget", or needs to navigate
  the neograph source code without making wrong-module import mistakes.
version: 0.1.0
---

# Neograph Codebase Navigation

Provides the import map, layer discipline, and module ownership rules for the
neograph declarative LLM graph compiler. Prevents the most common agent mistake:
importing from the wrong internal module.

## The Golden Rule

Never guess import paths. Always grep first:

```bash
grep -rn "def function_name" src/neograph/
grep -rn "class ClassName" src/neograph/
```

## Public API Imports

All public symbols re-exported from `neograph/__init__.py`:

```python
# Core
from neograph import Node, Construct, compile, run, configure_llm
from neograph import Each, Oracle, Operator, Loop, ModifierSet
from neograph import Tool, ToolInteraction, tool
from neograph import FromInput, FromConfig, ExcludeFromOutput
from neograph import LintIssue, lint, describe_type, describe_value

# Decorators
from neograph import node, merge_fn, construct_from_functions, construct_from_module

# Registration (also available from neograph directly)
from neograph.factory import register_scripted, register_tool_factory, register_condition

# Renderers
from neograph import Renderer, XmlRenderer, DelimitedRenderer, JsonRenderer
from neograph.renderers import render_input

# Errors
from neograph import CompileError, ConstructError, ConfigurationError, ExecutionError
```

## Frequent Import Mistakes

| Wrong | Right | Why |
|-------|-------|-----|
| `from neograph._sidecar import register_scripted` | `from neograph.factory import register_scripted` | `_sidecar` has accessors, not registration |
| `from neograph.tool import register_tool_factory` | `from neograph.factory import register_tool_factory` | Factory at `factory.py:107` |
| `from neograph._llm import describe_value` (deferred) | Top-level in `_llm.py` now | Was promoted, stale deferred imports may exist |
| `from neograph._construct_validation import X` in decorators.py | Import in `_construct_builder.py` instead | Layer discipline: decorators -> builder -> validation |

## Layer Discipline

```
User code
   |
@node / ForwardConstruct / runtime Node|Modifier    <- DX layer (decorators.py)
   |
Construct(nodes=[...])                               <- IR layer (construct.py, validation)
   |
compile()                                            <- Compiler (compiler.py, state.py)
   |
factory._make_*_wrapper                              <- Runtime dispatch (factory.py, _dispatch.py)
   |
LangGraph StateGraph
```

Do not add @node-specific logic to IR-layer modules (`node.py`, `construct.py`,
`_construct_validation.py`, `factory.py`, `modifiers.py`). The decorator produces
instances those modules already accept.

## Deferred Import Budget

A structural guard test enforces a maximum of **41** deferred imports (imports
inside function bodies) across `src/neograph/*.py`. To check:

```bash
uv run pytest tests/test_structural_guards.py::TestDeferredImportBudget -v
```

Before adding a deferred import, verify a cycle actually exists by checking
whether the target module imports back. If no cycle, promote to top-level.

## Structural Guards

Run all guards after any import or comment changes:

```bash
uv run pytest tests/test_structural_guards.py -v
```

Guards enforce: deferred import budget, no ticket IDs in comments (`(neograph-xxxx)`),
no bare `except Exception: pass`, `_construct_builder` does not import from `decorators`.

## Additional Resources

### Reference Files

- **`references/module-map.md`** - Complete module ownership table with line counts and responsibilities
