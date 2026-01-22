# Session Completion Skill - Quick Reference Index

Fast navigation to all skill components.

---

## Core Skill

**[SKILL.md](SKILL.md)** - Main skill documentation (1,079 words)
- Core Principle: Work NOT complete until git push succeeds
- Quick Checklist (MANDATORY vs CONDITIONAL)
- 6-step workflow (Check → File → Verify → Close → PUSH → Verify)
- CRITICAL RULES
- Git workflow patterns
- Common pitfalls
- Troubleshooting
- Post-session verification

---

## References (Detailed Documentation)

### [references/git-workflows.md](references/git-workflows.md)
Advanced git operations and troubleshooting (1,097 words)

**Contents**:
- Creating Pull Requests
  - Using GitHub CLI
  - PR creation checklist
- Handling Merge Conflicts
  - Rebase conflicts
  - Merge conflicts
  - Conflict resolution tips
- Troubleshooting Common Issues
  - Updates rejected
  - Permission denied
  - Committed to wrong branch
  - Undo last commit
  - Accidentally committed sensitive data
- Advanced Operations
  - Interactive rebase
  - Cherry-pick
  - Stash changes
  - Bisect to find bugs
- Git Safety Best Practices
- Git Configuration Tips

### [references/issue-tracking-integration.md](references/issue-tracking-integration.md)
Integration patterns for multiple issue tracking systems (1,278 words)

**Contents**:
- Beads Integration
  - Configuration
  - Session completion workflow
  - Commands reference
- GitHub Issues Integration
  - Configuration
  - Session completion workflow
  - Commands reference
- Jira Integration
  - Configuration
  - Session completion workflow
  - Commands reference
- Linear Integration
  - Configuration
  - Session completion workflow
  - Commands reference
- Integration Patterns
  - Auto-close issues from commits
  - Commit message format
- Branch Naming Conventions
- Automation Scripts

### [references/verification-patterns.md](references/verification-patterns.md)
Language-specific verification patterns (1,207 words)

**Contents**:
- Python Projects
  - Standard verification (ruff, mypy, pytest)
  - Auto-fix issues
  - Configuration files
  - Common violations
- JavaScript/TypeScript Projects
  - Standard verification (ESLint, TypeScript, Jest)
  - Auto-fix issues
  - Configuration files
- Rust Projects
  - Standard verification (cargo fmt, clippy, test)
  - Auto-fix issues
  - Configuration files
  - Common issues
- Go Projects
  - Standard verification (gofmt, golangci-lint, test)
  - Auto-fix issues
  - Configuration files
  - Common issues
- Ruby Projects
  - Standard verification (RuboCop, RSpec)
  - Auto-fix issues
  - Configuration files
- Java Projects
  - Standard verification (Checkstyle, Maven/Gradle)
  - Auto-fix issues
  - Configuration files
- CI/CD Integration
  - GitHub Actions examples
- Pre-commit Hooks

---

## Examples (Executable Scripts)

### [examples/basic-session-end.sh](examples/basic-session-end.sh)
Standard session completion workflow (executable)

**Demonstrates**:
- Check current status
- Run verification steps
- Stage changes
- Commit changes
- Push to remote
- Verify completion

**Usage**:
```bash
./examples/basic-session-end.sh
```

### [examples/with-beads.sh](examples/with-beads.sh)
Session completion with Beads integration (executable)

**Demonstrates**:
- Check incomplete work (beads)
- File new issues (beads)
- Run quality gates
- Git + Beads workflow
- Verify completion (git + beads)

**Usage**:
```bash
./examples/with-beads.sh
```

### [examples/with-github-issues.sh](examples/with-github-issues.sh)
Session completion with GitHub Issues integration (executable)

**Demonstrates**:
- Check incomplete work (GitHub)
- Create new issues (GitHub)
- Run quality gates
- Git workflow with issue auto-close
- Verify completion (git + GitHub)

**Usage**:
```bash
./examples/with-github-issues.sh
```

---

## Documentation

