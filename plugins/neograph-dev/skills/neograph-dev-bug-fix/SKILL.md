---
name: neograph-dev-bug-fix
description: >
  This skill should be used when the user asks to "fix a bug", "debug this",
  "trace the root cause", "write a failing test first", "TDD bug fix", or
  when a runtime crash or incorrect behavior needs to be diagnosed and fixed
  in the neograph codebase. Provides the neograph-specific TDD workflow with
  quality gates that prevent the recurring mistakes from prior sessions.
version: 0.1.0
---

# Neograph Bug Fix Workflow

Encodes the TDD bug fix process with neograph-specific gates. Every bug fix
in this codebase follows the same sequence: reproduce with a failing test,
trace the root cause, fix minimally, verify via mutation, run full suite.

## The Invariant

**Tests must fail BEFORE the fix, pass AFTER, and fail again when the fix is
reverted.** This is the mutation verification protocol. A test that never
produced a FAILED output is not a regression test.

## The Workflow

### Step 1: Reproduce with a failing integration test

Write a test that demonstrates the bug through the **full dispatch chain**,
not just the unit function. Neograph bugs almost always manifest at the
boundary between layers (rendering + prompt compilation, lint + runtime keys,
compile + checkpoint).

```python
# WRONG: unit test that calls the function directly
result = _resolve_var("claim.text", {"claim": rendered_string})
assert result == ""  # this passes but doesn't catch the real bug

# RIGHT: integration test through the full pipeline
graph = compile(construct)
result = run(graph, input={"node_id": "test"})
# Assert on what the LLM actually received, not intermediate values
```

Verify the test FAILS before proceeding. Print the failure output. Record it.

### Step 2: Trace the root cause

Identify the exact line where behavior diverges from expectation. For neograph,
the common divergence points are:

| Symptom | Likely location |
|---------|----------------|
| Wrong data shape in prompt | `_dispatch.py:_render_input` or `renderers.py:render_input` |
| KeyError in template | `_llm.py:_resolve_var` or consumer's `prompt_compiler` |
| Missing field in state | `state.py:compile_state_model` or `factory.py:_extract_input` |
| Type mismatch at assembly | `_construct_validation.py:_check_fan_in_inputs` |
| DI param not found | `decorators.py:_classify_di_params` or `runner.py:_inject_input_to_config` |

### Step 3: Fix minimally

Change only what is necessary. Do not refactor surrounding code. Do not add
error handling for scenarios that are not part of the bug. Do not clean up
nearby code.

### Step 4: Mutation verify

Temporarily revert the production code (stash only the source files, keep
the test file). Confirm the test fails again. This proves the test is
coupled to the fix.

```bash
git stash push -m "mutation" src/neograph/the_file.py
uv run pytest tests/the_test.py::TheTest -x --tb=line
# Must show FAILED
git stash pop
```

### Step 5: Full suite + structural guards

```bash
uv run pytest -q --tb=short
```

Check for:
- Zero failures (no regressions)
- Deferred import budget still within 41
- No ticket IDs in comments
- No new warnings beyond baseline

## Gates

Before closing a bug fix:

- [ ] Failing test existed BEFORE the fix (not added after)
- [ ] Test goes through full dispatch chain (not just the unit function)
- [ ] Mutation verification passed (revert fix -> test fails)
- [ ] `uv run pytest -q` shows zero failures
- [ ] `uv run pytest tests/test_structural_guards.py -v` passes
- [ ] No `pytest.mark.xfail` used (xfail is NOT a failing test)
- [ ] No warning suppression added to pyproject.toml

## Common Mistakes

### Testing what was built, not what should have been built

The rendering asymmetry bug (neograph-qybn) went undetected in 1363 tests
because 5 existing tests *asserted the broken behavior*. The test said
`assert result is obj` (raw passthrough) when the correct behavior was
BAML rendering. When fixing a bug, verify the test asserts the **intended
contract**, not the current implementation.

### Unit tests that miss the integration boundary

Inline prompt tests called `_substitute_vars` directly with raw models.
The real dispatch chain runs `_render_input` first, which BAML-renders the
dict values. The unit test passed but the integration path crashed. Always
test through the layer boundary where the bug manifests.

### Suppressing warnings instead of fixing root causes

Adding `filterwarnings` to pyproject.toml hides problems. The only acceptable
filter is for intentional test behavior (e.g., tests that deliberately trigger
deprecation warnings). If a warning appears in production code paths, fix the
source.

## Three-Surface Parity Rule

Any IR-level behavioral change (`node.py`, `_construct_validation.py`,
`factory.py`, `state.py`) must be tested through all three API surfaces:

1. `@node` decorator path
2. Declarative `Node.scripted()` path
3. Programmatic `Node() | Modifier()` path

The most common neograph bug pattern: a feature works via `@node` but breaks
via the programmatic API because the decorator sets up state that the
programmatic path skips.

## Additional Resources

### Reference Files

- **`references/past-bugs.md`** - Catalog of bug patterns from prior sessions with root causes
