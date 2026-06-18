# Changelog

All notable changes to the dev-practices plugin are documented here.

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
