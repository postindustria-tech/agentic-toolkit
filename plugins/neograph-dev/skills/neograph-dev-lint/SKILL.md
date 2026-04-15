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

### 3. Template-Ref Placeholder Checks

When a `template_resolver` is provided, reads template text for template-ref
prompts, extracts `{placeholder}` names, and validates against input keys.
Added in neograph-vkiw.

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
- [ ] `uv run pytest tests/test_validation.py tests/test_cli.py -v` passes

## Anti-Patterns

- **Adding a CLI flag without updating ALL Namespace calls in test_cli.py.**
  There are 10+ Namespace() calls. Missing one causes AttributeError in CI.
- **Monkeypatching lint with a lambda that doesn't accept new kwargs.**
  Same failure mode — the real lint signature changes, the mock doesn't.
- **Checking template text without a resolver.** Template-ref prompts are
  opaque. Without a resolver, lint cannot read the template. Fail open (skip),
  not closed (false error).
