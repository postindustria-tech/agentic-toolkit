# Validate ticket-quality audits

Use when maintaining the skill, not during normal audits. Cases and semantic
expectations are in [evals.json](evals.json). No test framework or live account is
required. Fixtures are invented REST v3-style issue/search JSON and source notes.

## Static checks

Run the installed skill-creator's `scripts/quick_validate.py` against this skill
directory; record the resolved validator path and outcome. Check JSON syntax,
local Markdown links, discovery description, trailing whitespace and absence of
unfinished scaffolding or customer-specific runtime assumptions. Version lives
under metadata to satisfy the validator. Shared plugin packaging is outside this
skill's ownership.

## Independent runs

1. For each case create a fresh temporary directory. Copy only SKILL.md, runtime
   references and that case's raw files; do not expose this procedure, expectations,
   previous evaluation outputs or draft assessments. The deliberately supplied
   previous.md is raw evidence for the rerun, not an expected current answer.
2. For mixed-backlog create a temporary Git repository with main containing
   helper.py: `def resolve(user):` followed by indented `return user`. Commit it
   locally using an invented author. Create and commit branch working changing
   only the signature to `def resolve(user, legacy):`. Leave working checked out.
   Neither branch has a return annotation. Use apply_patch for file creation/edits;
   never use the user's repository for this fixture. Record both commit IDs.
3. Give a fresh-context agent the case prompt, isolated skill and input locations,
   permitted repository and output directory. Allow only those reads and report
   writes, no live calls, nested agents or input/repository edits. The maintainer
   link need not resolve in this deliberately minimal runtime copy. If delegation
   is unavailable, use a separate fresh host session; do not label a self-review
   that has seen expectations an independent pass.
4. Read the whole generated report. Grade each expectation against input evidence,
   not exact wording. Reconcile keys/counts, all nine score columns, non-good notes,
   priorities and readiness. Confirm the code-claim run inspected main and left
   working unchanged. Record pass/fail with report sections, date, input hashes,
   artifact paths and execution mode. Temporary paths are local/nonportable.
5. Fix only demonstrated failures and rerun affected cases in fresh contexts. Keep
   failed outcomes in the result record. Record live retrieval, gate execution,
   default-output and other unexercised behavior as untested, not passed.

The private draft assessment is design provenance, not a replayable ticket export:
without full underlying issue/source/repository snapshots it is not an independent
behavioral fixture. Never commit private exports or generated real-project reports.
