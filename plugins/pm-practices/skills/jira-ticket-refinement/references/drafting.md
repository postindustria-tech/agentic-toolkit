# Drafting subset

A ticket should let its implementer act and its reviewer verify the result.
The title predicts the content. Each AC must be capable of failing objectively;
"works properly" is not an AC. Scale detail with the cost of misunderstanding,
not a compulsory section count. Name non-obvious scope exclusions and keep
unlocated deferrals visible as tracking gaps. This is the small drafting subset
of ticket-quality guidance, not a second copy of its full audit rubric.

## Template

Use this order, with blank lines between headings, paragraphs and lists:

```markdown
### Summary

What changes, for which role/surface, and the intended outcome.

### Context

Why it matters, with links to the controlling requirement or decision.

### Current State

Optional: verified present behavior. Cite repository/ref/file/line when inspected.

### Acceptance Criteria

- Preconditions and action produce a specific observable outcome.
- A relevant negative or boundary case has a defined outcome.

### Dev Tasks

- Concrete implementation work grounded in the evidence available.
- Verification work for the agreed acceptance criteria.
```

Replace guidance text with actual evidence; do not upload the template itself.
Current State is optional for greenfield work or unavailable code. Dev Tasks
can name behavior/modules without invented file paths. Preserve bug starting
conditions, role/environment, reproduction steps, actual and expected behavior;
put them in Current State and AC without unnecessary duplication. Research
tickets need the question, constraints and deliverable, not invented feature QA
criteria. An exact one-line polish change can stay concise.

Quote comments only when helpful and retain their source ID/link. There is no
hardcoded decision-maker or universal comment precedence. If a later comment
conflicts with a controlling source, expose the decision instead of silently
implementing "latest wins". Source absence is not permission to invent limits,
roles or error behavior. Mark unresolved questions separately from decided AC.

Preserve accessible links, tables, code blocks, mentions, attachments and relevant
requirements when restructuring. Plain-text extraction may miss important ADF
nodes; inspect the rich structure before replacing a description. If preservation
cannot be assured with the available writer, stop at the draft and explain why.

## Fibonacci proposal scale

| Points | Guidance, not a conversion from hours or file count |
| --- | --- |
| 1 | Tiny copy, constant or isolated obvious change |
| 2 | Small, clear, localized scope with little uncertainty |
| 3 | Straightforward change across a few related parts |
| 5 | Coordinated interfaces/components or meaningful investigation |
| 8 | Significant feature, state changes or multi-service coordination |
| 13 | Too broad: propose coherent breakdown; do not assign automatically |

Explain blast radius, uncertainty and verification effort. Do not assume two
files always means 3 points or a frontend/backend split always exists. If crucial
scope is undecided, leave the estimate pending rather than guessing. Zero/missing
values must not be silently treated as approval to estimate. If the team requests
a different scale, surface that conflict and obtain direction instead of quietly
rounding its numbers. Breakdown suggestions are proposals, not authorization to
create tickets, link them or redistribute existing points.
