# Config and field identity

Read the supplied/established private `jira-project.json` if it exists; otherwise
take the equivalent values from the user. Reuse the shared keys:
`base_url`, `project_key`, `story_points_field` (custom field ID or null). Refinement does not
require any JQL, title, status mapping or threshold the file may also hold for
other skills, and does not repurpose such a JQL as bulk triage scope. A missing explicit config path is reported; proceed from arguments only
if they resolve the needed settings, not by silently selecting another site.

Optional refinement settings in the same file can identify extra fields:

```json
{
  "base_url": "https://jira.example.invalid",
  "project_key": "DEMO",
  "story_points_field": "customfield_99999",
  "refinement_fields": {
    "Area": {
      "id": "customfield_99998",
      "type": "single_select",
      "options": {"Portal": "99001", "Reporting": "99002"}
    }
  }
}
```

These values are invented, not defaults. Only the requested fields are relevant;
do not require every project to have Area or Form. Never copy cloud IDs, users,
field IDs or option IDs from another project. If a connector needs a cloud ID,
resolve it for the confirmed site through its available resources; do not bake
one into the skill. A null points field disables point writing until a verified
field is supplied; it does not mean clear every estimate.

Confirm the active authenticated site and project against the inputs. Use the
existing ACLI account/wrapper; do not log in, switch accounts, install tools or
read credential files as an implicit setup step. Check editable field metadata
and allowed values for the actual project/issue type before custom-field writes.
Config mappings are hints that can go stale. A known-good ticket illustrates a
value but does not prove it is editable or allowed on a different issue type.

# Supported transport, not guessed payloads

Start with installed ACLI help. Commands checked with ACLI 1.3.29:

```sh
acli jira workitem view "$key" --fields '*all' --json
acli jira workitem comment list --key "$key" --paginate --json
acli jira workitem edit --help
acli jira workitem edit --generate-json
```

`--generate-json` is local schema discovery, not an edit. Inspect it in a private
temporary directory and strip every unrequested sample field. Its edit schema
has `issues`, `description`, `summary` and other standard fields, **not a generic
REST `fields` envelope or documented arbitrary custom-field slot**. Do not guess
`customFields` or insert `customfield_*` at its root and claim support.

For a description-only ACLI edit, a minimal payload is:

```json
{
  "issues": ["DEMO-1"],
  "description": {
    "type": "doc",
    "version": 1,
    "content": [{"type": "paragraph", "content": [{"type": "text", "text": "Approved text"}]}]
  }
}
```

After approval and a fresh read, apply the private payload with
`acli jira workitem edit --from-json "$payload" --yes --json`. The file must
contain exactly the approved issue key and fields. `--yes` satisfies the CLI's
prompt, not the user's approval requirement. `--description-file` supports plain
text or ADF; markdown is not documented as converted to rich content here.

For points/select edits, inspect whether the installed version now supports them.
Otherwise use an already available, authorized Jira REST/connector edit operation,
explaining that transport before approval. Do not switch platforms to TWG or
build a custom authentication wrapper. If no supported authenticated writer or
editable metadata reader is available, stop with the proposal and identify the
missing capability; do not make unsupported fields appear applied. Do not apply
only the description from an approved combined proposal without permission for
that partial operation.

Jira Cloud REST v3 uses a different envelope, for example:

```json
{
  "fields": {
    "customfield_99999": 3,
    "customfield_99998": {"id": "99001"}
  }
}
```

Single-select options commonly use an ID object; multi-select uses an array of
option objects; numbers use JSON numbers. Verify the field's actual schema and
allowed operation, not just this example. Omit unchanged fields. Clearing a
field requires explicit approval and its documented empty representation; neither
"always null" nor "never null" is correct for every field.

Every description write, through ACLI or REST, carries an Atlassian Document
Format (ADF) document, not markdown or a list of text lines. Build `heading`,
`paragraph`, `bulletList`/`orderedList` with `listItem`, `text` with `link`
marks and `codeBlock` nodes from the approved draft. A connector may explicitly support a markdown-string conversion mode;
use that only if its tool schema documents it. Preserve paragraphs, heading
levels, lists and links semantically; do not retry by blindly changing formats.
Prefer source-provided comment URLs. Otherwise cite the issue URL plus exact
comment ID/author/date; only construct a deep link if its format is verified for
the configured site. Never hardcode the draft's UI query parameters as universal.

References: [ACLI edit](https://developer.atlassian.com/cloud/acli/reference/commands/jira-workitem-edit/),
[Jira issue edit and edit metadata](https://developer.atlassian.com/cloud/jira/platform/rest/v3/api-group-issues/),
[Jira Cloud v3 rich-text format](https://developer.atlassian.com/cloud/jira/platform/rest/v3/intro/).
