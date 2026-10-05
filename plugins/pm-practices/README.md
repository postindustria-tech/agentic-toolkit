# PM Practices Plugin

**Version**: 0.1.0

**Status**: Skills are tested with fixture-based evals and ready to use.

Project-management skills for teams that plan in documents (statements of work,
milestone plans) and track work in Jira Cloud. The skills are project agnostic:
every site, project key, field id and status name comes from your input or a
private config file, never from the plugin.

## Installation

```bash
/plugin marketplace add postindustria-tech/agentic-toolkit
/plugin install pm-practices@agentic-toolkit
```

## Which skill to use

| You want to know or do | Skill | Writes to Jira? |
|---|---|---|
| Does the plan (document milestones, Jira epics or both) cover every agreed requirement? | `requirements-coverage-audit` | No |
| Are these existing tickets clear, complete, consistent and testable? | `jira-ticket-quality-audit` | No |
| Rewrite existing tickets: description, acceptance criteria, dev tasks, points, fields | `jira-ticket-refinement` | Only approved changes |
| Turn a brief, bug report or requirement gap into new tickets, including a breakdown | `jira-ticket-creation` | Only the approved set |

Typical order: coverage audit finds requirements with no ticket, ticket creation
creates them, quality audit scores what exists, refinement fixes what the audit
found. Each skill also works alone.

The audits are read-only. Refinement and creation draft first, show the exact
keys and fields, and write only after you approve. Both write descriptions as
Atlassian Document Format documents so headings, lists and links survive.

## Setup

### Jira access through ACLI (audits, refinement, creation)

Install the Atlassian CLI (`acli`) and authenticate once per site:

```bash
acli jira auth login
acli jira auth status
```

If you work with several sites, keep one config directory per site and run the
skills through a small wrapper that sets `ACLI_CONFIG_DIR`. Tell the skill which
wrapper or command to use; a skill never logs in, switches accounts or installs
tools on its own.

### Jira access through the REST API (ticket creation metadata)

Ticket creation reads required-field metadata through the Jira Cloud REST API.
Create an API token at https://id.atlassian.com/manage-profile/security/api-tokens
and export:

```bash
export JIRA_EMAIL="you@example.com"
export JIRA_API_TOKEN="..."
```

Never paste the token in chat or pass it on a command line.

### Project config

Refinement and creation share one private config file, usually named
`jira-project.json`, with `base_url`, `project_key` and `story_points_field`.
Keep the real file outside version control.

## Private outputs

Reports, snapshots, charts, drafts and payloads contain your ticket text and
people's names. Every skill writes them to a new private temporary directory
unless you name a directory that is not tracked by git. No skill modifies ignore
rules or commits outputs.

## Voice of the outputs

Reports, drafts and questions are written for readers with intermediate
English. Each skill runs the pass in `references/voice.md` before it presents
anything: one claim per sentence, the mechanism instead of adjectives, no
metaphors or engineering idioms, no AI filler. The pass changes wording only,
never keys, labels, counts, citations or fixes.

## Skills

| Skill | Purpose |
|---|---|
| `requirements-coverage-audit` | Requirement-by-requirement coverage ledger against document milestones and Jira plans, with exclusions and historical versions |
| `jira-ticket-quality-audit` | Nine-dimension rubric scoring of open tickets, prioritized defects, rerun comparison |
| `jira-ticket-refinement` | Draft and apply approved descriptions, acceptance criteria, dev tasks, Fibonacci points and fields, with fresh-read and read-back checks |
| `jira-ticket-creation` | From a brief to approved new tickets: missing parts, contradictions, duplicates, structure plan, rubric self-check, create with read-back |

See each skill's `SKILL.md` for inputs and rules, and its `evals/` for the
fixture-based checks maintainers run.
