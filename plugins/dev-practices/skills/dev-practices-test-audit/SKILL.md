---
name: dev-practices-test-audit
description: >
  Audit non-obligation tests to classify each assertion's source of truth. Use
  when asked to "audit tests", "test audit", "classify test assertions", "test
  source of truth", "how do we know tests are correct", "test authority audit",
  "characterization test check", "verify test correctness", "audit test quality
  source". Answers: "How do we know this test is testing correct behavior?" For
  each test, traces the assertion to an authoritative source (spec, architecture
  pattern, explicit product decision) or flags it as a characterization test.
args: <test-file-1> [test-file-2] ...
---

# Test Source-of-Truth Audit

Classify every test assertion by its authority level. Tests derived from
obligations have a clear source of truth. Tests written for coverage, regression,
or transport contract don't -- this skill fills that gap.

## Args

```
/dev-practices-test-audit tests/unit/test_format_resolver.py
/dev-practices-test-audit tests/unit/test_products_transport.py tests/unit/test_dynamic_products.py
```

One or more test file paths. Each file is audited independently.

## The Three Questions

For every test function, answer:

1. **What behavior does this test assert?**
   One sentence: "asserts that X returns Y when Z"

2. **What authoritative source says this is correct?**
   Check sources in priority order (see below). Record the source or "none found."

3. **Classification?**
   Based on the source (or lack thereof), classify the test.

## Sources of Truth (Priority Order)

| Priority | Source | Where to check | Example |
|----------|--------|----------------|---------|
| 1 | **Protocol/API spec** | JSON schemas, Python types in spec libraries | "Format resolution returns ValueError when format not found" |
| 2 | **Architecture patterns** | Project CLAUDE.md, architecture docs | "Transport wrapper returns protocol-specific result, impl returns model" |
| 3 | **Structural guards** | `test_architecture_*.py` -- guards define enforceable contracts | "ValidationError in wrapper -> specific error type" |
| 4 | **Explicit product decision** | Code comments, PR descriptions, task descriptions, docstrings with rationale | "list_available_formats returns [] on error (graceful degradation)" |
| 5 | **None found** | No external authority -- test documents current implementation behavior | "DB row not found -> returns None" |

## Classification Labels

| Label | Meaning | Action |
|-------|---------|--------|
| `SPEC_BACKED` | Spec or library defines this behavior | Keep as-is, add spec permalink |
| `ARCH_BACKED` | Architecture pattern or structural guard enforces this | Keep as-is, add pattern reference |
| `DECISION_BACKED` | Explicit product decision documented somewhere | Keep as-is, add decision reference |
| `CHARACTERIZATION` | No external source -- locks current behavior | Keep, but add comment: `# Characterization: locks current behavior, no spec backing` |
| `SUSPECT` | Current behavior may be wrong -- no source AND the logic seems questionable | Flag for product decision, file beads issue |

## Protocol

### Step 1: Read each test file

For each file in args:

1. Read the full test file
2. List every test function with its class
3. For each test, extract:
   - The assertion(s) -- what exactly does it check?
   - The setup -- what state is constructed?
   - The action -- what production function is called?

### Step 2: Read the production code under test

For each unique production module referenced by the tests:

1. Read the production function(s) being tested
2. Note: docstrings with rationale, code comments explaining "why"
3. Note: any spec references already present

### Step 3: Check authoritative sources

For each test assertion, check sources in priority order. **Stop at the first match.**

### Step 4: Produce the audit report

Add a classification comment block at the top of each test file:

```python
# --- Test Source-of-Truth Audit ---
# Audited: YYYY-MM-DD
#
# SPEC_BACKED (N tests):
#   test_x -- spec: format resolution order
#   test_y -- library: FormatId equality
#
# ARCH_BACKED (N tests):
#   test_z -- architecture pattern: transport returns protocol result
#
# CHARACTERIZATION (N tests):
#   test_w -- locks: returns None when DB row missing
#
# SUSPECT (N tests):
#   test_v -- list_available_formats returns [] on error (should it propagate?)
# ---
```

### Step 5: Handle SUSPECT tests

For each `SUSPECT` test:

1. File a beads issue:
   ```bash
   bd create --title="Product decision needed: <behavior>" \
     --description="Test <name> asserts <behavior> but no spec or product decision backs this." \
     --type=task --priority=3
   ```

2. Add a `# SUSPECT` comment to the test with the beads ID.

### Step 6: Handle CHARACTERIZATION tests

For each `CHARACTERIZATION` test, add a brief inline comment:

```python
# Characterization: locks current behavior (no spec backing)
def test_no_product_row_returns_none(self):
```

No beads issue needed -- characterization tests are valuable as regression guards,
they just don't prove correctness.

### Step 7: Commit

```bash
git add <audited-test-files>
git commit -m "docs: audit test sources of truth for <file(s)>"
```

## What This Skill Does NOT Do

- Does not rewrite tests (audit only -- add comments and classifications)
- Does not read the full spec end-to-end (checks targeted areas per test)
- Does not assume "current behavior = correct behavior"
- Does not remove any tests (even SUSPECT ones stay, just flagged)
- Does not audit obligation tests (use spec verification for those)

## Output Summary

At the end, print a summary table:

```
Test Source-of-Truth Audit Summary
==================================
File: tests/unit/test_format_resolver.py
  SPEC_BACKED:      3/17
  ARCH_BACKED:      5/17
  DECISION_BACKED:  1/17
  CHARACTERIZATION: 6/17
  SUSPECT:          2/17

Total: 17 tests audited
  SUSPECT issues filed: 2
```

## When to Use

- After writing coverage gap tests
- After writing transport wrapper tests
- After writing any tests not derived from obligations
- When reviewing test quality before merge
- When asked "how do we know these tests are correct?"

## See Also

- `/dev-practices-obligation-test` -- Writes tests FROM obligations
- `/dev-practices-code-review` -- Audits production code (not tests)
- `/dev-practices-execute` -- Execute individual beads tasks
