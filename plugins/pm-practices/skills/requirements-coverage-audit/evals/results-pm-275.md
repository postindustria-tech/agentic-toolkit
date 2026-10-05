# Unified coverage evaluation — pm-275, 2026-09-07

The pre-rename results remain in [results.md](results.md) as history, not evidence
for this version. These runs use fresh-context host subagents, one per case,
with only the copied skill/runtime references and that case's raw inputs.
No grader expectations or earlier reports were supplied. The coordinator grades
the resulting reports against source evidence and evals.json.

Local, nonportable artifacts: `/private/tmp/pm-275-evals.MaKqvO/`, under each case's
`output/`. Real source copies and their reports remain outside version control.
Entrypoint line wrapping changed after execution copies were made; runtime wording
and references are otherwise identical.

## Static checks

- Baseline and renamed skill pass the installed validator:
  `/Users/eugenedymo/.codex/skills/.system/skill-creator/scripts/quick_validate.py`.
  The renamed invocation targets `plugins/pm-practices/skills/requirements-coverage-audit`.
- Six distinct eval cases; all JSON parses and all fixture paths resolve.
- Recorded search envelopes contain 12 unique issues over two pages (8 + 4),
  with a continuation token followed by a final page. Companion detail resolves
  the one description omitted from search in complete cases.
- Local ACLI `1.3.29-stable` search/view help confirms the documented command and
  field-selection flags. No live retrieval was exercised; this is not integration proof.
- Old discovery names occur only in the explicitly historical results record.
  The obsolete skill directory is removed. Shared packaging placeholders remain
  pm-h8l's responsibility and were not changed.
- Final local Markdown links resolve, including evaluation results. Whitespace
  checks pass. Runtime instructions contain no unfinished placeholders or fixed
  customer/project/heading assumptions; synthetic identifiers are invented. No
  real Jira export, customer identifier fixture or private report was added.

## Input SHA-256

| Input | Hash |
|---|---|
| harbor-sow.md | `962d684405203a9d2abd26abc1db1ba85a0920a3b40ff01926a0463ac534c75e` |
| jira/scope.md | `a9dedad082cfdcef1cd0af060b76f32d07ca5ddfc7bcda144e1fc05b5709d5cb` |
| jira/page-1.json | `ab9768e92245a314f28bd8987056c9662b66924c58a14c86b56e6297f5492c1e` |
| jira/page-2.json | `c6e48f89ccb2ca24cbc24b408f80673b818d78338be9e2d6a6bfbdc0758cae97` |
| jira/details-8.json | `8bce724a91cf2c6c9fe9da6172f28d0cf3dfc314da81a699ceec866b293b2ab1` |
| jira/snapshot.md | `9225e3b56537a26ff6e6a3bc784f2ab40a9da416708a72a4dddecf09fd2565d1` |
| jira/incomplete-snapshot.md | `a0d8dd1dac106c99d6a6eb0e0df4da289620e5b517ac77aaceb598607db3bd15` |
| Private current SoW | `118d27f37aba472835595d3e26d2b0c86a39998607ef93c8a86e816b6f8e2e66` |
| Private historical SoW | `b46ed96b5b4b559df11a8436d1d14da289d607a847056de7cbacd40060a46b0c` |

## Document regressions

| Case / expectation | Result and output evidence |
|---|---|
| synthetic-full: absent | PASS — merged F1 identifies S2 Loan history, distinguishing transaction recording and citing both windows. |
| synthetic-full: implicit | PASS — F2 identifies S3 under profile maintenance with clarification. |
| synthetic-full: excluded | PASS — E1 cites D1 for S4; not an active gap. |
| synthetic-full: unsupported | PASS — U2 identifies Weather forecast widget; U1 separately identifies transaction recording. |
| synthetic-full: accounting | PASS — ledger S1–S5 once: 2 explicit + 1 implicit + 1 absent + 1 excluded. Five plan bullets reconcile separately. |
| synthetic-full: artifacts | PASS — two milestone reports plus merged report, evidence/confidence/limits, no tracker or implementation claims. |
| synthetic-selected: selection | PASS — Opening day report and selected merged report only; complete source context. |
| synthetic-selected: local-findings | PASS — S1/S5 explicit, S3 implicit with citations. |
| synthetic-selected: limits | PASS — both reports disclaim whole-SoW completeness and global sweep/history reconciliation. |
| synthetic-selected: boundaries | PASS — S2 remains outside selection, S4 separately excluded by D1. |

