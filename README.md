# Agentic Toolkit

Claude Code plugin marketplace for building agentic systems with LangGraph, DSPy, and AI workflows.

## Installation

```bash
# Add the marketplace
/plugin marketplace add postindustria-tech/agentic-toolkit

# Install specific plugins
/plugin install langgraph-dev@agentic-toolkit
/plugin install dev-practices@agentic-toolkit
/plugin install plugin-qa@agentic-toolkit

# Or install all
/plugin install langgraph-dev@agentic-toolkit dev-practices@agentic-toolkit plugin-qa@agentic-toolkit
```

**Upgrading from pi-dev?** See [UPGRADE.md](UPGRADE.md) for instructions.

## Available Plugins

### LangGraph Development (`langgraph-dev`) - v0.1.0

Tutorial-grounded patterns and best practices for LangGraph development.

**Status**: Skills are tested and ready to use. Commands and agent are work in progress.

**What's Included:**
- **21 Skills** (Tested) - RAG, multi-agent, memory, streaming, testing, state management, tool calling, and more
- **5 Commands** (WIP) - Generators for workflows, state schemas, tests, agents, deployments
- **1 Agent** (WIP) - Workflow validator

**Skills Cover:**
- LangGraph fundamentals (state, graphs, routing, streaming)
- Agent patterns (ReAct, multi-agent, tools)
- RAG systems (basic, corrective, document processing)
- Memory and context management
- Testing and deployment
- Error handling and optimization

### Development Practices (`dev-practices`) - v0.1.0

Development practices and workflows for quality-driven software engineering.

**Status**: Production ready - both skills fully tested and documented.

**What's Included:**
- **2 Skills** (Production Ready) - Test-driven development and session completion workflows
- **Beads Integration** - Seamlessly integrates with beads task management workflow

**Skills:**
- **TDD Workflow** (`/dev-practices-tdd-workflow`) - Complete test-driven development cycle with sacred rule enforcement (tests define requirements, never adjust tests to match code). Includes language-specific patterns for Python, JavaScript, Go, TypeScript, and more
- **Session Completion** (`/dev-practices-session-completion`) - End-of-session checklist ensuring no work is lost. Covers verification steps, git workflows, issue tracking integration, and proper push-to-remote procedures

**Language Support:**
- Python, JavaScript/TypeScript, Rust, Go, Ruby, Java
- Verification patterns and quality gates for each language
- CI/CD integration examples (GitHub Actions, pre-commit hooks)

### Plugin QA (`plugin-qa`) - v0.1.0

Quality assurance tools for validating and perfecting Claude Code plugin skills.

**Status**: Production ready - both skills tested and ready to use.

**What's Included:**
- **2 Skills** (Production Ready) - Skill auditing and perfection workflows

**Skills:**
- **Skill Perfection** (`/plugin-qa-skill-perfection`) - Audit and fix plugin skills in a single pass. Verifies skill content against official documentation, fixes issues immediately, and produces verification reports. Includes optional Python syntax preflight script.
- **QA Audit** (`/plugin-qa-skill-qa-audit`) - Comprehensive QA verification of plugin skills. Verifies every line of instruction, code example, and claim against official documentation. Produces structured audit reports with severity ratings and quality metrics.

**Use Cases:**
- Validate skill correctness before publishing
- Check for deprecated APIs and outdated documentation
- Verify code examples are complete and executable
- Ensure documentation links are current and accessible
- Systematic quality review with detailed reporting

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
    "plugin-qa@agentic-toolkit": true
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
