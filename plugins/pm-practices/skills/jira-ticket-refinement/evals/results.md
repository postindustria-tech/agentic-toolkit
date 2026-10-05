# Validation record — pm-fys

Date: 2026-09-07. Implemented from the draft's single/bulk triage, discovery,
description template, point scale, formatting guidance and pitfalls. The small
drafting subset is self-contained; the full ticket-quality rubric is not copied
or required at runtime. Shared project config keys match delivery metrics.

## Static and tool checks

- skill-creator quick_validate: passed; entrypoint 125 lines.
- evals.json syntax, all local Markdown links and per-file whitespace: passed.
- Project-specific leakage check for original project names/keys and unfinished
  markers: passed. Bundled people, hostnames, field/option IDs are invented.
- Installed ACLI 1.3.29-stable help inspected for edit, view, search and comment
  list; edit --generate-json inspected locally without performing any edit.
- ACLI edit schema exposes standard fields and ADF descriptions, not a documented
  arbitrary custom-field envelope. Runtime guidance does not invent one. Custom
  field work requires a supported, already authorized REST/connector path and
  actual editable metadata; otherwise the proposal is blocked, not partly applied.
- Official ACLI edit and Jira Cloud v3 issue/format documentation informed the
  transport reference. No live ticket retrieval or mutation was performed.

## Independent forward tests

Two fresh-context agents received their separate raw fixtures and runtime
instructions, not eval expectations or each other's output. Main agent read both
complete responses and assessed all 10 semantic expectations: passed.

Temporary outputs (not committed):
`/private/tmp/pm-fys-eval.i3XZuG/draft.md` and `apply.md`.

1. **Drafting:** preserves owner-only export, excludes emails, verifies direct
   endpoint denial in AC, rejects the conflicting comment and embedded approval
   bypass instruction, exposes the invite tracking gap and does not invent code
   evidence. A provisional 5-point proposal is explicitly reasoned and not treated
   as an established estimate from the stale audit. The simple copy ticket stays
   unchanged at 1 point with its icon/layout exclusion. No edits are claimed;
   combined application is blocked by unavailable custom-field capabilities.
2. **Approved batch decisions:** marks the timed-out write verified from matching
   read-back, does not retry it, pauses the concurrently changed ticket pending a
   refreshed proposal/approval, and leaves the remaining ticket pending a fresh
   read. No rollback, transitions, clearing or other unapproved actions.

These are behavioral instruction tests, not executions of a fake Jira writer.
No runtime instruction changes were necessary after observing the outputs.

## Untested and deliberately absent

Live authentication, edit permissions/option contexts, rich-node preservation,
server-side race behavior, actual write/read-back and candidate-discovery
pagination remain untested against Jira. Case 2 exercises recorded evidence,
not HTTP failure injection. Discovery's short/ADF-empty distinction and the
13-point breakdown path are specified but not independently forward-tested here.

No custom writer, authentication wrapper, extra config loader or dependency was
added. No status management, automatic links or subtask creation was carried over
from the broader draft. Shared manifest/marketplace/changelog work belongs to
pm-h8l. Generated artifacts remain private and outside version control.