## Jira recorded-export evaluations

| Case / expectation | Result and output evidence |
|---|---|
| jira-three-way: full-inventory | PASS — merged Canonical ledger has S1–S12 once with separate document/Jira columns; F1 records S2 absent in document but covered by DEMO-9. |
| jira-three-way: partial | PASS — F4 and S6 row retain SMS as uncovered current scope despite DEMO-3's ticket exclusion. |
| jira-three-way: many-to-many | PASS — B1 combines DEMO-4/11 into one S7; B2 names closed DEMO-5's S8/S9 bundle without implementation claims. |
| jira-three-way: exclusion | PASS — E1 cites D1 for S4; no false Jira gap. |
| jira-three-way: negative-evidence | PASS — F5 rejects DEMO-6's title using its weather-only description; F6 records S11 deferral without destination. Both are snapshot-qualified no-ticket findings after full-content review. |
| jira-three-way: content-access | PASS — S12 cites details-8.json, distinguishing omitted search content from absence. |
| jira-three-way: boundary | PASS — versions define milestones; shared epic is a container. S1/S3/S5 covered, S2 in Lending desk, weather unsupported. |
| jira-selected: selection | PASS — only Opening day report plus merged selected report, with explicit no-global-sweep and completeness limitations. |
| jira-selected: elsewhere | PASS — B1 distinguishes S7 submission here and cancellation in DEMO-11 elsewhere; B2 places S2 in DEMO-9, not globally missing. |
| jira-selected: local | PASS — selected table cites DEMO-1/10/2; four version-selected tasks, not all children of the epic. |

Three-way totals reconcile independently: document 2 explicit + 1 implicit +
8 absent + 1 excluded = 12; Jira 8 ticketed + 1 partial + 2 no ticket + 1 excluded
= 12. Reverse-check totals are separate. Selected Jira uses 14 linked parts of
12 parent requirements (S6 and S7 split), with four selected ticketed parts; it
does not sum parent/child counts or claim a global coverage sweep.

| Case / expectation | Result and output evidence |
|---|---|
| jira-incomplete: missing-page | PASS — Snapshot records isLast=false, continuation token, 8 of 12 expected issues and missing parent; no complete-source claim. |
| jira-incomplete: unknown-not-absent | PASS — F1 and ledger keep S2/S3/S7 cancellation unknown, not no ticket; no withheld issue content is cited. |
| jira-incomplete: preserve-positive | PASS — S1/S5 and S8/S9 retain evidence, B1 flags the bundle, S4 cites D1; F5 keeps S12 inaccessible. |
| jira-incomplete: accounting | PASS — 14 linked canonical parts from 12 parents: 6 ticketed + 7 unknown + 1 excluded. F4 keeps deferral destination unknown; no confirmed no-ticket findings. |

## Private document regression

All seven expectations passed. The per-expectation evidence names private
document content, so it is kept in the private results file outside git.

All six cases passed; no case was skipped or rerun. Granularity differs between
runs: linked splits are allowed, but totals must reconcile within a run. The private
run's 129 rows are not a replacement fixed target for future evaluations. Interpretive
listing/placement decisions remain reviewable; passing these cases is not a claim
that arbitrary future documents will be analyzed without errors.

## Validation limits

Recorded exports test matching, ADF/detail interpretation, selected boundaries and
missing-data handling, not live ACLI export shape or network pagination. Live
retrieval remains untested. Host-wide automatic discovery, optional per-milestone
parallelism, default output directories, rerun preservation and missing-private-
fixture skipping require separate behavioral checks; instructions are inspected.
