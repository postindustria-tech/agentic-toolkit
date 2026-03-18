---
name: step-development
description: >
  BDD step development workflow for pytest-bdd projects. Use when you need to
  "develop BDD steps", "wire missing steps", "implement step definitions",
  "create BDD step implementations", "fix broken BDD steps". Parses Gherkin
  feature files, diffs against existing step definitions, and provides a
  structured implementation workflow for missing steps.
args: "<feature-file-or-pattern>"
version: 1.0.0
---

# BDD Step Development

Develop BDD step definitions for a feature by parsing Gherkin, diffing against
existing steps, and walking a structured implementation workflow. Each step goes
through research, review, implement, and verify phases.

## When to Use

- `/qa-bdd-step-development tests/bdd/features/my-feature.feature` -- wire ALL missing steps
- `/qa-bdd-step-development tests/bdd/features/auth-*.feature` -- fix broken steps (re-enumerates from Gherkin)

## Does NOT Cover

- Writing `.feature` files (write Gherkin first, then invoke this)
- Non-BDD tests (unit tests, integration tests)

## Protocol

### Step 1: Enumerate Missing Steps

Parse Gherkin and diff against existing step definitions:

```bash
# 1. Find all step text in the feature file(s)
grep -E '^\s+(Given|When|Then|And|But) ' tests/bdd/features/<feature>.feature \
  | sed 's/^\s*//' | sort -u > /tmp/gherkin_steps.txt

# 2. Find all registered step patterns
grep -rn '@given\|@when\|@then' tests/bdd/steps/ \
  | grep -oP "(?:parse|re)\(['\"])(.*?)(['\"])" | sort -u > /tmp/existing_patterns.txt

# 3. Diff -- unmatched lines are missing steps
# (Manual matching needed -- patterns use parsers.parse/re)
```

Alternatively, use `ast-grep` for structural queries:
```bash
# Find all existing Given steps
ast-grep --pattern '@given($_)' tests/bdd/steps/

# Find all existing When steps
ast-grep --pattern '@when($_)' tests/bdd/steps/

# Find all existing Then steps
ast-grep --pattern '@then($_)' tests/bdd/steps/

# Steps using parsers.parse()
ast-grep --pattern '@given(parsers.parse($_))' tests/bdd/steps/
```

Group missing steps into batches of 3-5 by scenario affinity (same scenario
or related scenarios that share Given context).

### Step 2: Research Each Batch

For each batch of missing steps:

1. **Identify test level** (see decision table below)
2. **Find related production code** that the steps will exercise
3. **Find existing step patterns** to follow (look at neighboring step files)
4. **Identify factories** available for test data setup

### Step 3: Implement Steps

For each missing step:

1. Write the step function following the patterns below
2. Use proper decorators (`@given`, `@when`, `@then`)
3. Follow the REQUIRED/FORBIDDEN rules for each step type
4. Run `pytest tests/bdd/ -k "<scenario_name>" -x` to verify

### Step 4: Verify

After implementing all steps in a batch:

```bash
# Run the specific feature
pytest tests/bdd/features/<feature>.feature -x -v

# Run quality checks
make quality
```

## Test Level Decision (HARD RULE)

This is the #1 gate in the research phase. Get this wrong and nothing else matters.

| Condition | Level | Why |
|-----------|-------|-----|
| Step exercises DB state or multi-step flows | **Integration** | Real DB catches bugs mocks miss |
| Step exercises UI or rendered pages | **E2E** | Needs full stack |
| Step tests pure computation, no I/O, no DB | Unit | Only exception |
| **Unsure** | **Integration** | Always default up, never down |

## Step Type Decision Table

### Given Steps

| REQUIRED | FORBIDDEN |
|----------|-----------|
| Factory objects (e.g., `MyFactory.build()`) | Raw dict literals `{...}` |
| Direct subscript access on known maps | `.get()` on known maps (silent None) |
| Sync registry after mutation | Forgetting to sync state |
| Direct context access `ctx["key"]` | `ctx.get("key")` (masks missing setup) |

### When Steps

| REQUIRED | FORBIDDEN |
|----------|-----------|
| Real Pydantic request objects | Raw kwargs to production code |
| Production code dispatch pattern | Duplicate dispatch per feature |
| `except Exception as exc: ctx["error"] = exc` | `ctx["error"] = SomeError(...)` (fabrication) |
| Production code path | Re-implementing business logic in test |

### Then Steps

| REQUIRED | FORBIDDEN |
|----------|-----------|
| `assert X == Y` with comparison operator | `assert x` (bare truthiness) |
| Descriptive message `f"Expected {a}, got {b}"` | No message |
| Typed attribute access `resp.field` | Dict access `resp["field"]` on typed objects |
| Real assertion body | `pass`, empty body, delegation to no-ops |

## Quality Gates (8 Mechanical Checks)

Every step must pass ALL 8 before verification:

| # | Check | What to look for |
|---|-------|-------------------|
| 1 | No `ctx.get("env")` | Use `ctx["env"]` -- guaranteed by fixture |
| 2 | No `hasattr(env, ...)` | Call methods directly or xfail |
| 3 | No bare `assert x` | Must compare values, not just truthiness |
| 4 | No `pass` / empty body | Must have real assertion or skip with reason |
| 5 | No dict literals in registry | Use factories to build real objects |
| 6 | No error fabrication in When | Call production code, catch real exceptions |
| 7 | Test level matches research | Integration unless justified |
| 8 | `make quality` passes | Exit code 0 |

## Common Mistakes

### 1. No-op delegation
```python
# WRONG -- assertion does nothing
def then_header_present(ctx): _pending(ctx, "then_header_present")

# FIX -- implement real assertion or skip with reason
def then_header_present(ctx): pytest.skip("not wired yet")
```

### 2. Silent env degradation
```python
# WRONG -- masks missing setup
env = ctx.get("env")
if hasattr(env, "set_response"): ...

# FIX -- direct access, guaranteed by fixture
env = ctx["env"]
env.set_response(...)
```

### 3. Error fabrication in When steps
```python
# WRONG -- tests the test, not production
ctx["error"] = ValidationError(message="bad input")

# FIX -- call production code
try:
    result = production_function(invalid_request)
except Exception as exc:
    ctx["error"] = exc
```

### 4. Dict literals in registry
```python
# WRONG -- raw dict instead of typed object
ctx["items"] = [{"name": "x", "type": "display"}]

# FIX -- factory builds real typed object
ctx["items"] = [ItemFactory.build(name="x", type="display")]
```

## ast-grep Rules

The plugin bundles ast-grep rules that catch common BDD anti-patterns:

- `bdd-no-ctx-get-env.yml` -- Catches `ctx.get("env")` in step files
- `bdd-no-error-fabrication.yml` -- Catches error fabrication in When steps
- `bdd-no-hasattr-env.yml` -- Catches `hasattr(env, ...)` in step files

Install these rules in your project's `.ast-grep/rules/` directory and run:
```bash
ast-grep scan
```

## Workflow Summary

```
1. Parse Gherkin feature file(s)
2. Diff against existing step definitions
3. Group missing steps into batches (3-5 per batch)
4. For each batch:
   a. Research: identify test level, find production code, find patterns
   b. Implement: write step functions following the rules above
   c. Verify: run pytest on the feature, run quality checks
5. Final verification: run full BDD suite
```
