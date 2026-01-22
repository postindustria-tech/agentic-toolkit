---
name: dev-practices-session-completion
description: This skill should be used when the user asks to "end session", "complete work", "landing the plane", "finish session", "git push workflow", "session checklist", "push to remote", "how do I finish my work", "commit and push workflow", "finish coding session", "save my work", "end my work session", or needs to properly complete and commit work. Provides critical workflow ensuring no work is lost. Integrates with beads plugin for task tracking and git synchronization.
version: 0.1.0
---

# Session Completion Workflow

## Overview

This skill is the final step in the development workflow managed by the beads plugin (`/beads:workflow`). Session completion is typically triggered after completing Step 4 (Verify & Close) in the beads workflow, ensuring all work is properly committed and pushed to remote.

---

## Core Principle

**Work is NOT complete until `git push` succeeds**. This workflow ensures no work is lost between sessions or during conversation compaction.

---

## Quick Checklist

Before ending any work session:

**MANDATORY** (always required):
1. ✅ Run verification steps if code changed
2. ✅ Push to remote repository
3. ✅ Verify working tree is clean and synchronized

**CONDITIONAL** (task-dependent):
1. ✅ Check incomplete work in issue tracking system
2. ✅ File issues for remaining work
3. ✅ Close completed tasks

**CRITICAL**: Never say "ready to push when you are" - YOU must complete the push.

---

## Step-by-Step Workflow

### Step 1: Check Incomplete Work

Review issue tracking system for in-progress tasks.

**For each in-progress task**:
- Can you finish it quickly? → Complete and close it
- Is it blocked? → Update status/description, leave in_progress
- Changed scope? → Close and create new issue for actual work

**Don't leave tasks hanging without clear status**.

---

### Step 2: File Issues for Remaining Work

Create issues for:
- Follow-up tasks discovered during work
- Known limitations or technical debt
- Tasks that need requirements clarification
- Refactoring opportunities identified

**Update project roadmap** if priorities changed.

---

### Step 3: Run Verification Steps

**MANDATORY if code changed**:

Run project-specific verification:
```bash
# Example verification commands
make quality        # Run linters, type checkers, tests
npm test           # JavaScript/TypeScript projects
pytest             # Python projects
cargo test         # Rust projects
```

**If violations found**:
1. Auto-fix safe issues using linters
2. Manually fix remaining violations
3. For complex violations: create issues, then proceed
4. Verify: All checks must pass before commit

**See**: `references/verification-patterns.md` for language-specific examples.

---

### Step 4: Close Completed Tasks

Close all verified tasks in issue tracking system.

**Verification before closing**:
- ✅ Each task's acceptance criteria met (from requirements documentation)
- ✅ Verification steps passed (if code changed)
- ✅ Examples execute correctly (if applicable)
- ✅ Documentation updated

**Don't bulk close** without verifying each task individually.

---

### Step 5: PUSH TO REMOTE (CRITICAL)

**Git workflow** (canonical single source of truth):

```bash
# 1. Check status
git status

# 2. Stage changes
git add <files>

# 3. Sync issue tracking (if integrated with git)
# Example: bd sync, gh issue sync, etc.

# 4. Commit with descriptive message
git commit -m "Descriptive one-line summary

Detailed description of changes:
- Change 1
- Change 2
- Change 3

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>"

# 5. Sync issue tracking again (if needed)

# 6. Push to remote
git push

# 7. Verify success
git status
# Expected: "Your branch is up to date with 'origin/main'"
```

**If push fails**: Resolve conflicts and retry until it succeeds.

**See**: `references/git-workflows.md` for advanced git operations.

---

### Step 6: Verify

**Final checks**:
```bash
git status
# Expected: "working tree clean"
# Expected: "Your branch is up to date with 'origin/main'"
```

**Check issue tracking system**:
- In-progress work is documented OR empty
- No pending changes

**All checks must pass** before ending session.

---

## CRITICAL RULES

**Absolute requirements**:
1. ✅ **ALWAYS** complete work with successful `git push` - work is NOT complete otherwise
2. ✅ **ALWAYS** push yourself - never delegate to user with "ready when you are"
3. ✅ **IF push fails**: Resolve conflicts and retry until it succeeds
4. ✅ **NEVER** stop before pushing - that leaves work stranded locally
5. ✅ **ALWAYS** verify working tree clean after push

---

## Git Workflow Patterns

### Standard Commit Flow

```bash
# Check what changed
git status

# Stage specific files
git add <files>

# Commit with descriptive message
git commit -m "Summary

- Detail 1
- Detail 2

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>"

# Push to remote
git push

# Verify
git status
```

### With Issue Tracking Integration

See `references/issue-tracking-integration.md` for:
- Beads integration (git-backed issue tracking)
- GitHub Issues integration
- Jira integration
- Linear integration

---

## Common Pitfalls

**Requirements & Planning**:
- ❌ Not checking requirements documentation before closing tasks
- ❌ Closing tasks without verifying acceptance criteria

**Workflow**:
- ❌ Working on multiple tasks without documenting which is in progress
- ❌ Bulk closing tasks without individual verification

**Git Operations**:
- ❌ Forgetting to push after final commit
- ❌ Saying "work is done" before `git push` succeeds
- ❌ Not syncing issue tracking system with git commits

**Verification**:
- ❌ Skipping verification steps before commit
- ❌ Committing with failing tests or linter violations
- ❌ Not creating issues for complex violations discovered

---

## Troubleshooting

### Forgot to run verification steps

**If already committed**:
```bash
# Run verification
make quality  # or project-specific command

# If violations found, fix them
# ... fix code ...

# Amend commit
git add <files>
git commit --amend --no-edit

# Force push (if already pushed)
git push --force-with-lease
```

**Better**: Always run verification BEFORE committing.

---

### "git push" fails

**Error: "Updates were rejected"**
```bash
# Remote has changes you don't have locally
git pull --rebase origin main
git push
```

**See**: `references/git-workflows.md` for detailed troubleshooting.

---

### Left task in_progress by mistake

Update task status in issue tracking system:
- If task is actually done: close it
- If task needs more work: update description with context, leave in_progress

---

## Post-Session Verification

**Before ending session, verify**:
- [ ] `git status` → "working tree clean"
- [ ] `git status` → "up to date with origin/main"
- [ ] Issue tracking → in_progress tasks are documented OR empty
- [ ] Verification steps passed (if code changed)
- [ ] All completed tasks closed
- [ ] No uncommitted changes
- [ ] Context documented for next session (if needed)

**If ALL checked**: Session complete ✅

---

## References

- **Git Workflows**: `references/git-workflows.md` - Pull requests, merge conflicts, advanced operations
- **Issue Tracking Integration**: `references/issue-tracking-integration.md` - Integration patterns
- **Verification Patterns**: `references/verification-patterns.md` - Language-specific verification
- **Examples**: `examples/` - Working examples for common scenarios

---

## Examples

### Basic Session End

See `examples/basic-session-end.sh` for complete workflow example.

### With Beads Integration

See `examples/with-beads.sh` for session completion with beads issue tracking.

### With GitHub Issues

See `examples/with-github-issues.sh` for GitHub Issues integration.
