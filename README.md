# Agentic Toolkit

Claude Code plugin marketplace for building agentic systems with LangGraph, DSPy, and AI workflows.

## Installation

```bash
# Add the marketplace
/plugin marketplace add postindustria-tech/agentic-toolkit

# Install specific plugins
/plugin install langgraph-dev@agentic-toolkit
/plugin install pi-dev@agentic-toolkit

# Or install both
/plugin install langgraph-dev@agentic-toolkit pi-dev@agentic-toolkit
```

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

### Post Industria Development (`pi-dev`) - v0.1.0

Productivity and infrastructure development workflows for quality-driven development.

**Status**: Production ready - both skills fully tested and documented.

**What's Included:**
- **2 Skills** (Production Ready) - Test-driven development and session completion workflows
- **Beads Integration** - Seamlessly integrates with beads task management workflow

**Skills:**
- **TDD Workflow** (`/pi-dev-tdd-workflow`) - Complete test-driven development cycle with sacred rule enforcement (tests define requirements, never adjust tests to match code). Includes language-specific patterns for Python, JavaScript, Go, TypeScript, and more
- **Session Completion** (`/pi-dev-session-completion`) - End-of-session checklist ensuring no work is lost. Covers verification steps, git workflows, issue tracking integration, and proper push-to-remote procedures

**Language Support:**
- Python, JavaScript/TypeScript, Rust, Go, Ruby, Java
- Verification patterns and quality gates for each language
- CI/CD integration examples (GitHub Actions, pre-commit hooks)

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
    "pi-dev@agentic-toolkit": true
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
