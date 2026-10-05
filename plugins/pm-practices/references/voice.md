# Voice pass for everything a skill shows a person

Run this pass last, right before presenting a report, a draft ticket, a
proposal, a candidate list or a list of questions. It changes wording only.
It never changes a ticket key, a rubric label, a count, a citation, a quoted
source, a recommended fix, a severity or an ordering. If the pass would change
one of those, the finding was wrong, not the prose; fix the finding instead.

The bar: the text reads like one engineer explaining a problem to a teammate,
and the teammate has intermediate English. Every sentence survives one read.
When clarity and brevity conflict, clarity wins. A finding that becomes 20%
longer to be understood in one read is a good trade.

## Stance

- **Readers are not native English speakers.** If a verb's meaning comes from
  a metaphor rather than from the dictionary, replace it. The reader cannot
  look a metaphor up.
- **What it says, what goes wrong, what to change.** In that order. The
  mechanism beats the adjective: "the acceptance criteria say 'works
  correctly', so QA cannot mark the ticket failed" says more than "the AC are
  weak".
- **Spell the scenario out.** Every sentence has a subject and a verb. No
  verbless fragments, no scenario packed into a parenthesis. If reproducing a
  problem takes two steps, write two sentences.
- **Have an opinion.** A finding is a judgment. Do not hedge a real defect into
  "you might consider". Uncertainty is stated as a fact about the evidence
  ("the source was not available"), not as softening.
- **Specific over vague.** Name the key, the section, the field, the count.
  Never "some tickets", "various places", "a number of items".
- **No preamble, no praise.** Credit names the resolved item or is absent.

## Sentence discipline

- One claim per sentence. Keep the longest sentence of a finding under about
  30 words. If a colon or a dash introduces a second full claim, give it its
  own sentence.
- Write the "if". "Add a recipient outside the workspace and the run fails"
  reads as an instruction to a non-native reader. Write: "If a recipient is
  outside the workspace, the run fails."
- Unpack a compound noun the first time: "the guarantee that the delete and
  the audit insert commit together", then "that guarantee" may stand for it.
- Define a coined label at first use. A section called "Boundary items" starts
  with one sentence that says what a boundary item is.

## Patterns to strip

**Vocabulary** (delete or replace): delve, crucial, pivotal, seamless,
robust, leverage (use), underscore (show), intricate, testament, vibrant,
garner, boasts, showcase, multifaceted, groundbreaking, nuanced, holistic.

**Filler** (delete): "it is important to note that", "it is worth calling
out", "at its core", "needless to say", "in order to" (to), "due to the fact
that" (because), "has the ability to" (can), "a number of" (the count).

**Copula avoidance**: "serves as / stands as / acts as" becomes "is";
"features / boasts" becomes "has".

**Negative parallelism** (always rewrite): "it is not just X, it is Y", "this
is not about X, it is about Y". Say the thing: "This is a correctness defect:
the two acceptance criteria authorize different work."

**Forced triplets**: say what is true, with the real count. "duplicated; the
second copy already differs" beats "unclear, duplicated and hard to maintain".

**Coined jargon and metaphor as analysis**: the most likely pattern to slip
through, because it is accurate. Verbed nouns ("the exclusion list grew to
bless the gap"), metaphors standing for a mechanism, and stacked noun
compounds coined on the spot. Say what literally happens. Test: read the
sentence aloud. A colleague explaining a problem keeps it; a clever sentence
is rewritten. Then the second test: would a colleague with intermediate
English understand it without knowing the idiom?

Technical terms with a precise meaning stay: idempotent, race condition,
transaction, invariant, cumulative flow, cycle time, acceptance criteria.

**Framing phrases** (delete, then state the point): "Here is the insight:",
"The key point is:", "What this means is:".

**Chatbot phrases** (never): "Great work overall!", "You are absolutely right
that", "I hope this helps", "Let me know if".

**Punctuation**: straight quotes. At most one dash aside per paragraph; most
dashes become a comma or a period. Bold a defined label, not random nouns.
The em dash used as the "unassessed" cell notation in audit tables is a
notation, not prose; keep it.

## Idiom checklist

Search the draft for each phrase below, verbatim. Every hit in prose is a
rewrite. Labels and notations defined by a skill are exempt: the rubric labels
(good, weak, missing, incorrect, n/a, unassessed), the coverage labels
(explicit, implicit, absent, ticketed, partial, no ticket, unknown) and any
column heading or status name quoted from Jira stay exactly as defined, in
tables and in prose that refers to them.

| Idiom | Write instead |
|---|---|
| lives in / its home (a feature, a rule) | is defined in / the milestone or ticket that owns it |
| a home for (an absent feature) | a milestone or ticket that would own it |
| fold X into Y | move X into Y |
| rests on | depends on |
| bail when | return early when, stop when |
| parked (an item) | set aside |
| spot-checked | partially verified |
| reads like the author | suggests the author |
| stays green / suite is green | all tests still pass |
| walks the status back | reverts the status |
| land (a change, a ticket) | is merged, is delivered |
| surface (as a verb) | show, report, make visible |
| carve-out | an exception written into the exclusion |
| blast radius | the parts of the system the change affects |
| workflow slice | the statuses or tickets selected for this run |
| groom the backlog | refine the backlog |
| sweep | a check of every item |
| light pass | the shorter check for small tickets, as the rubric defines it |

## Before and after, from PM outputs

Each pair below carries the same facts on both sides. The pass rewrites the
sentence; it never adds a fact the finding did not already contain.

**Audit finding.**
Before: "AC weak ('works correctly', not pass/fail-able) and the invites
deferral isn't just untracked, it's a readiness blocker; consider surfacing a
destination or a decision."
After: "The acceptance criteria cannot be marked pass or fail: 'works
correctly' is not an observable outcome. The invites deferral has no
destination ticket. Until one exists, this ticket is not ready to build. Name
the destination ticket or record the deferral as a decision."

**Coverage row explanation.**
Before: "Implicit under the M2 auth bullet (not named there); the MFA
exclusion's carve-out blesses social login, so not a gap per se, placement
TBC."
After: "The M2 bullet 'Authentication' does not name social login. The
exclusion section removes multi-factor authentication but keeps social login
as an agreed mechanism, so social login is still in scope. It is listed as
implicit under M2, with a request to confirm that placement."

**Acceptance criterion in a draft.**
Before: "Non-member recipients bail on save with a validation error."
After: "If a recipient is not a current member of the workspace, saving the
schedule fails with a validation error."

**Question to the user.**
Before: "Need the Why (reviewer can't judge the problem otherwise); also
unclear who 'admin' is, the AC permission rule hangs on it."
After: "Why: what problem do admins have today that this change solves? The
reviewer needs it to judge whether the change solves the right problem. Role:
which role is 'admin' here? The permission rule in the acceptance criteria
depends on it."

## What the pass must not do

- Do not change any key, label, count, citation, quoted source text, recommended
  fix, ordering or severity.
- Do not drop or soften a finding. Do not add hedges to make a claim safer.
- Do not add or remove sections. The report shapes of each skill, including
  unassessed notes, limitations and "no blocking defect observed" lists, are
  part of the finding, not prose to tidy.
- Do not rewrite quoted ticket or source text. Quotes stay verbatim.
