# Release Notes

## v0.2.0 - Plugin Namespacing & Dev-Practices Addition (2026-01-22)

### 🎉 New Plugin: dev-practices

Added **dev-practices** plugin for development practices and workflows:

- **TDD Workflow** (`dev-practices-tdd-workflow`) - Complete test-driven development cycle with sacred rule enforcement (tests define requirements, never adjust tests to match code). Includes language-specific patterns for Python, JavaScript, Go, TypeScript, Rust, Ruby, and Java.

- **Session Completion** (`dev-practices-session-completion`) - End-of-session checklist ensuring no work is lost. Covers verification steps, git workflows, issue tracking integration, and proper push-to-remote procedures.

**Features:**
- Language-agnostic TDD best practices
- Beads workflow integration
- Comprehensive verification patterns for 6+ languages
- CI/CD integration examples
- Quality gates and pre-commit hooks

### ⚠️ Breaking Changes: Langgraph-Dev

**All 21 langgraph-dev skills renamed with plugin namespace prefix.**

This ensures proper namespacing as the plugin ecosystem grows and prevents naming conflicts between plugins.

#### Migration Guide

**Skill Names Changed:**
```
OLD                          NEW
─────────────────────────────────────────────────────────
basic-rag                 →  langgraph-dev-basic-rag
graph-construction        →  langgraph-dev-graph-construction
human-in-the-loop         →  langgraph-dev-human-in-the-loop
react-agents              →  langgraph-dev-react-agents
... (all 21 skills)
```

**What This Means:**
- ✅ **Skill triggers still work** - Description-based auto-discovery unchanged
  - Still use: "help me build RAG", "create a graph", etc.
  - Skills load automatically based on context

- ⚠️ **Direct skill invocations require new names**
  - Old: `/basic-rag`
  - New: `/langgraph-dev-basic-rag`

**Complete List of Renamed Skills:**
1. `langgraph-dev-basic-rag`
2. `langgraph-dev-conditional-routing`
3. `langgraph-dev-conversation-memory`
4. `langgraph-dev-corrective-rag`
5. `langgraph-dev-deployment-patterns`
6. `langgraph-dev-document-processing`
7. `langgraph-dev-error-recovery`
8. `langgraph-dev-graph-construction`
9. `langgraph-dev-human-in-the-loop`
10. `langgraph-dev-memory-store-and-knowledge`
11. `langgraph-dev-multi-agent-supervisor`
12. `langgraph-dev-parallel-execution`
13. `langgraph-dev-performance-optimization`
14. `langgraph-dev-prompt-engineering`
15. `langgraph-dev-react-agents`
16. `langgraph-dev-state-management`
17. `langgraph-dev-streaming-execution`
18. `langgraph-dev-structured-output`
19. `langgraph-dev-subgraphs-and-composition`
20. `langgraph-dev-testing-agentic-systems`
21. `langgraph-dev-tool-calling`

### 📦 Installation

```bash
# Add the marketplace
/plugin marketplace add postindustria-tech/agentic-toolkit

# Install both plugins
/plugin install langgraph-dev@agentic-toolkit dev-practices@agentic-toolkit
```

### 🔧 Team Auto-Install

Update your project's `.claude/settings.json`:

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
    "dev-practices@agentic-toolkit": true
  }
}
```

### 🛠️ Technical Changes

**Configuration:**
- Added explicit `skills` arrays to both plugin.json files
- Enhanced metadata (homepage, repository, keywords, license)
- Updated marketplace.json with dev-practices entry

**Documentation:**
- Updated README.md with dev-practices section
- Added installation instructions for both plugins
- Updated skill counts and descriptions

**Quality:**
- Removed development artifacts from dev-practices
- Consistent naming convention across all skills
- Professional metadata for marketplace distribution

### 📊 Plugin Status

**Langgraph-Dev (v0.2.0):**
- 21 skills - All production ready
- 5 commands - Work in progress
- 1 agent - Work in progress

**Dev-Practices (v0.1.0):**
- 2 skills - Production ready
- Beads workflow integration
- Multi-language support

### 🎯 Future Plans

- DSPy development plugin (`dspy-dev`)
- Anthropic Agent SDK toolkit (`agent-sdk-dev`)

---

## v0.1.0 - Initial Release (2024)

Initial release of the agentic-toolkit marketplace with langgraph-dev plugin.

**Features:**
- 22 LangGraph skills (later consolidated to 21)
- RAG patterns (basic, corrective, document processing)
- Multi-agent systems
- State management and memory
- Testing and deployment patterns

---

**Repository:** https://github.com/postindustria-tech/agentic-toolkit
**Issues:** https://github.com/postindustria-tech/agentic-toolkit/issues
**License:** MIT
