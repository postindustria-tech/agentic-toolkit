---
name: dev-practices-code-review
description: >
  Launch multi-agent code review covering architecture, security, testing, and
  consistency. Use when asked to "code review", "review code", "audit code",
  "multi-agent review", "architecture review", "security review", "testing
  review", "DRY review", "consistency review", "layering review", "launch
  review agents", "review my changes", "review this PR", or needs comprehensive
  code quality analysis. Spawns specialized review agents for each dimension.
args: "[scope]"
---

# Multi-Agent Code Review

## MANDATORY: Use Agent Teams with Review Agents

You MUST use the agent team feature with the review agent types defined in
the plugin's `agents/` directory. Review agents are read-only for source code --
they scan, analyze, and write findings to their assigned output file.
They do NOT modify source code.

### What you must NOT do:
- Do NOT launch independent background subagents without `team_name`
- Do NOT use `run_in_background: true` with standalone Task calls
- Do NOT use `subagent_type: "general-purpose"` for review -- use the specific review agent types

## Protocol

### Step 1: Load team tools
```
ToolSearch: "select:TeamCreate"
ToolSearch: "select:TaskCreate"
ToolSearch: "select:SendMessage"
```

### Step 2: Create output directory and team

```bash
REVIEW_DIR=".claude/code-review/$(date +%d%m%y_%H%M)"
mkdir -p "$REVIEW_DIR"
```

```
TeamCreate: team_name="code-review-<DDMMYY>", description="Multi-agent code review"
```

### Step 3: Determine scope

The review scope is: `$ARGUMENTS`

If no scope was provided, default to `full` (all project source directories).

### Step 4: Create tasks and spawn reviewer teammates

For each review dimension, create a task and spawn a teammate.
All MUST be spawned in a single message (parallel launch).

```
Task:
  team_name: "<team-name>"
  name: "review-testing"
  subagent_type: "review-testing"
  prompt: |
    Review scope: <REVIEW_SCOPE>
    Output file: <REVIEW_DIR>/review-testing.md

    Read your agent definition for the full checklist and output format.
    Write your findings to the output file. Do NOT modify any other file.
```

The 5 review agents available in this plugin:

| name | subagent_type | Output file |
|------|---------------|-------------|
| review-testing | review-testing | `<dir>/review-testing.md` |
| review-dry | review-dry | `<dir>/review-dry.md` |
| review-consistency | review-consistency | `<dir>/review-consistency.md` |
| review-layering | review-layering | `<dir>/review-layering.md` |
| review-python-practices | review-python-practices | `<dir>/review-python-practices.md` |

You may add project-specific review agents (review-architecture, review-security,
review-execution-excellence) by creating agent definitions in your project's
`.claude/agents/` directory and adding them to the spawn list.

### Step 5: Monitor and coordinate

- Reviewers send messages when they complete or get stuck
- Messages are delivered automatically -- no polling needed
- Use SendMessage to communicate with reviewers by name
- When all report done, proceed to synthesis

### Step 6: Synthesize findings

After ALL agents complete, read all output files and produce a synthesis
report at `<REVIEW_DIR>/synthesis.md`.

**Synthesis is NOT a simple count.** Follow this protocol:

#### 6a: Validate Critical and High findings

For every Critical and High finding across all reports:
1. Run the reproduction command the agent provided
2. If it reproduces -> mark **verified**
3. If it doesn't reproduce -> mark **false positive** with reason
4. Check if another agent found the same issue -> **deduplicate**

#### 6b: Spot-check Medium findings

For Medium findings, spot-check ~30%. Verify the pattern holds for the rest.

#### 6c: Summarize Low findings

Low findings get a summary table without individual verification.

#### 6d: Cross-reference across agents

Identify systemic patterns -- issues flagged independently by multiple agents.
These are the most important findings because they indicate structural problems.

#### 6e: Write synthesis.md

Use this exact structure:

```markdown
# Code Review Synthesis -- <DATE>

**Scope**: <what was reviewed>
**Agents**: N ran, N produced findings
**Date**: YYYY-MM-DD

## Validation Summary

| Agent | Raw Findings | Verified | False Positives | Deduped |
|-------|-------------|----------|-----------------|---------|
| testing | N | N | N | N |
| dry | N | N | N | N |
| consistency | N | N | N | N |
| layering | N | N | N | N |
| python-practices | N | N | N | N |
| **Total** | **N** | **N** | **N** | **N** |

## Critical Findings (verified)

### CRIT-01: <title>
- **Source agent**: <which agent found this>
- **Original ID**: <agent's finding ID>
- **File**: `path:line`
- **Verification**: <what the synthesizer did to confirm>
- **Cross-references**: <other agents that flagged related issues>
- **Impact**: <concrete consequence>
- **Recommended action**: <specific fix>

## High Findings (verified)

## Medium Findings (verified)

## Low Findings (summary only)

| ID | Agent | File | Description |
|----|-------|------|-------------|

## Patterns Observed

<Cross-cutting themes from multiple agents>

## False Positives Discarded

| Original ID | Agent | Why discarded |
|-------------|-------|---------------|

## Metrics

- **Test coverage shape**: unit=N, integration=N, e2e=N
- **Security posture**: N critical, N high open items
```

### Step 7: Shut down team and report

1. Send shutdown requests to all reviewers
2. Delete the team after all teammates shut down
3. Present the synthesis summary to the user
4. Do NOT auto-file beads issues -- the user reviews first and decides what to act on
