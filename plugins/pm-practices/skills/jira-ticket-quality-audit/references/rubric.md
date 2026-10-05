# Ticket quality rubric

A good ticket lets its implementer act and its reviewer verify the result. This
is not a mandatory template. Dimensions are independent: excellent AC can coexist
with a contradiction or a misleading title.

## Labels

| Label | Meaning |
|---|---|
| good | Present and usable without material clarification |
| weak | Present but clarification is needed |
| missing | Absent where needed, confirmed from available full content |
| incorrect | Present but demonstrably wrong; authorizes wrong work |
| n/a | Genuinely inapplicable to this ticket's type or size; explain why |

Unavailable evidence is **unassessed**, not n/a or missing. Use the report's
unassessed notation and retain any independently demonstrated defect.

## Nine dimensions

### 1. Title

Does it predict the feature/defect and the size of the work? Name the change, not
just the area. A title such as "Search request returns 500 for an empty query"
is useful; "Search improvements" conceals what will be delivered. Surface scope
hidden in the body even when the main feature matches the title.

### 2. Why

Is the current problem, affected person/system and consequence clear? "Improve
UX" is weaker than "Members cannot tell whether their reservation was submitted".
Do not demand a separate Why heading when the motivation is already evident.

Motivation helps implementers make small judgment calls and reviewers judge
whether the change solves the right problem.

### 3. Completeness & scope

Check both internal specificity and alignment to the controlling source for this
ticket's slice. Are surfaces, fields, roles, rules, flows and decided models
concrete? Are relevant source obligations accounted for, with justified boundaries
and explicit destinations for deferred work? Check meaningful empty/error/other-role/
cancellation paths; do not invent exhaustive edge cases unrelated to the change.
"Where allowed" needs a permission authority. An undecided limit must be exposed
as a decision, not silently filled in. Record the absence of a controlling source
instead of inventing one or claiming the external check passed.

At a non-obvious boundary, an explicit, justified out-of-scope statement is a
strength. Silence is weak when it leaves material scope ambiguous, not merely
because an out-of-scope heading is absent.

### 4. AC

Can each criterion be marked pass/fail objectively? Does the set establish relevant
preconditions, triggers and observable outcomes, including negative/boundary paths?
Does it cover what the scope promises? "Works correctly" is not an observable
test. Given/When/Then syntax is optional. "Designer supplies the asset" is a
dependency, not an implementation acceptance criterion.

### 5. Correctness

Do Why/What/AC agree? Do referenced artifacts support the assertion? Are claims
about current behavior true when evidence is available? For example, "delete the
temporary channel" and "temporary channel remains accessible" authorize different
work unless the distinction is explained. A proven stale code diagnosis is
incorrect, not merely weak. Access denied is not proof of a broken reference.

### 6. Consistency

Does the ticket use current vocabulary/models and agree with related tickets or
explicitly supersede them? A documented model change is not a defect. Silent
divergence needs a cited comparison, not the assessor's preferred terminology.

### 7. Size

Is this one buildable, reviewable, closeable outcome? Multiple AC can verify one
outcome; do not demand one test per ticket. Independently deliverable capabilities
hidden under one task risk partial completion being concealed by closure. A rule
fragmented across tickets with no complete owner is the opposite failure. Recommend
a coherent parent with explicit children where useful, without creating them.

Ask: when this ticket is marked done, is there one coherent outcome to accept?

### 8. Relations

Are dependencies, overlaps, parents and deferrals identified with resolvable keys
and boundaries? Check both prose and metadata. If a deferred workflow's ticket
exists but its key is omitted, recommend linking that key; if no destination is
located, state search limits. A completed parent with an unexplained open child
needs reconciliation, not automatic closure of the child.

A confirmed untracked deferral is at least weak under Relations and a readiness
gap. If incomplete retrieval or inaccessible evidence prevents establishing
whether a destination exists, that check is unassessed instead; do not turn a
limited search into proof that no ticket exists.

### 9. Repro (bugs)

Require a known starting state and actionable reproduction steps, expected and
actual results, role and environment where relevant, and useful accessible evidence.
A precise title may carry the symptom; it need not be repeated ceremonially, but
it cannot substitute for missing conditions needed to reproduce. Do not penalize
absence of a screenshot when a request/response is sufficient. A bug's expected
behavior must be checked against its cited specification, not assumed correct.

"Doesn't work properly" does not identify a symptom. In a multi-role system,
"user" does not identify the role needed to reproduce the bug.

## Applicability and assessment effort

The bar and assessment effort scale with the cost of misunderstanding the ticket,
not its category name alone.

- Implementation stories/tasks/bugs receive full review of applicable dimensions.
  Bugs can express Why and AC through impact and expected behavior; do not demand
  duplicated prose. Repro is n/a for non-bugs.
- Epics and parent tasks intentionally span work: judge a coherent outcome and
  child coverage, not implementation-ticket size. Use n/a for implementation QA
  criteria where inappropriate; missing child evidence is unassessed, not failure.
- Research/design/decision tickets need a question, constraints and expected output
  (decision, design or recommendation), not feature-level QA criteria. Assess those
  under scope; AC may be n/a when that output definition is sufficient.
- Genuinely small UX-polish tasks get a batched light pass: read each fully, check
  Title, unambiguous change under Completeness & scope, and any necessary design
  reference under Correctness. Other dimensions are n/a with a shared light-pass
  explanation. An exact self-contained spacing value need not have a design link.
  Escalate to full review if contradictions or hidden scope emerge. Bugs are not
  exempt from reproduction checks because the visual change looks small.

## Prioritization

Incorrect assertions first, hidden scope (title/size) second, then cheap gaps such
as missing motivation or weak AC. This is judgment guidance, not a numerical
formula. Open decisions and prerequisites can block otherwise well-written work;
make that visible in readiness recommendations. No overall average can cancel a
contradiction.

## Sources

This rubric adapts these sources to prose tickets and project-context review;
it is not a verbatim checklist from any one framework.

- [Bill Wake: INVEST in Good Stories, and SMART Tasks](https://xp123.com/articles/invest-in-good-stories-and-smart-tasks/) — value, size and testability.
- [QUS framework / AQUSA project](https://github.com/RELabUU/aqusa-core) — the framework informs completeness, clarity and freedom from conflicts; the tool checks only a syntactic subset.
- [Mozilla: Bug Writing Guidelines](https://bugzilla.mozilla.org/page.cgi?id=bug-writing.html) — actionable reproduction, expected and actual results.
- [Joel Spolsky: Painless Bug Tracking](https://www.joelonsoftware.com/2000/11/08/painless-bug-tracking/) — useful bug reports.
- [Cucumber: Gherkin Reference](https://cucumber.io/docs/gherkin/reference/) — preconditions, triggers and observable outcomes, without requiring its syntax.

A text-only linter cannot establish these contextual checks: contradictions,
source-relative omissions and untracked deferrals require project evidence,
although tools can assist the review.
