# Forward checks

Validate frontmatter with skill-creator's quick_validate.py; parse evals.json and
check local reference links and whitespace. No runtime scripts are bundled: this
skill uses available Jira tools rather than implementing another writer.

For each eval, give a fresh-context agent the runtime SKILL.md and its linked
references, the corresponding raw fixture, and a private temporary output folder.
Do not give eval expectations or prior outputs. Prohibit live calls, installs,
source edits and nested delegation. Ask it to perform the fixture's user request
and save its response. Real/synthetic generated reports stay outside Git.

Read responses against each expectation in evals.json. Judge semantic scope,
evidence and authorization behavior, not exact headings or wording. Case 1 tests
drafting with conflicting comments, no repo and limited tool capability. Case 2
tests decisions from recorded approval/read/write evidence; it is not a running
mock writer or proof that a live edit succeeds. Candidate discovery pagination,
real custom-field permissions, ADF preservation and write verification against a
live Jira site require separately authorized integration tests.