### [README.md](README.md)
Skill overview and quick start (492 words)

**Contents**:
- Overview
- Structure
- When to use this skill
- Quick start
- Key features
- Examples
- Critical rules
- References
- Version history

### [EXTRACTION_SUMMARY.md](EXTRACTION_SUMMARY.md)
Detailed extraction documentation (1,315 words)

**Contents**:
- What was extracted
- File structure created
- Key transformations (generalization, parameterization, separation)
- What was kept vs generalized
- Skill frontmatter
- Quality checks
- Usage examples
- Integration with other skills
- Future enhancements
- Comparison before/after
- Verification
- Success criteria
- Design decisions
- Lessons learned

### [COMPARISON.md](COMPARISON.md)
Before/after visual comparison (detailed)

**Contents**:
- Before: Project-specific workflow
- After: Universal reusable skill
- Side-by-side comparison
  - Trigger phrases
  - Issue tracking
  - Verification steps
  - Git workflow
  - Documentation structure
- Content mapping
- Word count comparison
- Usability comparison
- Quality metrics
- Migration path
- Success criteria

### [INDEX.md](INDEX.md)
This file - Quick reference index

---

## Quick Navigation by Use Case

### "I need to end a session"
→ Start with [SKILL.md](SKILL.md)

### "I'm using Beads for issue tracking"
→ [references/issue-tracking-integration.md#beads-integration](references/issue-tracking-integration.md)

### "I'm using GitHub Issues"
→ [references/issue-tracking-integration.md#github-issues-integration](references/issue-tracking-integration.md)

### "I'm using Jira"
→ [references/issue-tracking-integration.md#jira-integration](references/issue-tracking-integration.md)

### "I have a Python project"
→ [references/verification-patterns.md#python-projects](references/verification-patterns.md)

### "I have a JavaScript/TypeScript project"
→ [references/verification-patterns.md#javascripttypescript-projects](references/verification-patterns.md)

### "I have a Rust project"
→ [references/verification-patterns.md#rust-projects](references/verification-patterns.md)

### "I need help with pull requests"
→ [references/git-workflows.md#creating-pull-requests](references/git-workflows.md)

### "I have merge conflicts"
→ [references/git-workflows.md#handling-merge-conflicts](references/git-workflows.md)

### "I want to see an example"
→ [examples/basic-session-end.sh](examples/basic-session-end.sh)

### "How do I run the examples?"
→ Make executable: `chmod +x examples/*.sh`
→ Run: `./examples/basic-session-end.sh`

---

## File Statistics

| File | Type | Words | Purpose |
|------|------|-------|---------|
| SKILL.md | Core | 1,079 | Main workflow |
| references/git-workflows.md | Reference | 1,097 | Git operations |
| references/issue-tracking-integration.md | Reference | 1,278 | Issue trackers |
| references/verification-patterns.md | Reference | 1,207 | Verification |
| README.md | Documentation | 492 | Overview |
| EXTRACTION_SUMMARY.md | Documentation | 1,315 | Extraction details |
| COMPARISON.md | Documentation | TBD | Before/after |
| INDEX.md | Documentation | TBD | This file |
| examples/basic-session-end.sh | Example | - | Basic workflow |
| examples/with-beads.sh | Example | - | Beads integration |
| examples/with-github-issues.sh | Example | - | GitHub integration |

**Total**: 10 files, 6,468+ words

---

## Version

**Current Version**: 0.1.0 (2025-01-20)

**Next Steps**:
- Test skill invocation
- Gather user feedback
- Consider additional issue trackers (Asana, Trello, Azure DevOps)
- Consider additional languages (C/C++, PHP, Swift)

---

## Quick Links

- [Main Skill](SKILL.md)
- [Git Workflows](references/git-workflows.md)
- [Issue Tracking](references/issue-tracking-integration.md)
- [Verification Patterns](references/verification-patterns.md)
- [Basic Example](examples/basic-session-end.sh)
- [Beads Example](examples/with-beads.sh)
- [GitHub Example](examples/with-github-issues.sh)
