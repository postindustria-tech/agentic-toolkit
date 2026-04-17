---
name: neograph-dev-lint
description: >
  This skill should be used when the user asks to "extend lint", "add a lint
  check", "validate templates", "neograph check", "lint issue types",
  "template_resolver", "known_template_vars", or needs to understand how
  the lint system works, how to add new checks, or how the CLI wires through
  to lint().
version: 0.1.0
---

# Neograph Lint System

Provides the architecture of `lint()`, how to extend it with new checks, the
template placeholder validation system, and the CLI wiring checklist. The lint
is a read-only analysis pass that walks the construct graph and reports issues
without modifying anything.

## Architecture

`lint()` lives in `src/neograph/lint.py`. It walks all nodes in a Construct
(recursing into sub-constructs) and runs checks. Currently three check categories:

### 1. DI Binding Checks (original)

Validates that `FromInput`/`FromConfig` parameters have matching keys in the
provided config dict. Existing since v0.1.

### 2. Inline Prompt Placeholder Checks

Validates that `${var}` placeholders in inline prompts match predicted input
dict keys. Added in neograph-0h3x.

Inline prompts only see raw dict keys from `node.inputs` -- no flattened fields
from `render_for_prompt` return types, and no framework extras like `node_id`,
`project_root`, or `human_feedback`. The `_KNOWN_EXTRAS` set
(`{"node_id", "project_root", "human_feedback"}`) is explicitly subtracted from
valid keys for inline prompts (see `valid_keys = predicted_keys | (known_vars - _KNOWN_EXTRAS)`
at lint.py:231). This is because inline `${var}` substitution skips the full
rendering pipeline (`_render_with_flattening` never runs).

### 3. Template-Ref Placeholder Checks

When a `template_resolver` is provided, reads template text for template-ref
prompts, extracts `{placeholder}` names, and validates against input keys.
Added in neograph-vkiw.

Template-ref prompts see the full set of available keys: predicted input keys +
flattened field names from `render_for_prompt` return annotations + all known
vars (including framework extras like `node_id`/`project_root`/`human_feedback`).
This is because the `prompt_compiler` receives the `RenderedInput.for_template_ref`
dict which merges rendered inputs with flattened fields and framework extras.
The valid key set is `predicted_keys | known_vars` (lint.py:236) -- no
subtraction of `_KNOWN_EXTRAS`.

## The lint() API

```python
from neograph.lint import lint, LintIssue

issues = lint(
    construct,
    config={"node_id": "test"},              # DI config (optional)
    known_template_vars={"topic", "schema"},  # Consumer-supplied extras (optional)
    template_resolver=my_resolver,            # Template text resolver (optional)
)
```

## `_predict_input_keys` and the include_flattened Parameter

`_predict_input_keys(node, include_flattened=True)` (lint.py:286) computes what
dict keys a node will see at runtime. For dict-form `node.inputs`, the base keys
are the dict keys themselves.

The `include_flattened` parameter controls whether flattened field names from
`render_for_prompt` BaseModel return types are added to the key set:

- **`include_flattened=False`** -- used for inline prompts. Inline `${var}`
  substitution does not go through the rendering pipeline, so flattened fields
  and framework extras are not available. Only raw input dict keys are valid.
- **`include_flattened=True`** (default) -- used for template-ref prompts. Adds
  flattened field names by calling `_get_flattened_field_names()` (lint.py:309)
  for each input type. These names come from statically inspecting the
  `render_for_prompt()` return type annotation on each input type.

This parameter is the root of the inline/template-ref key asymmetry: inline
prompts see a strict subset of the keys that template-ref prompts see.

## `render_for_prompt` Return Annotation Introspection

`_get_flattened_field_names(input_type)` (lint.py:309) statically analyzes the
`render_for_prompt()` return type annotation to predict which flattened keys
will be available at runtime.

