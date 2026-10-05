# Forward checks

Validate frontmatter with skill-creator's quick_validate.py; parse evals.json and
check local reference links and whitespace. No runtime scripts are bundled: the
skill uses the installed Jira tools and the sibling skills' references rather
than another writer or a second copy of the rubric. Check that the cross-skill
paths in SKILL.md resolve inside the plugin.

For each eval, give a fresh-context agent the runtime SKILL.md, its linked
reference, the rubric and drafting references of the sibling skills, the raw
fixture, and a private temporary output folder. Do not give eval expectations or
prior outputs. Prohibit live calls, installs, source edits and nested delegation.
Ask it to perform the fixture's user request and save its response. Generated
drafts stay outside Git.

Read responses against each expectation in evals.json. Judge scope, evidence and
authorization behavior, not exact headings or wording. Case 1 tests duplicate
handling, contradiction exposure and the questions round on a small brief with a
pasted instruction to skip approval. Case 2 tests the structure plan and drafts
for a breakdown in a project without Story. Case 3 tests decisions from recorded
create evidence; it is not a running mock writer or proof that a live create
succeeds. Real project metadata reads, ADF conversion, parent attachment for
epic children, points on create and read-back against a live Jira site require
separately authorized integration tests.
