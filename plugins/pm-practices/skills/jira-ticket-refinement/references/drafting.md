# Drafting subset

A ticket should let its implementer act and its reviewer verify the result.
The title predicts the content. Each AC must be capable of failing objectively;
"works properly" is not an AC. Scale detail with the cost of misunderstanding,
not a compulsory section count. Name non-obvious scope exclusions and keep
unlocated deferrals visible as tracking gaps. This is the small drafting subset
of ticket-quality guidance, not a second copy of its full audit rubric.

## Template

Use this order, with blank lines between headings, paragraphs and lists. Why,
What and Acceptance Criteria are the names the ticket-quality rubric uses, so a
draft and an audit talk about the same parts:

```markdown
### Why

The problem today, who has it and the consequence, with links to the
controlling requirement or decision.

### Current State

Optional: verified present behavior. Cite repository/ref/file/line when inspected.

### What

Optional lead, at most two sentences: the outcome for the role/surface when
the ticket is done. It never lists the changes; delete it when the title or
the items already say the same. Then one item per change: a verb that names
the change, the place, and the behavior the change must deliver. See "What"
below. Verification work the acceptance criteria need, such as tests to add,
is listed in the same form.

### Acceptance Criteria

- Preconditions and action produce a specific observable outcome.
- A relevant negative or boundary case has a defined outcome.

### Open decisions

Optional: a choice the developer cannot make alone, with the item that depends
on it.

### Dependencies

Optional: tickets this work depends on or defers to, by key, with what each one
delivers and whether it is delivered yet.
```

Replace guidance text with actual evidence; do not upload the template itself.
Current State, Open decisions and Dependencies are optional; Current State is
usually absent for greenfield work or unavailable code. Items under What can
name behavior/modules without invented file paths. Preserve bug starting
conditions, role/environment, reproduction steps, actual and expected behavior;
put them in Current State and AC without unnecessary duplication. Research
tickets need the question, constraints and deliverable, not invented feature QA
criteria. An exact one-line polish change can stay concise.

Quote comments only when helpful and retain their source ID/link. There is no
hardcoded decision-maker or universal comment precedence. If a later comment
conflicts with a controlling source, expose the decision instead of silently
implementing "latest wins". Source absence is not permission to invent limits,
roles or error behavior. Keep unresolved questions under Open decisions, never
inside decided AC.

Preserve accessible links, tables, code blocks, mentions, attachments and relevant
requirements when restructuring. Plain-text extraction may miss important ADF
nodes; inspect the rich structure before replacing a description. If preservation
cannot be assured with the available writer, stop at the draft and explain why.

## What

Each item under What is an instruction to the developer, not a description of
the finished component. "Report endpoint: public, throttled, answers 204"
describes an endpoint; it does not say whether to create one, change one or
keep one. The AC say what must be true when the ticket is done. An item under
What says which change to make, and where, to get there. The test for every
item: a developer who reads only this item knows what to do, where, and what
the result must do.

- Start with the verb that names the change: create, add, change, remove,
  rename, move, configure, verify. The verb must agree with Current State;
  write "create" only when Current State shows the thing does not exist.
- Name the place in the same sentence: the repository and the module or
  surface. Name a file only when it was inspected and the change is bound to
  it. A label before a colon ("Terraform:", "Tests:") does not replace the verb.
- One change per item. If an item needs commas or semicolons to carry several
  requirements, put the requirements in a nested list under the item.
- Describe the behavior, not the implementation. Say what the change must do
  and where the result is visible. Leave the library, the pattern and the code
  structure to the developer. Include an implementation detail only when it is
  a real constraint: the team or a controlling source decided it, or the item
  fixes a bug whose evidence is a specific line. A detail that is only a
  suggestion is marked as one ("one option: ...") so the developer can choose
  differently.
- Names are implementation too: a route path and method, a table or column, a
  class, a setting, an environment variable. Leave them to the developer unless
  something outside the ticket already depends on the exact name: an existing
  caller, a published contract, a vendor configuration or a controlling
  source. Write "an endpoint that receives CSP reports", not
  `POST /api/v1/csp-reports`.
- A constraint carries its value ("reject bodies over 16 KB with 413"), names
  the source that holds the value, or is an open decision. "Throttled" and
  "body size limited" are adjectives, not instructions. Do not invent a value
  to satisfy this rule; name the gap instead.
- A ticket key is not a description. Say in a few words what the referenced
  ticket delivers. If that ticket is not delivered yet, the item depends on it:
  say so and list it under Dependencies.
- An exclusion is a full sentence: "Do not use a third-party report
  collector", not "No vendor".
- A value list (a header value, a config block) is not a task. Attach it to
  the item that writes it, or put it in the AC as the expected value.
- A choice the developer cannot make alone is an open decision, not a task.
  Keep it under Open decisions; the task that depends on it names it.

Before: "Report endpoint: `POST /api/v1/csp-reports` in the API, public,
throttled (DEMO-12 pattern), body size limited, logs the report with pino and
answers 204. No vendor."

After:

- Create an endpoint in the API repository that receives Content Security
  Policy violation reports from browsers; no such endpoint exists today.
  - Browsers send CSP reports without credentials, so the route has no
    authentication.
  - Limit how often one client can call it. DEMO-12 adds per-IP throttling
    for public routes and is not delivered yet, so it is a dependency.
  - Reject bodies over the agreed limit with 413. The limit stays under Open
    decisions until the owner sets it.
  - Write each report to the API log and answer 204 with an empty body.
  - Do not use a third-party report collector. The log is the only store.

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
