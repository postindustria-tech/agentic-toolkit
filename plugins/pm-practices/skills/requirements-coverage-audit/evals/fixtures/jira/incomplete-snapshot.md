# Synthetic Jira snapshot provenance

All people, IDs, keys and URLs are invented. These files model Jira REST v3
GET /rest/api/3/search/jql responses; companion notes are not API response fields.
Snapshot: 2026-09-07T10:00:00Z. Query: project = DEMO ORDER BY key ASC.
Milestones are fields.fixVersions names Opening day and Lending desk. DEMO-100
is a cross-release epic, not a milestone. All statuses are included.

The full search has two pages and 12 unique issues, including the parent epic.
page-1.json starts the sequence; its nextPageToken requests page-2.json, which
ends with isLast=true. No other tasks or linked issues are in this snapshot.
Provided descriptions contain the available acceptance text; there is no separate
acceptance custom field. DEMO-8 description was inaccessible and is omitted, not
empty; no companion issue detail could be retrieved. Other returned descriptions
are complete. Reports must distinguish pagination completeness from content access.
This is export-only evidence; do not query a live Jira account.

## Supplied subset

Only page-1.json is available for this run. The page identified by
nextPageToken=synthetic-page-2 is missing; its records were not retrieved.
The two-page/12-issue count describes the expected source, not a successful fetch.
Do not infer the missing page's content or treat the seven readable descriptions
on page 1 as the entire project.
