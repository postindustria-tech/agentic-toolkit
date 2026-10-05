# Structure rules, project metadata and creation

## Choosing the shape

| Situation | Shape |
|---|---|
| One buildable, reviewable, closeable outcome, 8 points or less | One ticket (Task, Bug or Story as the project uses them) |
| One outcome, pieces not valuable alone, split only for parallel work or review size | Parent ticket with Subtasks |
| Several outcomes, each independently acceptable and closeable | Epic (or the project's parent level) with child tickets |
| Outcome would be 13 or more | Breakdown required; never a single 13-point ticket |

Ask of every proposed ticket: when it is marked done, is there one coherent
outcome to accept? If a child cannot be accepted on its own, it is a subtask of
something, not a sibling. If a parent would be "done" only when every child is
done and has no acceptance of its own, it is an epic-like container and should
carry outcome-level acceptance criteria rather than implementation ones.

Subtasks can only sit under a parent-level ticket, and a parent-level ticket
cannot be the parent of another parent-level ticket; only the level above can.
Use the hierarchy read from the project, not these generic names: a project may
lack Story, use a different parent level name, or disable subtasks.

Points go on the tickets that get built: children in a breakdown, the single
ticket otherwise. A parent with pointed children stays unpointed. If the user
wants parent points as well, say that reports will count the work twice unless
the parent is excluded there, and let the user decide.

## Reading project metadata

Issue types with their hierarchy level and subtask flag come from the project
view of the installed ACLI (checked with ACLI 1.3.29):

```sh
acli jira project view --key "$project_key" --json
```

Read `issueTypes[].name`, `issueTypes[].hierarchyLevel` and
`issueTypes[].subtask`. The project view does not list required fields. Those
come from the create metadata of Jira Cloud REST v3, with the same account the
other skills use (`JIRA_EMAIL` and `JIRA_API_TOKEN` environment variables, Basic
auth; never ask for the token in chat or print it):

```text
GET {base_url}/rest/api/3/issue/createmeta/{project_key}/issuetypes
GET {base_url}/rest/api/3/issue/createmeta/{project_key}/issuetypes/{issue_type_id}
```

Both responses are paginated: read `startAt`, `maxResults` and `total` (or
`isLast`) and request the next page until every item has been returned. A
required custom field on a later page is as binding as one on the first, and
a create that omits it fails after approval. Collect `fields[].required` per
type from the complete set only. Summary, project and reporter are usually
required and the tool fills them; a required component, priority or custom field
must be in the draft before approval. If a page could not be retrieved, the
required-field list is incomplete: say so, do not declare the payload ready, and
ask before creating. If neither read is possible, say which facts are unknown
and keep the plan to the types the user confirmed.

## Duplicate search

Search the project by the distinctive words of the brief, open tickets first and
then recently delivered ones, with validated JQL and quoted values:

```sh
acli jira workitem search --jql "$jql" --fields 'key,summary,status,issuetype,parent' --paginate --json
acli jira workitem view "$key" --fields '*all' --json
```

Recipe fragments (substitute the validated project key and the team's resolved
states):

- Open work on the subject: `project = "DEMO" AND statusCategory != Done AND text ~ "members csv"`.
- Recently delivered work on the subject: `project = "DEMO" AND statusCategory = Done AND resolved >= -90d AND text ~ "members csv"`.

Text search is approximate. Try the user's vocabulary and the likely synonyms
once, read the candidates fully, and record the queries used. Search may reject
some field names; check local help.

## Create payload

Inspect the installed tool's schema before building a payload; it is local
discovery, not a write:

```sh
acli jira workitem create --generate-json
```

With ACLI 1.3.29 the schema has `projectKey`, `type` (case sensitive),
`summary`, `description` (ADF document), `labels`, `parentIssueId`, `reporter`,
`assignee` and an `additionalAttributes` map for `customfield_*` values. A
minimal approved payload:

```json
{
  "projectKey": "DEMO",
  "type": "Subtask",
  "summary": "Approved title",
  "parentIssueId": "10042",
  "description": {
    "type": "doc",
    "version": 1,
    "content": [{"type": "paragraph", "content": [{"type": "text", "text": "Approved text"}]}]
  }
}
```

The description is always an Atlassian Document Format (ADF) document, on
create and on any later edit. Build it from the approved markdown: `heading`
nodes with their level, `paragraph`, `bulletList` and `orderedList` with
`listItem` children, `text` nodes with a `link` mark for links, and
`codeBlock` for code. Do not send markdown or plain text as the description
string and call it formatted; Jira shows it as one block. The ACLI
`--description` and `--description-file` flags accept plain text or ADF and do
not convert markdown. Omit every field that was not
approved; do not include sample values from the generated schema.

Create with `acli jira workitem create --from-json "$payload" --json`, one call
per ticket, parent before children. Take the parent id for the children from
the parent's read-back, not from an assumption about key or id format. The
schema documents `parentIssueId` for subtasks; whether the same field attaches a
child to an epic, and whether `additionalAttributes` sets the points field, must
be confirmed by read-back on the first real create in a project. If either does
not apply, use an already authorized Jira REST edit on the new key with the
same rules the refinement skill documents, or report the field as pending.

Jira Cloud REST v3 create, when used instead of ACLI, takes a `fields` envelope
with `project`, `issuetype`, `summary`, `description` (ADF), `parent` as
`{"key": "DEMO-1"}` and custom fields by id. Verify the field schema for the
project; do not guess option ids.

## Read-back and failure handling

After each create, read the new ticket with `--fields '*all'` and compare
summary, description structure, type, parent, labels and points with the
approved draft. Record per ticket: created and verified, created with pending
fields, or not created. A success response without a readable ticket is not a
verified create.

On a timeout or unclear error, stop. Search the project by the exact summary
before retrying; a create that timed out may have succeeded. Never replay the
batch, never delete a ticket to clean up, and do not create children while the
parent's state is unknown. Report what exists and what remains, then wait.

References: [ACLI workitem create](https://developer.atlassian.com/cloud/acli/reference/commands/jira-workitem-create/),
[Jira issue create and create metadata](https://developer.atlassian.com/cloud/jira/platform/rest/v3/api-group-issues/),
[Jira Cloud v3 rich-text format](https://developer.atlassian.com/cloud/jira/platform/rest/v3/intro/).
