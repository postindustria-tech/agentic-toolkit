# Release Notes

## v0.3.0 - Plugin-QA Addition (2026-01-25)

### 🎉 New Plugin: plugin-qa

Added **plugin-qa** plugin for quality assurance of Claude Code plugins and skills:

- **Skill Perfection** (`plugin-qa-skill-perfection`) - Audit and fix plugin skills in a single pass. Verifies content against official documentation, fixes issues immediately as they're found, and produces concise verification reports. Includes optional Python syntax preflight script for Python-heavy skills.

- **QA Audit** (`plugin-qa-skill-qa-audit`) - Comprehensive QA verification of plugin skills. Systematically verifies every line of instruction, code example, and claim against official documentation. Produces detailed audit reports with severity ratings, verification statistics, and quality metrics.

**Features:**
- Audit + fix in single pass (skill-perfection)
- Comprehensive verification reporting (skill-qa-audit)
- Official documentation verification with source citations
- Severity-based issue categorization (Critical/High/Medium/Low)
- Code completeness, syntax, and API accuracy validation
- Documentation link verification
- Python syntax preflight script (optional, advisory)
- Quality metrics and scoring

**Use Cases:**
- Validate skills before publishing
- Check for deprecated APIs and outdated documentation
- Verify code examples are complete and executable
- Ensure documentation accuracy
- Systematic quality review with detailed reporting

### 📦 Installation

```bash
# Install plugin-qa
/plugin install plugin-qa@agentic-toolkit

# Or install all three plugins
/plugin install langgraph-dev@agentic-toolkit dev-practices@agentic-toolkit plugin-qa@agentic-toolkit
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
    "dev-practices@agentic-toolkit": true,
    "plugin-qa@agentic-toolkit": true
  }
}
```

### 📊 Plugin Status

**Plugin-QA (v0.1.0):**
- 2 skills - Production ready
- Complementary to Anthropic's plugin-dev
- Focus on quality assurance vs creation

---

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

**Note:** This plugin was initially released as `pi-dev` but was renamed to `dev-practices` for clarity and broader applicability. If you installed `pi-dev`, see the **Upgrade Instructions** section below.

### 🔄 Upgrade Instructions: pi-dev → dev-practices

If you previously installed `pi-dev`, upgrade to `dev-practices`:

```bash
# 1. Refresh marketplace to see updated plugins
/plugin marketplace add postindustria-tech/agentic-toolkit

# 2. Uninstall old plugin
/plugin uninstall pi-dev@agentic-toolkit

# 3. Install new plugin
/plugin install dev-practices@agentic-toolkit
```

**For team auto-install:** Update `.claude/settings.json`:
```json
{
  "enabledPlugins": {
    "dev-practices@agentic-toolkit": true
  }
}
```

**See detailed upgrade guide:** [UPGRADE.md](UPGRADE.md)

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
- Enhanced metadata (homepage, repository, keywords, license)
- Updated marketplace.json with dev-practices entry
- Skills are auto-discovered from `skills/` directory structure

**Documentation:**
- Updated README.md with dev-practices section
- Added installation instructions for both plugins
- Updated skill counts and descriptions

**Quality:**
- Removed development artifacts from dev-practices
- Consistent naming convention across all skills
- Professional metadata for marketplace distribution

### 🐛 Bug Fix (v0.2.1)

**Fixed plugin.json validation error:**
- Removed invalid `skills` arrays from plugin.json files
- Skills are auto-discovered by Claude Code from directory structure
- This fixes installation errors: "skills: Invalid input"

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
