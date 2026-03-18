---
name: qa-bdd-inspect-steps
description: >
  Context-aware BDD step assertion completeness inspector. Use when you need to
  "inspect BDD steps", "audit step assertions", "check BDD assertion completeness",
  "find weak assertions", "find missing assertions". Links each Then step to its
  Gherkin scenario(s) before triage, so the AI evaluates assertions against SCENARIO
  INTENT not just step text. Also inspects Gherkin specifications for upstream
  vagueness (e.g., "result is valid" gives no implementation target).
args: "[--pass1-only] [--gherkin-quality] [--features-dir PATH] [--steps-dir PATH] [--output PATH]"
version: 1.0.0
---

# BDD Step Assertion Completeness Inspector (v2 -- Context-Aware)

Inspects BDD step functions for semantic completeness by placing each step
in the context of the scenario(s) that use it.

## Why Context Matters

v1 asked: "Does this function implement what the step text claims?"
A helper that checks "response exists" for "validation should result in valid"
would PASS (technically correct for the claim).

v2 asks: "Does this function verify what the SCENARIO intends?"
If the scenario tests whether a feature WORKS, checking "response exists" proves
input acceptance, not behavioral correctness -- FLAG.

## Usage

```
/qa-bdd-inspect-steps                          # Full pipeline (triage + deep trace)
/qa-bdd-inspect-steps --pass1-only             # Fast triage only
/qa-bdd-inspect-steps --gherkin-quality        # Also flag vague Gherkin specs
/qa-bdd-inspect-steps --steps-dir path/to/steps --features-dir path/to/features
```

## Prerequisites

- Python 3.10+
- `claude` CLI available on PATH (used for LLM triage passes)
- pytest-bdd project with `.feature` files and step definition files

## Pipeline

1. **Pass 0a**: AST scan -- extract step functions from step definitions directory
2. **Pass 0b**: Gherkin parse -- extract scenarios from features directory
3. **Pass 0c**: Link -- match each Then step to its scenario(s) via text matching
4. **Pass 1 (Sonnet)**: Context-aware triage -- each Then step shown WITH its
   scenario chain (Given/When/Then + tags + Examples + postconditions)
5. **Pass 2 (Opus)**: Deep trace -- architectural judgment on flagged steps
6. **Gherkin quality** (optional): Flag scenarios where the specification
   itself is too vague for a meaningful implementation

## Configuration

Default paths (override with CLI args):
- **Steps directory**: `tests/bdd/steps/`
- **Features directory**: `tests/bdd/features/`
- **Output**: `.claude/reports/bdd-step-audit-<timestamp>.md`

## Running the Script

```bash
python ${SKILL_DIR}/scripts/inspect_bdd_steps.py

# Custom paths
python ${SKILL_DIR}/scripts/inspect_bdd_steps.py \
  --steps-dir tests/bdd/steps \
  --features-dir tests/bdd/features \
  --output reports/bdd-audit.md

# Fast triage only (skip deep trace)
python ${SKILL_DIR}/scripts/inspect_bdd_steps.py --pass1-only

# Include Gherkin quality analysis
python ${SKILL_DIR}/scripts/inspect_bdd_steps.py --gherkin-quality
```

## Report

Written to the output path with:
- Step assertion issues by severity (MISSING > WEAK > COSMETIC)
- Gherkin specification quality issues (upstream problems)
- All flagged steps from Pass 1

## Severity Guide

| Severity | Meaning |
|----------|---------|
| MISSING | Assertion doesn't verify what the scenario intends (existence check for behavioral claim) |
| WEAK | Assertion checks something related but is significantly weaker than the scenario requires |
| COSMETIC | Naming/wording mismatch but the assertion is functionally correct for the scenario |

## When to Use

- After writing or modifying BDD step definitions
- After graduating @pending tests (verify assertions are not vacuous)
- Before closing BDD-related PRs
- With `--gherkin-quality` when upstream feature files change

## How It Works

### Two-Pass LLM Triage

**Pass 1 (Sonnet -- fast triage)**: Each Then step is presented alongside its
full scenario context (Given/When/Then chain, tags, Examples table). Sonnet
classifies each as FLAG or PASS based on whether the assertion strength matches
the scenario's intent.

**Pass 2 (Opus -- deep trace)**: Only flagged steps get deep analysis. Opus
examines the step's production context (imports, helper functions) and makes an
architectural judgment about what the correct assertion should be.

This two-pass design keeps costs low (Sonnet handles the bulk) while maintaining
high accuracy (Opus validates the flags).

### Step-to-Scenario Linking

The linker handles three pattern forms:
- Exact string match: `@then("the response is successful")`
- Parser patterns: `@then(parsers.parse("the {entity} has status {status}"))`
- Regex patterns: `@then(parsers.re(r"the response contains \d+ items"))`

Scenario Outline `<param>` placeholders are treated as wildcards during matching.