The algorithm:
1. Look up `render_for_prompt` on `input_type` via `getattr`.
2. Resolve the return annotation using `_resolve_return_type()`, which calls
   `typing.get_type_hints()` with a frame-walking fallback for locally-defined
   types (same technique as neograph's DI classifier).
3. If the return type is a `BaseModel` subclass, extract non-excluded field
   names from `model_fields`.
4. Return the field names as a `set[str]`. If any step fails (no method, no
   annotation, not a BaseModel), return an empty set.

This lets lint warn about template placeholders that reference flattened fields
without calling `render_for_prompt` at runtime -- purely static analysis.

### LintIssue

```python
@dataclass
class LintIssue:
    node_name: str    # "Node 'proc'"
    param: str        # The problematic parameter/placeholder name
    kind: str         # Issue category
    message: str      # Human-readable description
    required: bool    # True = ERROR (will crash), False = WARN
```

### Issue Kinds

| Kind | Severity | Meaning |
|------|----------|---------|
| `from_input` | varies | DI FromInput param not in config |
| `from_config` | varies | DI FromConfig param not in config |
| `from_input_model` | varies | Bundled model field not in config |
| `from_config_model` | varies | Bundled model field not in config |
| `template_placeholder_unresolvable` | ERROR | Placeholder not in input keys or known extras |
| `template_placeholder_known_vars_only` | WARN | Placeholder only resolvable via known_vars (bridge alias risk) |
| `loop_condition_unregistered` | ERROR | Loop when= string not in condition registry |
| `loop_condition_none_unsafe` | WARN/ERROR | Loop when= crashes on None (first iteration) |

### Loop Condition Checks (neograph-sfj8)

lint() now validates Loop modifier when-conditions. Three checks in `_check_loop_condition()`:

1. **String condition not registered** (kind: `loop_condition_unregistered`, ERROR):
   If `Loop.when` is a string, checks `registry.condition.get(name)`. Reports if missing.

2. **Callable condition not None-safe** (kind: `loop_condition_none_unsafe`, WARN):
   Smoke-tests `when(None)` -- catches `lambda d: d.score < 0.8` without `d is None or` guard.
   WARN because the callable might handle None via other means.

3. **Registered string condition None-unsafe** (kind: `loop_condition_none_unsafe`, ERROR):
   If a registered string condition (e.g., from `parse_condition`) crashes on None, report as ERROR.
   `parse_condition` results always crash on None because `getattr(None, field)` raises.

Implementation: `_check_loop_condition` in lint.py, wired into `_walk()` for both Nodes and Constructs.
Uses deferred import `from neograph._registry import registry` (bumped import budget to 42).

## How to Add a New Lint Check

### Step 1: Add the check function

In `lint.py`, create a function following the pattern:

```python
def _check_my_thing(
    node: Node,
    issues: list[LintIssue],
    *,
    # Accept whatever context your check needs
) -> None:
    """Check description."""
    # Skip nodes that don't apply
    if not relevant_condition:
        return
    # Detect the problem
    if problem_detected:
        issues.append(LintIssue(
            node_name=f"Node '{node.name}'",
            param=problematic_param,
            kind="my_check_kind",
            required=True,  # True = ERROR, False = WARN
            message="Description of the problem",
        ))
```

### Step 2: Wire into _walk

Add the call in `_walk()` after existing checks:

```python
_check_my_thing(item, issues, my_param=my_param)
```

### Step 3: Thread parameters through lint() -> _walk

If the check needs new parameters, add them to both `lint()` and `_walk()`
signatures. Follow the pattern of `known_vars` and `template_resolver`.

### Step 4: Wire into CLI

In `__main__.py:cmd_check`, load the new parameter and pass to `lint()`.
**Critical: grep for ALL existing `argparse.Namespace(` calls in test_cli.py
and add the new field to every one.** Missing fields cause `AttributeError`.

### Step 5: Update monkeypatched lint

In `test_cli.py`, the `test_lint_issues_displayed` test monkeypatches `lint`
with a lambda. The lambda must accept ALL keyword arguments:

```python
lambda construct, *, config=None, known_template_vars=None, template_resolver=None, your_new_param=None: [...]
```

## The CLI Wiring Checklist

When adding a new parameter to `lint()`:

- [ ] Add parameter to `lint()` signature in `lint.py`
- [ ] Thread through `_walk()` and down to the check function
- [ ] Add CLI flag in `__main__.py` `check_p.add_argument(...)`
- [ ] Parse and pass in `cmd_check()` to `lint()`
- [ ] Add `known_vars=None` (or equivalent) to ALL `argparse.Namespace()` calls in `test_cli.py`
- [ ] Update the monkeypatched lint lambda in `test_lint_issues_displayed`
- [ ] Write tests that exercise the new parameter through `lint()` directly
- [ ] Write at least one CLI test through `cmd_check()`

## The template_resolver Pattern

Consumer provides a callable that maps template names to text:

```python
def my_resolver(template_name: str) -> str | None:
    """Load template text from the prompt registry."""
    path = Path(f"prompts/{template_name}.txt")
    if path.exists():
        return path.read_text()
    return None

issues = lint(construct, template_resolver=my_resolver)
```

For `neograph check --setup`, the setup module exports `get_template_resolver()`:

```python
# my_check_config.py
def get_check_config():
    return {"node_id": "test", "project_root": "/path"}

def get_template_resolver():
    def resolve(name):
        path = Path(f"prompts/{name}.txt")
        return path.read_text() if path.exists() else None
    return resolve
```

## Gates

Before submitting lint changes:

- [ ] Existing DI lint behavior unchanged (run existing lint tests)
- [ ] New check has integration tests (not just unit tests)
- [ ] CLI wiring checklist complete (all Namespace calls updated)
- [ ] Monkeypatched lint lambda updated
- [ ] Loop condition checks fire on both Node and Construct modifiers
- [ ] Registered string conditions are smoke-tested for None-safety
- [ ] Existing loop tests (which use proper None-safe conditions) produce no lint issues
- [ ] `uv run pytest tests/test_validation.py tests/test_cli.py -v` passes

## Anti-Patterns

- **Adding a CLI flag without updating ALL Namespace calls in test_cli.py.**
  There are 10+ Namespace() calls. Missing one causes AttributeError in CI.
- **Monkeypatching lint with a lambda that doesn't accept new kwargs.**
  Same failure mode — the real lint signature changes, the mock doesn't.
- **Checking template text without a resolver.** Template-ref prompts are
  opaque. Without a resolver, lint cannot read the template. Fail open (skip),
  not closed (false error).
- **Assuming inline and template-ref prompts see the same keys.** Inline
  `${var}` skips the rendering pipeline, so flattened fields from
  `render_for_prompt` and framework extras (`node_id`, `project_root`,
  `human_feedback`) are not available. Template-ref `{var}` goes through
  full rendering and sees the complete key set. This asymmetry caused
  neograph-b3ox.
