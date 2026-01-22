# Issue Tracking Integration Patterns

Integration patterns for different issue tracking systems with session completion workflow.

---

## Beads Integration

**Beads**: Git-backed issue tracking that persists across sessions. Managed by the beads plugin.

### Setup

See beads plugin quickstart:
```
/beads:quickstart        # Interactive setup guide
```

### Session Completion Workflow

```bash
# 1. Check incomplete work
/beads:list              # Filter by status=in_progress

# 2. File new issues
/beads:create            # Interactive issue creation

# 3. Close completed tasks
/beads:close <id>        # Close each verified task

# 4. Stage code changes
git add <files>

# 5. Sync beads (commits .beads/issues.jsonl)
/beads:sync

# 6. Commit code changes
git commit -m "Descriptive message

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>"

# 7. Sync beads again (ensure consistency)
/beads:sync

# 8. Push to remote
git push

# 9. Verify
git status               # "up to date with origin/main"
/beads:sync              # Should be no-op (no pending changes)
```

### Beads Commands Reference

See beads plugin for full command reference:
```
/beads:workflow          # Full workflow guide and all commands
```

**Common commands**:
- `/beads:ready` - Show available tasks (no blockers)
- `/beads:show <id>` - View task details
- `/beads:create` - Interactive task creation
- `/beads:update <id>` - Update task (status, description, etc.)
- `/beads:close <id>` - Close task with summary
- `/beads:sync` - Sync with git remote
- `/beads:dep` - Manage dependencies
- `/beads:epic` - Manage epics

---

## GitHub Issues Integration

**GitHub Issues**: Native GitHub issue tracking.

### Configuration

```bash
# Install GitHub CLI
brew install gh  # macOS
# or: https://cli.github.com/

# Authenticate
gh auth login
```

### Session Completion Workflow

```bash
# 1. Check in-progress issues
gh issue list --assignee @me --state open

# 2. Create new issues
gh issue create --title "Follow-up task" --body "Description" --label "enhancement"

# 3. Close completed issues (from commit messages)
git add <files>
git commit -m "Fix authentication bug

Closes #123

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>"

# 4. Push to remote (auto-closes issues)
git push

# 5. Verify
gh issue list --assignee @me --state open
```

### GitHub CLI Commands Reference

```bash
# List issues
gh issue list                         # All issues
gh issue list --assignee @me          # Your issues
gh issue list --label bug             # By label
gh issue list --state open            # Open only

# Create issue
gh issue create --title "..." --body "..." --label "bug"
gh issue create --title "..." --assignee @me

# Update issue
gh issue edit <number> --add-label "in-progress"
gh issue edit <number> --add-assignee @me

# Close issue
gh issue close <number>
gh issue close <number> --comment "Fixed in #456"

# Auto-close from commits
# Use: "Closes #123" or "Fixes #123" in commit message
```

---

## Jira Integration

**Jira**: Enterprise issue tracking.

### Configuration

```bash
# Install Jira CLI
brew tap ankitpokhrel/jira-cli
brew install jira-cli

# Configure
jira init
```

### Session Completion Workflow

```bash
# 1. Check in-progress issues
jira issue list --assignee=$(jira me) --status "In Progress"

# 2. Create new issues
jira issue create --type Task --summary "Follow-up task" --priority Medium

# 3. Transition completed issues
jira issue move PROJECT-123 "Done"

# 4. Commit with Jira issue reference
git add <files>
git commit -m "PROJECT-123: Fix authentication bug

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>"

# 5. Push to remote
git push

# 6. Verify
jira issue list --assignee=$(jira me) --status "In Progress"
```

### Jira CLI Commands Reference

```bash
# List issues
jira issue list --assignee=$(jira me)
jira issue list --status "In Progress"
jira issue list --project PROJECT

# Create issue
jira issue create --type Task --summary "..." --priority High
jira issue create --type Bug --summary "..." --assignee user@example.com

# Update issue
jira issue move PROJECT-123 "In Progress"
jira issue move PROJECT-123 "Done"
jira issue assign PROJECT-123 user@example.com

# Add comment
jira issue comment PROJECT-123 "Work completed"
```

---

## Linear Integration

**Linear**: Modern issue tracking for development teams.

### Configuration

```bash
# Install Linear CLI
npm install -g @linear/cli

# Authenticate
linear login
```

### Session Completion Workflow

```bash
# 1. Check in-progress issues
linear issue list --assignee @me --state started

# 2. Create new issues
linear issue create --title "Follow-up task" --priority 2

# 3. Update completed issues
linear issue update PROJ-123 --state done

# 4. Commit with Linear reference
git add <files>
git commit -m "PROJ-123: Fix authentication bug

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>"

# 5. Push to remote
git push

# 6. Verify
linear issue list --assignee @me --state started
```

