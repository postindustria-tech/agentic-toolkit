---
name: obligation-test
description: >
  Write per-obligation behavioral tests with hard quality enforcement. Use when
  asked to "obligation test", "write obligation tests", "cover obligations",
  "obligation coverage", "behavioral test derivation", "per-obligation tests",
  "test from obligations", "fill obligation allowlist", "reduce obligation
  allowlist", "cover use case obligations". Each obligation gets its own
  research -> write-test -> verify -> commit chain. Replaces batch skills for
  new obligation coverage. Accepts obligation IDs directly or a prefix to
  auto-select uncovered obligations from the allowlist.
args: <obligation-ids-or-prefix> [--count N]
---

# Per-Obligation Test Derivation

Write one behavioral test per obligation with 6 hard quality rules enforced
mechanically. Each obligation gets deep research (scenario + production code +
test strategy) before any test code is written.

## Args

```
/dev-practices-obligation-test UC-004-MAIN-01 UC-004-MAIN-02 UC-004-MAIN-03
/dev-practices-obligation-test UC-004 --count 10
/dev-practices-obligation-test UC-001-MAIN --count 15
```

**Direct IDs**: Space-separated obligation IDs. Each must be a behavioral
obligation in your project's obligation documentation.

**Prefix mode**: A use-case prefix (e.g., `UC-004`, `UC-001-MAIN`).
Auto-selects uncovered obligations from the allowlist matching the prefix.
`--count N` limits how many (default: 10).

## Protocol

### Step 0: Resolve obligation IDs

If args look like a prefix (no trailing `-NN` sequence number):

```bash
python3 -c "
import json
al = json.loads(open('path/to/obligation_coverage_allowlist.json').read())
matches = sorted(oid for oid in al if oid.startswith('{prefix}'))
print(' '.join(matches[:N]))
print(f'Total matching: {len(matches)}, selected: {min(N, len(matches))}')
"
```

Store the resolved IDs for Step 1.

### Step 1: Cook the molecule

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/skills/dev-practices-execute/scripts/cook_formula.py \
  --formula ${CLAUDE_PLUGIN_ROOT}/skills/dev-practices-execute/formulas/obligation-test.yaml \
  --var "OBLIGATION_IDS={resolved_ids}" \
  --epic-title "Obligation tests: {prefix} batch N ({count} obligations)"
```

This creates: 1 setup atom + (4 atoms x N obligations) + 2 finalize atoms.

### Step 2: Baseline (setup atom)

Run project quality command, record pass count, allowlist size, and coverage count
in the epic notes. Close the baseline atom.

### Step 3: Research all obligations (parallel)

All research atoms unblock after baseline. For each obligation:

1. **Read the scenario** from obligation documentation. Extract: Given/When/Then, business rule, priority, layer.

2. **Translate Given/When/Then directly into the test**:
   - **Given** -> test setup (fixtures, env configuration)
   - **When** -> action (call production function)
   - **Then** -> assertions (expected output/state)

   The BDD spec is the **sole source** of expected behavior. Do NOT derive
   assertions from what the production code currently does.

3. **Check if production code implements it**: Locate the implementation function.
   - **Implemented** -> test should PASS
   - **Not implemented** -> test MUST still assert spec behavior, marked with
     `@pytest.mark.xfail(strict=True, reason="<what's missing>")`
   - Never write a test that asserts current (wrong) behavior instead of
     spec behavior. Never exclude an obligation as "not implemented."

4. **Store findings** in the atom notes via `bd update`.

5. **Close the research atom**.

### Step 4: Write tests (sequential per obligation)

Write-test atoms serialize via `depends_on_prev_barrier` to prevent
concurrent file modifications. For each obligation:

1. Read research notes from the previous atom.

2. Write ONE test following all 6 hard rules:

   | # | Rule | Check |
   |---|------|-------|
   | 1 | Import from project source | `from src.` or equivalent in test file |
   | 2 | Call production function | Test body calls impl function, repo method, or schema method |
   | 3 | Assert production output | Assertion checks a value from the production call |
   | 4 | Covers tag | Docstring contains exactly `Covers: {OID}` |
   | 5 | Use factories where applicable | Use test factories, not inline model construction |
   | 6 | Not mock-echo only | Does more than verify `mock.called` |

3. Self-check: Re-read the test and answer 4 yes/no questions.
   If any "no", rewrite before proceeding.

4. Run the test. PASS or XFAIL = proceed. ERROR = fix the test.

5. Close the write-test atom.

### Step 5: Verify (per obligation)

Six mechanical checks -- no judgment calls:

1. Production import exists
2. Covers tag is present and unique
3. Test runs without ERROR
4. Project quality command passes
5. No duplicate Covers tags
6. If test PASSES: remove OID from allowlist, run obligation guard

Close the verify atom.

### Step 6: Commit (per obligation)

```bash
git add <test_file> path/to/obligation_coverage_allowlist.json
git commit -m "test: add obligation test for {OID}"
```

Close the commit atom.

### Step 7: Finalize

After all obligation chains complete:

1. Run project quality command, compare to baseline
2. Run obligation guard
3. Record final state in epic notes
4. `bd sync`
5. Close finalize atoms and epic

## Batch Sizing

Recommended: **7-15 obligations per cook**.

- Fewer than 7: overhead of setup/finalize atoms not worth it
- More than 15: long molecule, risk of context compaction mid-chain

## xfail Policy

When production code doesn't implement the tested behavior:

```python
@pytest.mark.xfail(reason="<what's missing in production code>")
def test_name(self):
    """... Covers: {OID} ..."""
```

The xfail test STILL must follow all 6 rules. The `Covers:` tag still
removes the OID from the allowlist (the guard counts xfail as covered).

## Anti-Patterns

- Don't skip research -- shallow understanding produces mock-echo tests
- Don't batch-write 15+ tests at once -- quality degrades after 2-3
- Don't assert `mock.called` as the primary assertion (Rule 6)
- Don't drop obligations because "the code doesn't do this" -- use xfail
- Don't leave OIDs in the allowlist after a passing test covers them

## See Also

- `/dev-practices-remediate` -- Fill existing entity test stubs (batch approach)
- `/dev-practices-execute` -- Execute individual beads tasks
- `/dev-practices-test-audit` -- Audit test sources of truth
