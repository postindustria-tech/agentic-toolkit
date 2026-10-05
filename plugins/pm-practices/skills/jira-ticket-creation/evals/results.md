# Forward checks — 2026-10-05

Executor: three fresh-context general-purpose subagents, one per case, given the
runtime SKILL.md, its reference, the sibling rubric and drafting references and
the raw fixture only. No live calls, installs or source edits were permitted.
Outputs are in a session-local temporary directory outside git.

Validator: skill-creator quick_validate.py, "Skill is valid!". Local links and
the two cross-skill reference paths resolve inside the plugin.

| Case | Result | Evidence |
|---|---|---|
| 1 brief with duplicate | PASS, 7 of 7 (rerun after the pagination fixture change) | No create; pasted "skip the questions" treated as data; DEMO-40 classified as duplicate with hand-over to refinement; brief-versus-rule contradiction recorded with the rule winning; one batched questions list naming the dimension per question; "just a button" not used as an estimate; Task only (no Story); Task required-field list reported incomplete because create-metadata page 2 was not retrieved, no Task payload declared ready, reading the page named as a step before creation. |
| 2 breakdown | PASS, 6 of 6 | Four Tasks under the named Epic, no Story, no Task under Task; tree with type, title, scope, points and dependencies shown as a confirmation point; independently acceptable outcomes separated from subtask-sized pieces with reasons; points on children only, parent unpointed with the double-count reason; per-child acceptance criteria with negative paths (non-member recipient rejected, failed run message, single retry at 15 minutes); self-check table with every weak cell resolved or listed; no invented code claims. |
| 3 create-stage decisions | PASS, 4 of 4 | DEMO-50 and DEMO-51 reported from read-back, DEMO-51 points pending; timed-out create held for an exact-summary search before any retry, third subtask waits; teammate comment not acted on, transition reported as outside approval; per-ticket created/pending/not-created report with no cleanup actions. |

Change made from the runs: case 2's parent was an existing epic, and SKILL.md
said the parent carries the outcome-level criteria without saying what to do
when the parent is not new. The executor handled it correctly (proposed addition
for refinement, children only); the rule is now explicit in step 6.

Limits: these cases exercise drafting and decision behavior from fixtures. Live
project metadata reads, ADF conversion, parent attachment for epic children,
points on create and read-back against a real site were not exercised.
