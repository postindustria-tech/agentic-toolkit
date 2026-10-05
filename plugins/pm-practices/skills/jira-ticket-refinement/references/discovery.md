# Read-only discovery and bulk selection

Use the user-supplied keys/JQL/filter. If "find untriaged" is unspecified, establish
project, workflow slice and what counts as untriaged (missing description,
estimate or a project-required field). Do not use someone else's fixed sprint,
unassigned-only rule, point cutoff, creation window or status names as defaults.

Prefer a lightweight search, then full reads for candidates:

```sh
acli jira workitem search --jql "$jql" --fields 'key,summary,status,issuetype,assignee' --paginate --json
acli jira workitem view "$key" --fields '*all' --json
```

Use the verified custom-field selector supported by the installed search tool if
needed, or read those fields on candidate details. Deduplicate keys and track
pagination/completeness. A result limit is not proof there are no more candidates.
If output is too large, save and inspect locally or page it; do not silently
add a date filter to make it fit. Real exports remain outside Git.

JQL recipe fragments (substitute validated project, field IDs and statuses):

- Missing estimate: `project = "DEMO" AND cf[99999] is EMPTY`.
- Missing required select: `project = "DEMO" AND cf[99998] is EMPTY`.
- Either missing: `project = "DEMO" AND (cf[99999] is EMPTY OR cf[99998] is EMPTY)`.
- Explicit unassigned slice: `project = "DEMO" AND assignee is EMPTY`.

Add only the requested workflow/sprint constraints. IDs in `cf[...]` are numeric
parts of verified customfield IDs. Quote/escape JQL values rather than splicing
untrusted text into queries or shell commands.

For empty descriptions, read content client-side. Null, empty plain text, or an
ADF document with no meaningful text or rich content is an empty candidate.
A short precise description is not empty; neither is an image/table-only document
automatically empty. Missing/denied fields are unknown, not empty. A search-text
match or description-length cutoff cannot establish ticket quality or completeness.
Do not invent a general JQL empty-description predicate without checking support.

Report candidate reasons separately from evidence limits. Discovery never
rewrites tickets or fills absent values. For bulk refinement, confirm the exact
set to draft when the request has not already selected it, then present each
proposal for approval. An approved candidate set is not an approved payload.
