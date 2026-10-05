# pm-ud8 evaluation results

Date: 2026-09-07. Both required cases passed, all 15 semantic expectations.
Two fresh-context subagents read isolated runtime skills and raw case inputs;
neither received grader expectations or draft assessments. The coordinator read
both complete output reports and graded against source evidence. No runtime
instruction changes were needed after testing.

Local, nonportable artifacts:

- `/private/tmp/pm-ud8-evals.pHXDsW/full/output/ticket-quality-assessment.md`
- `/private/tmp/pm-ud8-evals.pHXDsW/rerun/output/ticket-quality-assessment.md`

## Mixed backlog

| Expectation | Result and report evidence |
|---|---|
| 1. Scope/accounting | PASS — Snapshot and score table: 13 retrieved = 10 eligible + 2 excluded + 1 context-only; active QA, rejected and held work included. Eight fully labeled, two partially scored; 10 unique rows. |
| 2. Contradiction/source | PASS — Incorrect assertions: DEMO-1 delete/retain and Pending/Reserved are incorrect with approved-rule citations; ordered ahead of hidden scope and grooming gaps. |
| 3. Bundled scope | PASS — Hidden scope: DEMO-2 CSV/email/audit split, undecided recipients/access and design destination; Grooming gaps identifies weak AC. Destination search limits stated. |
| 4. Bugs | PASS — DEMO-3 confirmed-empty Repro missing; DEMO-10 Repro good with request/response, without demanding screenshot/browser detail. |
| 5. Applicability | PASS — Applicability paragraph: DEMO-4 light pass without mandatory Why/design link; DEMO-5 question/constraints/output; DEMO-9 coherent parent and inspected child. |
| 6. Parent resolution | PASS — DEMO-6 empty description and completed DEMO-90 conflict cited; recommendation reconciles remaining scope, not automatic closure. |
| 7. Base branch | PASS — DEMO-7 stale argument claim incorrect against main commit; missing return annotation remains valid work. Checkout stayed clean on working. |
| 8. Metadata | PASS — DEMO-8 High/Medium, parent DEMO-9/90 and absent blocker link all identified against supplied convention, with parent-scope reconciliation. |
| 9. Report/boundary | PASS — All nine columns and non-good/applicability notes; source limits, counts and qualified readiness agree. No numerical aggregate, writes or implementation certification. |

Temporary repository main: `147c471b716e32bc3fc36adfe0295c4842aaf316`;
working: `a4cf2fd8ef22fee85e22686dd4b29e61cad841ee`.
Post-run `git status --short` was empty and current branch remained working.

## Incomplete rerun

| Expectation | Result and report evidence |
|---|---|
| 1. Partial accounting | PASS — Snapshot: five retrieved, four eligible, one Done excluded; missing next page and unknown total explicit. Four unique score rows. |
| 2. Missing evidence | PASS — DEMO-7 dimensions unassessed, denied detail not empty; old code finding unverified with repository unavailable. |
| 3. Fixed vs closed | PASS — Changes table resolves DEMO-1's two findings against current rule/text; DEMO-3 left scope, not fixed (description still empty). |
| 4. Rerun membership | PASS — DEMO-4 On Hold to QA, DEMO-13 newly observed (not claimed newly created), and absent-page DEMO-20 unverified, not removed/resolved. |
| 5. Context limits | PASS — DEMO-4 local spacing assessment retained; unavailable DEMO-9 parent recorded separately, without inventing parent contents. |
| 6. Report/boundary | PASS — Nine columns, explicit em-dash convention, evidence-backed changes, qualified readiness and no live operations. |

The evaluator also identified an unplanted but supported DEMO-13 reproduction
gap: a blank search does not guarantee empty results without a starting data
condition. This was accepted against the supplied Search rule, not removed to
force a defect-free result. The supplied rerun date is one day after runtime;
the report correctly retained it as unverified provenance rather than silently
changing it.

## Static validation

- Validator: `/Users/eugenedymo/.codex/skills/.system/skill-creator/scripts/quick_validate.py`
  against `plugins/pm-practices/skills/jira-ticket-quality-audit`: Skill is valid.
- JSON parsing, unique eval IDs/input existence, local Markdown links and all-file
  trailing-whitespace checks passed. Runtime portability scan passed: no fixed
  customer, appendix, SoW version or wrapper names. Entrypoint: 172 lines.
- `git diff --check` passed; because the plugin is untracked, direct all-file
  whitespace checks above also covered these new resources.
- Installed ACLI 1.3.29-stable search/view help confirms the example flags,
  `--paginate`, `--json`, `*all` and explicit field selection. This is local help
  inspection, not live retrieval validation.
- Skill discovery was reviewed for quality-vs-coverage/refinement boundaries;
  host-wide automatic selection was not exercised. Shared packaging unchanged.

## Input/runtime hashes (SHA-256)

| File | Hash |
|---|---|
| SKILL.md | d907fbca0713ef9cee2280c356d75ca7f6338942abd072a3a6cd97574f4c446c |
| references/rubric.md | 80565009c5482bc8e29c2cc28f55ee386a143dca124607519f28c70b9acb1b94 |
| fixtures/tickets.json | 93fff21dbc16ed96b7f62786a0b7f04fd23c48fd21ac770a10899e1746284f23 |
| fixtures/snapshot.md | 4c3b33c44f6c81bd5e181dd566bfba933c0d6a744c0fca77d9af14424e8cc960 |
| fixtures/rules.md | 7af6036952a2b7506196afe4df26f9af212dd677ed73102724121623a3e85bb6 |
| fixtures/rerun-page.json | 9b1090e38db0a4e1384b688e90b10568df7df79c5589bdd5d28be9a1e5c018c7 |
| fixtures/rerun-snapshot.md | 61e6612a4ff22e7cc160efff9907842955f1f8a7339269097fdc730e81e78b3d |
| fixtures/previous.md | afd9b5c3ef1467e690f8d82db599dfb4a47cfdeb73338192d373d39227380a0d |

## Limits

Untested: live ACLI retrieval/pagination and exact ACLI aggregate export shape,
quality-gate execution, dependency-version inspection, default output path,
existing-output preservation, ambiguous-workflow clarification and automatic
host discovery. The tests exercised recorded REST-style exports, not a real Jira
site. No private ticket-export replay was claimed: the draft report alone lacks
the complete underlying evidence needed for one. No customer exports or reports
were committed; no Jira writes, installs, or shared packaging changes were made.
