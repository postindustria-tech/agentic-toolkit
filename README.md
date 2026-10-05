# Agentic Toolkit

Claude Code plugin marketplace for building agentic systems. Five plugins covering LangGraph development, development practices, BDD quality assurance, the neograph graph compiler, and project-management practices for Jira and document-based plans.

## Installation

```bash
# Add the marketplace
/plugin marketplace add postindustria-tech/agentic-toolkit

# Install specific plugins
/plugin install langgraph-dev@agentic-toolkit
/plugin install dev-practices@agentic-toolkit
/plugin install qa-bdd@agentic-toolkit
/plugin install neograph-dev@agentic-toolkit
/plugin install pm-practices@agentic-toolkit
```

**Upgrading from pi-dev?** See [UPGRADE.md](UPGRADE.md) for instructions.

## Available Plugins

### LangGraph Development (`langgraph-dev`) - v0.1.0

Tutorial-grounded patterns and best practices for LangGraph development.

| Component | Count | Status |
|-----------|-------|--------|
| Skills | 21 | Production ready |
| Commands | 5 | WIP |
| Agents | 1 | WIP |

**Skills cover:** state management, conditional routing, conversation memory, ReAct agents, multi-agent supervisors, human-in-the-loop, streaming, structured output, subgraphs and composition, basic and corrective RAG, document processing, error recovery, parallel execution, performance optimization, prompt engineering, memory store and knowledge, deployment patterns, testing agentic systems.

**Commands (WIP):** create-workflow, create-state, create-tests, create-agent, create-deployment.

**Agent (WIP):** workflow-validator.

---

### Development Practices (`dev-practices`) - v0.2.1

Quality-driven development workflows with beads task management integration.

| Component | Count | Status |
|-----------|-------|--------|
| Skills | 8 | Production ready |
| Agents | 5 | Production ready |

**Skills:**

| Skill | Purpose |
|-------|---------|
| `execute` | Molecular task execution — atoms chained in sequence, survives context compaction |
| `tdd-workflow` | Test-driven development cycle with sacred rule enforcement |
| `session-completion` | End-of-session checklist ensuring no work is lost |
| `code-review` | Multi-agent code review across 8 dimensions |
| `obligation-test` | Per-obligation behavioral test derivation |
| `remediate` | Fill entity test stubs batch-by-batch with TDD |
| `test-audit` | Audit test sources of truth |
| `reclassify` | Reclassify and reorganize tasks |

**Review agents:** review-consistency, review-dry, review-layering, review-python-practices, review-testing.

---

### QA BDD (`qa-bdd`) - v0.2.0

Quality assurance tools for pytest-bdd projects and Claude Code plugin skills.

| Component | Count | Status |
|-----------|-------|--------|
| Skills | 4 | Production ready |

**Skills:**

| Skill | Purpose |
|-------|---------|
| `skill-qa-audit` | Read-only audit of plugin skills against official documentation |
| `skill-perfection` | Audit and fix skills in a single pass with optional Python preflight |
| `inspect-steps` | Context-aware BDD step assertion inspection |
| `step-development` | BDD step development workflows with AST-based anti-pattern detection |

---

### Neograph Development (`neograph-dev`) - v0.1.0

Development toolkit for the [neograph](https://neograph.pro) declarative LLM graph compiler.

| Component | Count | Status |
|-----------|-------|--------|
| Skills | 5 | Production ready |

**Skills:**

| Skill | Purpose |
|-------|---------|
| `neograph-dev-codebase-nav` | Import map, layer discipline, deferred import budget, module ownership |
| `neograph-dev-bug-fix` | TDD bug fix workflow with mutation verification and past bug catalog |
| `neograph-dev-test-design` | Test file layout, fake infrastructure, three-surface parity, Hypothesis |
| `neograph-dev-rendering` | Two prompt systems, rendering dispatch hierarchy, BAML parity invariant |
| `neograph-dev-lint` | Lint architecture, extension guide, CLI wiring checklist, template resolver |

---

### PM Practices (`pm-practices`) - v0.1.0

Project-management skills for requirements coverage, Jira ticket quality, refinement and creation. Project agnostic: site, project and field ids come from your private config. See [plugins/pm-practices/README.md](plugins/pm-practices/README.md) for setup.

| Component | Count | Status |
|-----------|-------|--------|
| Skills | 4 | Production ready |

**Skills:**

| Skill | Purpose |
|-------|---------|
| `requirements-coverage-audit` | Do document milestones and Jira plans cover every agreed requirement? Read-only |
| `jira-ticket-quality-audit` | Score open tickets on a nine-dimension rubric. Read-only |
| `jira-ticket-refinement` | Draft and apply approved descriptions, acceptance criteria, points and fields |
| `jira-ticket-creation` | Turn a brief into approved new tickets, including breakdowns, checked against the rubric |

---

## Team Auto-Install

Add to your project's `.claude/settings.json`:

```json
{
  "extraKnownMarketplaces": {
    "agentic-toolkit": {
      "source": {
        "source": "github",
        "repo": "postindustria-tech/agentic-toolkit"
      }
    }
  },
  "enabledPlugins": {
    "langgraph-dev@agentic-toolkit": true,
    "dev-practices@agentic-toolkit": true,
    "qa-bdd@agentic-toolkit": true,
    "neograph-dev@agentic-toolkit": true,
    "pm-practices@agentic-toolkit": true
  }
}
```

## Future Plugins

Planned additions:
- **`dspy-dev`** - DSPy patterns and optimization
- **`agent-sdk-dev`** - Anthropic Agent SDK toolkit

## License

MIT - see [LICENSE](LICENSE)

## Links

- Repository: https://github.com/postindustria-tech/agentic-toolkit
- Issues: https://github.com/postindustria-tech/agentic-toolkit/issues
