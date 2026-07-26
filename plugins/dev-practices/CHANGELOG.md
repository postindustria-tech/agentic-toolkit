# Changelog

All notable changes to the dev-practices plugin are documented here.

## 0.4.1

### Fixed

- **`semantic-merge`: base-assertion gate for reused worktrees (Phase 3).** A reused
  merge worktree's stale branch pointer, combined with an upstream that squash-merged
  the target branch's own lineage, produced a clean-looking merge that silently
  reverted the target's newest commits — the ff-sync aborted after printing
  `Updating x..y` (diagnostics truncated by a `tail` pipe) and every downstream check
  passed against the coherent-but-old tree. Phase 3 now requires an assertion that
  HEAD equals the intended base (and the worktree is clean) before merging, and bans
  truncating state-changing git output.
- **`semantic-merge`: pass-count comparison as Phase 7 layer 5.** A green behavior
  suite structurally cannot detect regression-to-xfail/skip; the coherence gate now
  ends with a per-suite PASSED-count comparison against each parent's pre-merge
  baseline, with every drop individually explained. This layer is what caught the
  205-scenario silent reversion above.

## 0.4.0

### Added

- **`semantic-merge` skill** — merge, consolidate, or integrate branches so the
  RESULT is correct, not merely conflict-free. Maps the branch DAG, sizes the TRUE
  conflict surface with a `merge-tree` simulation (not the inflated
  files-touched-by-both count), isolates the work in a throwaway worktree, splits
  conflicts into mechanical (rule-resolved: baselines, lockfiles, ledgers, data
  markers) vs semantic, resolves each semantic file with a fresh-context per-file
  subagent doing a union-of-intent merge, then verifies with a
  compile → lint → import-all → behavior-suite coherence gate before committing with
  an auditable resolution ledger. Hard rules: never content-merge generated or
  tool-owned data files (pin or regenerate); "unit-green" is not "merge-correct"; a
  clean auto-merge still needs review. Ships `scripts/merge-survey.sh` for the
  DAG + conflict-surface survey (Phases 1–2).

## 0.3.0

### Added

- **Fresh-context delegation in the `execute` skill.** The `task-execute`
  formula now dispatches its `research`, `review`, and `write-test` atoms to
  subagents running in a fresh context, eliminating the context pollution that
  degraded independent review and test design when every step shared one
  conversation. Delegation is declared per-atom via a `delegate:` block in the
  formula and is fully backward-compatible — atoms with no block run inline
  exactly as before. The orchestrator remains the single closer: a delegated
  subagent does the work, writes its outputs to the bead, and earns its gate
  label, but the orchestrator verifies and closes.
- **Three plugin-shipped agents** backing the delegated atoms, each carrying its
  role invariant in its system prompt (so the bead stays lean):
  - `dp-researcher` — establishes how a task should be built *in this codebase*:
    reuse over reinvention, current-pattern-over-deprecated (recency wins),
    docs-authoritative (flags code/doc contradictions rather than resolving
    them), surfaced at the right level of abstraction. Navigates via
    `.agent-index/` and `ast-grep` when available.
  - `dp-reviewer` — independent adversarial review (opus via frontmatter), with
    a reuse-bias criterion that flags near-duplicates of existing primitives.
  - `dp-test-author` — integration/E2E-first testing philosophy: test through
    the outermost surface, never mock the database/service under test, model
    failure modes and boundaries, TDD red.
- `codebase-scan` atom prefers `ast-grep` and `.agent-index` over text grep for
  the syntactic scan path when those tools are available, with grep/`git grep`/
  `ast` as the documented fallback.

### Changed

- `task-execute` bead descriptions for the three delegated atoms thinned to
  task-specifics; the role methodology now lives in the agent system prompts.
- `cook_formula.py` translates a `delegate:` block into `exec:delegate`,
  `exec:agent:<type>`, and `exec:model:<model>` labels that the walk loop reads
  to route the atom.