### Linear CLI Commands Reference

```bash
# List issues
linear issue list --assignee @me      # Your issues
linear issue list --state started     # In progress
linear issue list --state backlog     # Backlog

# Create issue
linear issue create --title "..." --priority 1
linear issue create --title "..." --assignee @me

# Update issue
linear issue update PROJ-123 --state started
linear issue update PROJ-123 --state done
linear issue update PROJ-123 --assignee @user

# Add comment
linear issue comment PROJ-123 "Work completed"
```

---

## Integration Patterns

### Auto-Close Issues from Commits

**GitHub syntax** (works with GitHub Issues):
```
Closes #123
Fixes #456
Resolves #789
```

**Jira syntax** (with Jira GitHub integration):
```
PROJECT-123 #done
PROJECT-456 #comment "Fixed in this commit"
```

**Linear syntax** (with Linear Git integration):
```
PROJ-123
Fixes PROJ-456
```

### Commit Message Format

**Standard format**:
```
<type>(<scope>): <subject>

<body>

<footer>
```

**Examples**:
```bash
# With GitHub issue
git commit -m "fix(auth): Fix password reset flow

- Add validation for email format
- Improve error messages

Closes #123

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>"

# With Jira issue
git commit -m "PROJECT-123: Implement user dashboard

- Add user profile component
- Add settings page

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>"

# With Linear issue
git commit -m "PROJ-123: Add dark mode toggle

- Add theme context
- Update components for dark mode

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>"
```

---

## Branch Naming Conventions

### With Issue Numbers

**GitHub/GitLab**:
```bash
feature/123-add-user-dashboard
bugfix/456-fix-login-error
hotfix/789-security-patch
```

**Jira**:
```bash
feature/PROJECT-123-add-user-dashboard
bugfix/PROJECT-456-fix-login-error
hotfix/PROJECT-789-security-patch
```

**Linear**:
```bash
feature/proj-123-add-user-dashboard
bugfix/proj-456-fix-login-error
hotfix/proj-789-security-patch
```

### Create Branch from Issue

```bash
# GitHub
gh issue develop 123 --checkout

# Jira
jira issue move PROJECT-123 "In Progress"
git checkout -b feature/PROJECT-123-$(jira issue view PROJECT-123 --plain | grep Summary)

# Linear
linear issue update PROJ-123 --state started
git checkout -b feature/proj-123-add-dashboard
```

---

## Automation Scripts

### Sync All Issues Before Commit

```bash
#!/bin/bash
# .git/hooks/pre-commit

# Beads
if command -v bd &> /dev/null; then
    bd sync
fi

# GitHub (update issue status)
if command -v gh &> /dev/null; then
    # Auto-update based on branch name
    BRANCH=$(git branch --show-current)
    ISSUE_NUM=$(echo "$BRANCH" | grep -oE '[0-9]+' | head -1)
    if [ -n "$ISSUE_NUM" ]; then
        gh issue edit "$ISSUE_NUM" --add-label "in-progress"
    fi
fi

# Jira
if command -v jira &> /dev/null; then
    BRANCH=$(git branch --show-current)
    ISSUE_KEY=$(echo "$BRANCH" | grep -oE '[A-Z]+-[0-9]+' | head -1)
    if [ -n "$ISSUE_KEY" ]; then
        jira issue move "$ISSUE_KEY" "In Progress"
    fi
fi
```

### Auto-Close Issues on Push

```bash
#!/bin/bash
# .git/hooks/post-commit

# Extract issue numbers from commit message
COMMIT_MSG=$(git log -1 --pretty=%B)

# GitHub
if echo "$COMMIT_MSG" | grep -qE "(Closes|Fixes|Resolves) #[0-9]+"; then
    ISSUE_NUMS=$(echo "$COMMIT_MSG" | grep -oE "#[0-9]+" | grep -oE "[0-9]+")
    for NUM in $ISSUE_NUMS; do
        gh issue close "$NUM"
    done
fi

# Jira
if echo "$COMMIT_MSG" | grep -qE "[A-Z]+-[0-9]+"; then
    ISSUE_KEYS=$(echo "$COMMIT_MSG" | grep -oE "[A-Z]+-[0-9]+")
    for KEY in $ISSUE_KEYS; do
        jira issue move "$KEY" "Done"
    done
fi
```

---

## References

- [Beads Documentation](https://github.com/beadslabs/beads)
- [GitHub CLI Documentation](https://cli.github.com/manual/)
- [Jira CLI Documentation](https://github.com/ankitpokhrel/jira-cli)
- [Linear CLI Documentation](https://developers.linear.app/docs/cli)
