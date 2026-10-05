# Pre-rename historical evaluation — pm-tr9, 2026-09-07

This records sow-milestone-coverage before pm-275. It is not validation of
requirements-coverage-audit; see [results-pm-275.md](results-pm-275.md) for new outcomes.

Executor: fresh-context host subagents, one per case, each working sequentially.
Only the copied skill, report-shapes reference, raw input documents, and case
request were supplied. The implementation coordinator graded the resulting
reports against evals.json and the source text. Expected findings and previous
assessment reports were not provided to executors.

Local artifacts: `/private/tmp/pm-tr9-evals.EZaKDh/`, with one directory per case.
These temporary paths are nonportable and may expire. Private source copies and
generated private reports remain outside git.

## Static validation

- PASS: `python3 /Users/eugenedymo/.codex/skills/.system/skill-creator/scripts/quick_validate.py plugins/pm-practices/skills/sow-milestone-coverage` returned `Skill is valid!`.
- PASS: evaluation JSON parses; all three case IDs are distinct and have prompts,
  expectations, and available input files.
- PASS: local Markdown reference links resolve; instruction files contain no
  unfinished placeholders; obsolete scaffold directory is absent.
- PASS: instruction inspection found no fixed project, appendix, version, or
  milestone assumptions. Entrypoint is 168 lines. Project terms occur in the
  explicitly separate private-document evaluation.

## Input SHA-256 hashes

| Input | SHA-256 |
|---|---|
| Synthetic fixture | `962d684405203a9d2abd26abc1db1ba85a0920a3b40ff01926a0463ac534c75e` |
| Private current SoW | `118d27f37aba472835595d3e26d2b0c86a39998607ef93c8a86e816b6f8e2e66` |
| Private historical SoW | `b46ed96b5b4b559df11a8436d1d14da289d607a847056de7cbacd40060a46b0c` |

## Synthetic full run — PASS

Artifacts: `synthetic-full/output/coverage-assessment.md`,
`milestone-opening-day-assessment.md`, `milestone-lending-desk-assessment.md`.

| Expectation | Result and evidence |
|---|---|
| absent | PASS — merged Findings G1 identifies Loan history as absent, citing S2 and both window boundaries. |
| implicit | PASS — I1 identifies Email change under Member profile maintenance with a clarification question. |
| excluded | PASS — E1 cites D1 and keeps Deposit refund out of gap counts. |
| unsupported | PASS — U2 and Lending desk reverse-check table identify Weather forecast widget without authoritative backing. The extra transaction-recording finding is source-supported and permitted. |
| accounting | PASS — Counts and full inventory ledger contains S1–S5 once each: 2 explicit + 1 implicit + 1 absent + 1 excluded = 5. Plan-bullet counts are separate. |
| artifacts | PASS — two milestone reports and merged report include evidence, confidence, boundaries, acceptance findings, and limitations. No tracker calls or implementation/ticket-existence claims. |

## Synthetic selected run — PASS

Artifacts: `synthetic-selected/output/coverage-assessment.md` and
`milestone-opening-day-assessment.md`.

| Expectation | Result and evidence |
|---|---|
| selection | PASS — only Opening day has an assessment, plus the merged selected report; full source and both windows are recorded as context. |
| local-findings | PASS — Items and local accounting classify S1/S5 explicit and S3 implicit with source and bullet citations. |
| limits | PASS — Selection limits explicitly states whole-SoW completeness was not assessed and global sweep/full historical reconciliation were not performed. Its five-item context table is explicitly not a global sweep. |
| boundaries | PASS — B1 keeps Loan history outside selected ownership, cites both boundaries without claiming exhaustive Lending desk coverage; X1 cites the refund exclusion. |

## Private full run — PASS

Both private fixtures were available; no cases were skipped. All seven
expectations passed. The per-expectation evidence names private document
content, so it is kept in the private results file next to the private case
definition outside git.

No failed cases or reruns were needed. Classification and grouping differ from
the historical assessment, as allowed by the grading criteria. This pass is not
an endorsement of every proposed milestone placement: interpretation remains
explicitly contestable and requires PM decisions.

## Limits of this validation

These cases exercise document-analysis behavior, not host-wide automatic skill
selection. Description routing was inspected. Optional parallel work within one
analysis, rerun preservation, and missing-fixture handling are documented but have
not been exercised in these cases. Evaluation does not establish factual accuracy
for arbitrary future SoWs.
