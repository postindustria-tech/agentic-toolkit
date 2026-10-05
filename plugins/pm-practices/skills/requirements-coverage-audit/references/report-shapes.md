# Brief and report shapes

Use these shapes for the relevant workflow stage. Omit inapplicable detail with a
reason, not an unexplained empty section. Use original source names and anchors.

## Milestone brief

- Target milestone name and source location; selected or full-run context.
- All milestone lists, all source texts/inventories, roles and precedence.
- Target outcome/theme, likely source sections, known relocations, and boundary
  questions supported by the supplied documents. Do not seed grader answers.
- Required outputs: report below plus a condensed summary for the merge.
- Instructions: follow SKILL.md classification, exclusion, and citation rules;
  return proposed ownership and released boundary items, not final global counts.

## Per-milestone assessment

1. Snapshot: date, source paths/versions, milestone, analysis mode and boundaries.
2. Summary: scope examined, principal risks, and counts derived from the rows.
3. Items table (document-only shape; add Jira coverage/evidence for Jira runs):

   | ID / source-derived name | Source citations | Listing / bullet relied on | Confidence | Placement / decision |
   |---|---|---|---|---|

4. Boundary items: source ID, proposed other milestone, reason, disputed alternatives.
5. Excluded items: source ID, exclusion citation, applicable conditions/carve-outs.
6. Unsupported bullets: quote/anchor the bullet, evidence searched, historical or
   supporting evidence if any, current-authority gap, and requested decision.
7. Acceptance/consistency findings and known limitations applicable to this milestone.

## Merged coverage assessment

1. Snapshot and source map: roles, precedence, paths/versions, milestone filename
   mapping, execution mode, and whether this is a full or selected analysis.
2. Headline counts: enumerate units and reconcile to rows. Keep authoritative,
   historical, supporting-only and reverse-check counts distinct.
3. Absent items: stable finding IDs, source IDs/citations, proposed homes or
   unresolved placement, confidence, and clarification questions. Proposed ownership
   does not change an absent listing classification.
4. Implicit items by milestone with the broader bullet and its interpretation.
5. Exclusions and unsupported bullets with evidence; acceptance-definition gaps.
6. Boundary resolutions, open decisions and cross-cutting findings.
7. Full-run coverage ledger (omit columns for sources not supplied):

   | Source ID / item | Parent/source anchor | Document disposition / coverage / evidence | Jira disposition / coverage / issue evidence | Finding/report link |
   |---|---|---|---|---|

   Enumerate every authoritative inventory item, including all split children;
   report omissions and duplicates, with reconciled counts. A gap may be unresolved
   ownership rather than absent wording—explain which. Supporting findings belong
   in their own table and must not inflate the authoritative inventory.
8. Historical reconciliation when supplied:

   | Version / original item ID | Source citation | Status | Current item/bullet or exclusion citation | Loss/decision |
   |---|---|---|---|---|

   Use the five historical statuses from SKILL.md, with separate parts for bundled
   lines. For a selected run, replace the global ledgers with local comparisons
   and explicitly state that the global sweep/reconciliation was not performed.
9. Known limitations: source availability and ambiguity, comparison baseline,
   interpretation and placement judgments, citation precision, execution and
   selection limits. State "Whole-SoW completeness was not assessed" for selection.
10. Suggested next steps: document clarification and scope decisions, not tracker
    writes or implementation task breakdowns.

## Jira additions to the same reports

- Snapshot: configured site/account identity (no credentials), query/filter, date,
  milestone mapping, selected scope, source pages/details, returned unique keys,
  pagination/content/access completeness and any unresolved boundaries.
- Evidence per requirement: issue key/link plus description/AC field or JSON pointer,
  covered and uncovered parts, contributing milestones, confidence and decision.
  Preserve unknown/unassessed separately from no ticket. Exclusions are separate
  dispositions; ticket-level exclusions do not override authoritative scope.
- Search log: summary candidates, full-text terms/results, description reads and
  linked/parent evidence. Qualify no-ticket findings by searched snapshot and scope.
- Named bundled-ticket findings: one key, all requirement IDs/parts, status, and
  verification risk without claiming anything is implemented or missing in the build.
- Keep doc/Jira totals separate. List unsupported ticket scope, undestined deferrals,
  evidenced plan drift and elsewhere coverage without inflating requirement counts.
- Selected runs use local comparisons, not a global ledger/sweep. State the
  whole-requirements completeness limitation even if all input pages are available.
