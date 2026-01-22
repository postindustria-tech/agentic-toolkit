# Session Completion Skill

Reusable skill for properly completing and committing work sessions.

## Overview

**Core Principle**: Work is NOT complete until `git push` succeeds.

This skill provides a universal workflow for:
- Running verification steps (linters, type checkers, tests)
- Managing issue tracking systems (Beads, GitHub Issues, Jira, Linear)
- Committing and pushing changes safely
- Verifying session completion

## Structure

```
session-completion/
├── SKILL.md                    # Main skill (1,500-2,000 words)
├── README.md                   # This file
├── references/                 # Detailed references
│   ├── git-workflows.md        # Pull requests, merge conflicts, troubleshooting
│   ├── issue-tracking-integration.md  # Beads, GitHub, Jira, Linear integration
│   └── verification-patterns.md       # Language-specific verification (Python, JS, Rust, Go, etc.)
└── examples/                   # Working examples
    ├── basic-session-end.sh    # Standard session completion
    ├── with-beads.sh           # With Beads integration
    └── with-github-issues.sh   # With GitHub Issues integration
```

## When to Use This Skill

Use this skill when the user asks to:
- "end session"
- "complete work"
- "landing the plane"
- "finish session"
- "git push workflow"
- "session checklist"
- "push to remote"

Or when they need to properly complete and commit work.

## Quick Start

### Basic Usage

1. Read `SKILL.md` for the core 6-step workflow
2. Follow mandatory steps (verification, push, verify)
3. Use conditional steps as needed (issue tracking)

### With Issue Tracking

1. Check `references/issue-tracking-integration.md` for your system
2. Follow integration-specific workflow
3. Sync issue tracking with git commits

### Language-Specific Verification

1. Check `references/verification-patterns.md` for your language
2. Run language-specific quality gates
3. Auto-fix safe issues before committing

## Key Features

### Universal Git Workflow

Core git operations work for all projects:
- Stage changes
- Commit with descriptive messages
- Push to remote
- Verify working tree clean

### Parameterized Integration

Issue tracking integration is parameterized:
- Beads (git-backed)
- GitHub Issues
- Jira
- Linear

Choose your system, follow integration pattern.

### Language-Agnostic Verification

Verification patterns for multiple languages:
- Python (ruff, mypy, pytest)
- JavaScript/TypeScript (ESLint, TypeScript, Jest)
- Rust (cargo fmt, clippy, test)
- Go (gofmt, golangci-lint, go test)
- Ruby (RuboCop, RSpec)
- Java (Checkstyle, Maven/Gradle)

## Examples

All examples are executable bash scripts:

```bash
# Make executable
chmod +x examples/*.sh

# Run basic workflow
./examples/basic-session-end.sh

# Run with Beads
./examples/with-beads.sh

# Run with GitHub Issues
./examples/with-github-issues.sh
```

## Critical Rules

1. **ALWAYS** complete work with successful `git push` - work is NOT complete otherwise
2. **ALWAYS** push yourself - never say "ready to push when you are"
3. **IF push fails**: Resolve conflicts and retry until it succeeds
4. **NEVER** stop before pushing - that leaves work stranded locally
5. **ALWAYS** verify working tree clean after push

## References

- **SKILL.md**: Main skill documentation
- **references/git-workflows.md**: Advanced git operations
- **references/issue-tracking-integration.md**: Issue tracking patterns
- **references/verification-patterns.md**: Language-specific verification
- **examples/**: Working examples

## Version History

- **0.1.0** (2025-01-20): Initial extraction from session-completion.md
  - Universal git workflow
  - Parameterized issue tracking integration
  - Multi-language verification patterns
  - Working examples for common scenarios
