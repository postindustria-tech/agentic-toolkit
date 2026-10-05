---
name: requirements-coverage-audit
description: >
  Audit whether milestones and their tasks account for agreed requirements, using
  document plans, Jira plans, or both. Use for "check SoW coverage", "did the
  milestones drop features", "compare SoW versions for milestone scope coverage",
  or "which SoW features have no ticket". Trace gaps, partial coverage, exclusions,
  and unsupported additions to sources. Read-only scope audit, not ticket-quality
  scoring, ticket refinement, or implementation verification.
metadata:
  version: "0.1.0"
---

# Requirements coverage audit

Compare the delivery plan against the supplied scope and produce traceable findings
for PM decisions. Read-only: do not write to Jira, create/refine tickets, generate
implementation tasks, score ticket quality, verify implementation, or rewrite scope.

## Inputs

Accept paths and source-role assignments in ordinary language or invocation arguments:

- `--scope PATH`: authoritative requirements, repeatable; required source role.
- `--plan PATH` (or `--sow PATH`): optional document milestone/task plan.
- `--jira-export PATH`: optional Jira search JSON/page files and companion details.
- `--jira-jql QUERY` or `--jira-filter ID`: optional authorized live Jira scope.
- `--jira-milestones MAPPING`: epic, release/version, or explicit issue-set mapping;
  accept ordinary-language assignments, not a fixed schema or epic assumption.
- `--old-sow PATH`: optional historical version, repeatable with its version/order.
- `--supporting PATH`: optional requirements, architecture, or recorded decisions.
- `--exclusions PATH`: optional exclusions or future-scope source.
- `--milestone NAME`: optional selection; default is all milestones.
- `--output DIR`: optional persistent private directory. Without it, write to a
  new timestamped directory under the system temporary directory and say that
  it is temporary. Honor a user-chosen directory only after checking it is not
  tracked or exposed to version control; do not modify ignore rules to make it
  so. Resolve the primary plan if several exist.

These are interpretation conventions, not an executable CLI or a project config.
Require authoritative scope and at least one delivery-plan source; one document can
fill several roles. Infer milestone names/count and relevant
sections from its contents; do not require a particular appendix, heading, domain,
or historical version. Preserve original milestone names in reports. Resolve an
ambiguous selection before analyzing it.

For Jira input, read [references/jira-matching.md](references/jira-matching.md)
before retrieval or assessment. Document-only runs do not contact Jira. Confirm
project/filter, milestone mapping, hierarchy, selection and available context;
do not silently change the configured account/site or assume an epic is a milestone.

Identify and record the source roles and precedence before assessing coverage:

| Role | Use |
|---|---|
| Milestone plan | Delivery promises under review |
| Authoritative scope | Current scope inventory against which coverage is judged |
| Historical versions | Prior intent; not automatically current obligations |
| Supporting evidence | Interpretation, placement, architecture constraints, acceptance criteria |
| Exclusions/future scope | Cited evidence of deliberate removal or deferral |

Ask the user when authority or precedence is materially ambiguous. Do not promote
history or supporting text to current authority without evidence. If the plan is
the only scope statement, report the lack of an independent comparison baseline;
do not present self-comparison as proof that no scope was lost. Report inaccessible
or incomplete source material before claiming completeness.

## Workflow

### 1. Establish the inventories

Read the full supplied source material relevant to the agreed analysis. Enumerate
scope items from the authoritative source, not from milestone reports or Jira.
Check the entire inventory against each supplied plan, never just document gaps.
A feature omitted from document milestones must still be examined in Jira.
Assign stable source IDs
(existing requirement IDs or heading paths with locally numbered items), and
record the source section and a line/page anchor. Enumerate historical line items
separately when supplied. Record versions/snapshot date and inventory granularity.

Use feature-level names derived from source wording, not invented specifications.
Split a source section when its independently deliverable features need different
milestones; retain the parent-to-child mapping. Shared references can point to the
same item, but distinct role permissions or lifecycle stages must not disappear
through deduplication. A heading containing several capabilities is not covered
merely because one of them is mapped.

### 2. Assess each milestone

Each analysis gets all milestone lists, source inventories, source texts,
exclusions, and precedence—not just its own slice. Compare features across the
whole current plan; old and new milestone numbers need not correspond.

Parallel work is optional. When available and permitted, use the host's subagent
mechanism for one assignment per milestone, respecting concurrency limits. Each
assignment reads the full shared context and the brief/report shapes in
[references/report-shapes.md](references/report-shapes.md). Otherwise work
sequentially with the same context. Record the execution mode; sequential runs
must not claim independent convergence. Parallel findings count as independent
only if the analyses did not see each other's conclusions before the merge.

For document plans, record citations, listing treatment, confidence,
placement rationale, and a specific clarification question where needed:

| Listing treatment | Evidence required |
|---|---|
| explicit | Identify the milestone bullet that names the feature |
| implicit | Identify the broader bullet and explain the interpretation and risk |
| absent | No covering bullet anywhere in the current plan after cross-checking exclusions |

`high` means scope and placement are supported without material ambiguity.
`needs-clarification` means scope, placement, or exclusion needs a decision; name
that decision. A proposed home for an absent feature does not make it covered.

