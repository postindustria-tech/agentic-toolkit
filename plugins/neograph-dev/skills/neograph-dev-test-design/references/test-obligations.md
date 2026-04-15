# Skill: Test Obligation Analysis

Systematically analyze functions to identify untested parameter combinations,
equivalence class gaps, and missing behavioral coverage that line coverage misses.

## When to use

- After reaching high line coverage (>90%) to find the semantic gaps
- Before releasing a version to audit critical paths
- After adding a new feature to verify combinatorial coverage
- When a bug is found that "should have been caught" by tests

## Args

```
/test-obligations <target>
```

Target can be:
- A module path: `src/neograph/runner.py`
- A function: `src/neograph/runner.py:run`
- A directory: `src/neograph/` (analyzes all public functions)
- `--audit` flag: compare against existing tests and report gaps

## Protocol

### Step 1: Identify the target functions

For each function in scope, extract:
- **Parameters**: name, type annotation, default value
- **Return type**
- **Side effects**: what global state, registries, or external systems does it read/write?
- **Control flow gates**: early returns, conditional branches that skip sections

### Step 2: Derive equivalence classes

For each parameter, identify meaningful equivalence classes based on type and usage:

| Type | Classes |
|------|---------|
| `X \| None` | `{None, valid_X}` |
| `dict[str, Any]` | `{empty, has_relevant_keys, missing_relevant_keys}` |
| `list[T]` | `{empty, single, multiple}` |
| `bool` | `{True, False}` |
| `BaseModel` | `{valid, with_optional_fields_missing}` |
| Union/enum | One class per variant |
| Callable/lambda | `{returns_truthy, returns_falsy, raises}` |

For parameters with **semantic coupling** (one parameter's value changes the
meaning of another), note the coupling:
```
run(): resume=non-None changes the meaning of config (must have _neo_input)
_walk(): param_res=empty changes whether merge_fn section is reachable
```

### Step 3: Derive cross-parameter obligations

Generate the **pairwise combinations** that matter. Not the full cartesian product
(exponential), but pairs where the combination creates distinct behavior:

```
Obligation: run(resume=dict, config=has_DI_fields) → FromInput resolves
Obligation: run(resume=dict, config=missing_DI_fields) → FromInput returns None
Obligation: _walk(param_res=empty, oracle.merge_fn=has_DI) → merge_fn DI checked
```

Rules for identifying meaningful pairs:
- Any parameter that gates a code section (early return, if-branch) creates an
  obligation with every parameter used inside that section
- Any parameter that affects state read by another function creates an obligation
  with every consumer of that state
- Any parameter that's a registry key (merge_fn name, condition name) creates an
  obligation with the registry state (registered vs unregistered)

### Step 4: Check side-effect obligations

For functions with side effects:
```
Side effect: run() mutates config["configurable"]["_neo_input"]
Obligation: verify config is mutated after first call
Obligation: verify mutated config is usable in subsequent resume call
```

### Step 5: Check boundary obligations

For parameters with ordered/sized types:
```
Boundary: list param → test with 0, 1, 2+ items
Boundary: int param → test with 0, 1, min, max, negative
Boundary: str param → test with empty, whitespace, special chars
```

### Step 6: Audit against existing tests

For each obligation, search the test suite for a test that covers it:
- Grep for the function name + parameter combination in test files
- Check if the combination appears in any parametrize decorator
- Check if the combination is exercised indirectly through integration tests

### Step 7: Output the obligation matrix

```markdown
## Function: `run(graph, input, resume, config)`

### Parameters
| Param | Type | Classes |
|-------|------|---------|
| input | dict \| None | {None, has_node_id, has_DI_fields} |
| resume | dict \| None | {None, has_feedback} |
| config | dict \| None | {None, fresh, has_configurable, has_neo_input} |

### Cross-parameter obligations
| ID | Combination | Expected behavior | Tested? |
|----|-------------|-------------------|---------|
| R-01 | input=dict, resume=None | normal execution | YES: test_basic_run |
| R-02 | resume=dict, config=has_neo_input | FromInput resolves | YES: test_from_input_resolves_after_resume |
| R-03 | resume=dict, config=fresh | FromInput returns None | NO → GAP |
| R-04 | input=None, resume=None | raises ValueError | YES: test_run_requires_input_or_resume |

### Side-effect obligations
| ID | Effect | Verified? |
|----|--------|-----------|
| R-SE1 | config mutated with _neo_input | YES: test_config_stashed |
| R-SE2 | _strip_internals removes neo_* | YES: test_strip_internals |

### Gaps (untested obligations)
- R-03: resume with fresh config (no _neo_input) — should this warn or error?
```

## Output format

Write the obligation matrix to stdout (or a file if `--output` specified).
Mark each obligation as:
- **COVERED**: test exists that exercises this combination
- **GAP**: no test found — potential blind spot
- **N/A**: combination is impossible (e.g., type system prevents it)
- **DEFERRED**: combination is valid but low-risk (document why)

## Anti-patterns

- Don't generate the full cartesian product — focus on pairwise combinations
  where the pair creates distinct behavior (control flow gates, state coupling)
- Don't count line coverage as "tested" — a line can execute without verifying
  the behavior at that line for the specific combination
- Don't generate obligations for pure internal helpers that are only called from
  one site — analyze the public caller instead
- Don't flag combinations that are prevented by the type system (e.g.,
  `resume: dict` + `input: dict` when the function returns early on resume)

## Example: what this would have caught

### neograph-pd8j (run resume + FromInput)
```
Obligation: run(resume=dict, config=fresh_without_input_fields)
  → post-interrupt node with FromInput param
  → FromInput resolves to None (BUG)
Status: GAP — no test exercises resume + FromInput combination
```

### neograph-s2h8 (lint early return + merge_fn DI)
```
Obligation: _walk(node.param_res=empty, node.oracle.merge_fn=has_bundled_DI)
  → early return at line 67 skips merge_fn check (BUG)
Status: GAP — tests only exercise nodes WITH param_res
```

Both would be flagged as gaps before the bugs reached production.
