---
name: neograph-dev-test-design
description: >
  This skill should be used when the user asks to "write tests", "add test
  coverage", "design test strategy", "where should this test go", "use
  Hypothesis", "write obligation tests", "use fakes", or needs to understand
  neograph test conventions, file layout, fake infrastructure, or the
  three-surface parity testing rule.
version: 0.1.0
---

# Neograph Test Design

Provides test conventions, file layout, fake infrastructure, and the obligation
test matrix pattern for the neograph codebase. The test suite has 1400+ tests
across 40 files. This skill prevents the most common testing mistakes.

## Test File Layout

### Where to put new tests

| Testing... | File | Package |
|-----------|------|---------|
| Assembly-time validation, fan-in, lint | `test_validation.py` | root |
| Rendering (BAML, XML, JSON, render_input) | `test_renderers.py` | root |
| Sub-constructs, state hygiene | `test_composition.py` | root |
| ForwardConstruct | `test_forward.py` | root |
| Conditions, condition registry | `test_conditions.py` | root |
| Loop modifier | `test_loop.py` | root |
| Inline prompts, ${var} resolution | `test_inline_prompts.py` | root |
| CLI (neograph check, test-scaffold) | `test_cli.py` | root |
| @node decorator basics | `decorator/test_basics.py` | decorator/ |
| @node construct assembly | `decorator/test_construct_assembly.py` | decorator/ |
| Scripted/think/agent/act modes | `modes/test_core_modes.py` | modes/ |
| LLM internals (retry, parsing) | `modes/test_llm_internals.py` | modes/ |
| Oracle modifier | `modifiers/test_oracle.py` | modifiers/ |
| Each modifier | `modifiers/test_each.py` | modifiers/ |
| Property-based topologies | `hypothesis/test_topologies.py` | hypothesis/ |
| Structural guards (AST scanning) | `test_structural_guards.py` | root |

New tests go in the matching file. If a feature spans multiple files, put the
test where the primary behavior lives.

## Fake Infrastructure

All fakes live in `tests/fakes.py`. Do not invent new fakes unless existing
ones genuinely do not cover the case.

```python
from tests.fakes import StructuredFake, StructuredFakeWithRaw, TextFake, ReActFake, configure_fake_llm

# Simple structured output
configure_fake_llm(lambda tier: StructuredFakeWithRaw(lambda m: m(field="value")))

# With capturing prompt compiler
captured = {}
def capturing_compiler(template, data, **kw):
    captured[template] = data
    return [{"role": "user", "content": "test"}]

configure_fake_llm(
    factory=lambda tier: StructuredFakeWithRaw(lambda m: m(result="ok")),
    prompt_compiler=capturing_compiler,
)

# ReAct tool loop
configure_fake_llm(lambda tier: ReActFake(
    tool_calls=[[{"name": "search", "args": {}, "id": "t1"}], []],
    final=lambda m: m(answer="done"),
))
```

## Naming Convention

BDD-style: `test_{what_should_happen}_when_{condition}`.
Class docstrings describe the feature being tested.

## Three-Surface Parity Rule

Any IR-level behavioral change must be tested through all three API surfaces:

1. **@node decorator**: `construct_from_functions("name", [fn1, fn2])`
2. **Declarative**: `Node.scripted("name", fn="reg_name", outputs=Type)`
3. **Programmatic**: `Node("name", ...) | Modifier(...)`

To register scripted functions for declarative tests:

```python
from neograph.factory import register_scripted
register_scripted("my_fn", lambda input_data, config: MyOutput(value="ok"))
```

## Hypothesis Property Tests

Located in `tests/hypothesis/`. Strategies in `topology.py` generate random
pipeline topologies. Use for invariant testing:

```python
from hypothesis import given, settings
import hypothesis.strategies as st
from tests.hypothesis.topology import any_topology_spec

@given(spec=any_topology_spec)
@settings(max_examples=50)
def test_invariant_holds_for_any_topology(self, spec):
    # Build, compile, run, assert invariant
```

Available topology strategies: `bare_topology`, `each_topology`,
`oracle_topology`, `fan_in_topology`, `sub_construct_topology`.

## The Obligation Test Matrix

For any new feature that crosses module boundaries, enumerate the dimensions
that need coverage and write tests for the cross-product. Example from
rendering dispatch:

| Dimension | Values to test |
|-----------|---------------|
| Renderer config | None, XmlRenderer, global |
| Input shape | single model, dict (fan-in), list, primitive |
| render_for_prompt | absent, returns str, returns BaseModel |
| API surface | @node, declarative, programmatic |
| Prompt type | inline ${var}, template-ref |

Full cross-product is impractical. Cover: each dimension has at least one test,
critical combinations have explicit tests, Hypothesis covers random combinations.

## Gates

Before submitting tests:

- [ ] Tests go in the correct file (see layout table above)
- [ ] Integration tests preferred over unit tests (mock-heavy tests are echo chambers)
- [ ] Fakes from `tests/fakes.py` used (no custom fakes unless justified)
- [ ] Three-surface parity for IR-level changes
- [ ] No `pytest.mark.xfail` in regression tests
- [ ] No `--ignore` or `-k "not ..."` to skip failures
- [ ] `uv run pytest -q` passes with zero failures

## Anti-Patterns

- **Testing what was built, not what should be built.** A test that asserts
  `result is raw_model` when the correct behavior is BAML rendering is
  locking in a bug, not preventing one.
- **Unit tests when integration is feasible.** Calling `_substitute_vars`
  directly misses the rendering that happens upstream in the dispatch chain.
- **Inventing new fakes.** `StructuredFakeWithRaw`, `ReActFake`, `TextFake`
  cover all production scenarios. Check `tests/fakes.py` first.
- **Skipping mutation verification.** If the test passes without the fix,
  it is not a regression test.

## Additional Resources

### Reference Files

- **`references/test-schemas.md`** - Shared Pydantic models in tests/schemas.py and helper patterns
- **`references/test-obligations.md`** - Full protocol for obligation test analysis with worked examples
