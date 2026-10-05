# Changelog

All notable changes to the pm-practices plugin are documented here.

## 0.1.0

### Added

- `requirements-coverage-audit`: compares the full requirement inventory with document milestones, Jira plans, or both, using a cited coverage ledger and explicit evidence limitations.
- `jira-ticket-quality-audit`: read-only ticket assessment using nine dimensions, five quality labels and separate unassessed evidence, with prioritized findings and rerun comparisons.
- `jira-ticket-refinement`: drafts descriptions, acceptance criteria, development tasks, Fibonacci estimates and project fields; applies only approved changes with freshness checks and read-back verification.
- `jira-ticket-creation`: creates new tickets from a brief; finds missing parts, contradictions and duplicates, plans the structure (single ticket, parent with subtasks, epic with children) from the project's own issue-type hierarchy, drafts against the ticket-quality rubric with the refinement template, and creates only the approved set with read-back verification. Questions and structure confirmation happen only when information is missing or the shape is a real choice; approval before any write is always required.
- Descriptions written by refinement and creation are Atlassian Document Format documents on every create and update.
- Reports, drafts and payloads go to a new private temporary directory by default; a user-chosen directory is used only after checking it is not tracked by version control.
- Shared `references/voice.md`: a final wording pass for every report, draft, proposal and question, written for readers with intermediate English; each skill points to it before its report or approval step.
- Plugin README with installation, skill selection, ACLI and REST setup and the private-output rule; the plugin is listed in the repository README.