For Jira plans use ticketed / partial / no ticket, with unknown/unassessed for
insufficient evidence, as defined in the Jira reference. Keep Jira and document
coverage separate; Jira placement need not mirror document placement.

Treat excluded items separately with the exclusion citation. Read carve-outs and
conditions: an exclusion heading alone is not evidence that everything beneath
it is excluded. Prerequisites can describe client inputs rather than excluded
delivery work. Contradictory exclusions remain decisions unless precedence settles them.

Put items belonging elsewhere into Boundary items with suggested milestone and
reason; do not count cross-references as additional ownership. Reverse-check every
milestone bullet or Jira task for authoritative or historical backing. Identify unsupported
bullets, distinguishing history-only or supporting-only evidence from current
authority; unsupported does not automatically mean out of scope.

If a milestone has no authoritative/historical mapping, check available supporting
requirements, internal consistency, uncovered requirements, overlap with other
milestones, architecture limits, exclusions, and the criteria against which it can
be accepted. Document missing acceptance definitions without inventing them or
assuming that every contract ties acceptance to an appendix.

### 3. Reconcile and sweep

For all-milestone runs, walk the original scope inventory item by item, including
items nobody claimed. Resolve duplicates and boundaries with evidence; leave
genuine ambiguities as named decisions. Keep a visible ledger with exactly one
row per canonical scope item, with a disposition for each supplied plan: one
canonical milestone owner, cited exclusion, or named gap (including unresolved
placement). Add unknown/unassessed when evidence cannot support a determination.
A requirement spanning milestones retains one accounting row with contributing
milestones and any ownership decision; do not force false single-milestone coverage.
Separate this accounting disposition
from explicit/implicit/absent listing treatment. Ownership may be a proposed home
for an absent item and is not proof of delivery-plan coverage.

For three-way runs use the same ledger with separate document-coverage and
Jira-coverage columns and evidence, not a third report type. Many tickets may
jointly cover one requirement; one ticket may cover many requirements. Neither
changes the number of canonical requirements. Do not sum coverage counts across plans.

Show the inventory-to-ledger mapping, missing/duplicate checks, and totals. Count
split child items once and retain their source parent links. Reconcile report
headline counts to item rows; report authoritative, historical, supporting-only,
and unsupported-bullet counts separately rather than summing overlapping sets.
Full accounting may still reveal gaps and unresolved decisions; it is not full
coverage. If the sweep is incomplete, say so and identify remaining source items.

For each historical item, record `retained`, `moved`, `excluded` (citation required),
`dropped` (no current coverage or documented exclusion found), or `unresolved`.
Use `moved` only when relocation is evidenced; otherwise use `retained` if still
represented or `unresolved` if uncertain. Historical scope absent from the current
plan is a potential loss, not an automatically binding current requirement.
For bundled historical items, classify linked parts separately so retaining one
part cannot hide a dropped part. Reconcile each supplied version independently.

For selected-milestone runs, keep full shared context and analyze the selection's
items and boundaries. Do not perform a claimed-items-only substitute for the full
sweep. State: "Whole-requirements completeness was not assessed" (for SoWs,
"Whole-SoW completeness was not assessed"). Mark global sweep and
full historical reconciliation as not performed; do not label other milestones'
unassessed scope as absent. Distinguish coverage inside the selected milestone from
coverage evidenced elsewhere; inaccessible other milestones remain unassessed.
Include relevant historical comparisons locally.

Before presenting a report, a draft, a proposal or a list of questions, run the
voice pass in `${CLAUDE_PLUGIN_ROOT}/references/voice.md` over the prose. It
changes wording only: never a key, a label, a count, a citation, a recommended
fix or a severity. The readers include people with intermediate English, so
every sentence must be understood in one read.

### 4. Write the reports

Read [references/report-shapes.md](references/report-shapes.md) when preparing
briefs or outputs. Write one milestone assessment per analyzed milestone and one
merged coverage assessment, even when the selection is a single milestone.
Use `milestone-<derived-name>-assessment.md` and `coverage-assessment.md`; disambiguate
colliding names using source order and record the mapping. Write to the output
directory resolved above (a private temporary directory unless the user supplied
an untracked one); on reruns preserve existing reports in a dated run directory
unless the user requested replacement.

Include source citations, absent and implicit findings, exclusions, unsupported
bullets, boundary resolutions, unresolved decisions, cross-cutting findings,
acceptance-definition gaps, and scope decisions. Jira findings may identify existing
ticket keys and missing coverage, but must not generate new ticket descriptions or
backend/frontend task lists. Do not copy source descriptions wholesale.

Known limitations must describe this run's source completeness/ambiguity,
comparison baseline, approximate or drifting citations where applicable,
judgment in placement and implicit/absent classification, execution mode, and
selection limits, plus Jira snapshot/query/access/content limits where applicable.
Never infer implementation from ticket coverage or status.

Keep real exports, private source fixtures and their reports outside version control.
Do not embed real customer identifiers, credentials, site/cloud/project/custom-field
values in committed skill resources. Runtime inputs may contain those identifiers;
synthetic fixtures use invented people/keys and clearly synthetic URLs.

## Maintainer validation

For changes to this skill, follow [evals/procedure.md](evals/procedure.md).
Evaluation inputs and grader expectations are not context for normal analysis.
