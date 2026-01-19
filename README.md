# Agentic Toolkit

Claude Code plugin marketplace for building agentic systems with LangGraph, DSPy, and AI workflows.

## Installation

```bash
/plugin marketplace add postindustria-tech/agentic-toolkit
/plugin install langgraph-dev@agentic-toolkit
```

## Available Plugins

### LangGraph Development (`langgraph-dev`) - v0.1.0

Tutorial-grounded patterns and best practices for LangGraph development.

**Status**: Skills are tested and ready to use. Commands and agent are work in progress.

**What's Included:**
- **22 Skills** (Tested) - RAG, multi-agent, memory, streaming, testing, state management, tool calling, and more
- **5 Commands** (WIP) - Generators for workflows, state schemas, tests, agents, deployments
- **1 Agent** (WIP) - Workflow validator

**Skills Cover:**
- LangGraph fundamentals (state, graphs, routing, streaming)
- Agent patterns (ReAct, multi-agent, tools)
- RAG systems (basic, corrective, document processing)
- Memory and context management
- Testing and deployment
- Error handling and optimization

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
    "langgraph-dev@agentic-toolkit": true
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
