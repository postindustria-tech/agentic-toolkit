# Git Workflows Reference

Advanced git operations for session completion.

---

## Creating Pull Requests

### Using GitHub CLI

```bash
# 1. Check current state
git status
git diff origin/main...HEAD  # All changes in PR

# 2. Ensure branch is up to date
git fetch origin
git rebase origin/main  # If needed

# 3. Push branch
git push -u origin <branch-name>

# 4. Create PR using gh CLI
gh pr create --title "PR title" --body "$(cat <<'EOF'
## Summary
- Change 1
- Change 2

## Test plan
- [ ] Unit tests pass
- [ ] Integration tests pass
- [ ] Manual testing completed

🤖 Generated with Claude Code
EOF
)"
```

### PR Creation Checklist

Before creating PR:
- [ ] All tests pass
- [ ] Verification steps pass (linters, type checkers)
- [ ] Branch is up to date with target branch
- [ ] Commit messages are descriptive
- [ ] Documentation updated (if needed)

---

## Handling Merge Conflicts

### Rebase Conflicts

```bash
# 1. Fetch latest
git fetch origin

# 2. Attempt rebase
git rebase origin/main
# Conflicts occur

# 3. Resolve conflicts
vi <conflicted-file>
# ... resolve conflicts ...

# 4. Mark resolved
git add <conflicted-file>

# 5. Continue rebase
git rebase --continue

# 6. Push (force with lease to preserve others' work)
git push --force-with-lease
```

### Merge Conflicts

```bash
# 1. Fetch latest
git fetch origin

# 2. Attempt merge
git merge origin/main
# Conflicts occur

# 3. Resolve conflicts
vi <conflicted-file>
# ... resolve conflicts ...

# 4. Mark resolved
git add <conflicted-file>

# 5. Complete merge
git commit -m "Merge origin/main"

# 6. Push
git push
```

### Conflict Resolution Tips

**Understand conflict markers**:
```
<<<<<<< HEAD
Your changes
=======
Their changes
>>>>>>> origin/main
```

**Keep your changes**: Delete conflict markers and "their changes"
**Keep their changes**: Delete conflict markers and "your changes"
**Keep both**: Combine changes, delete conflict markers

---

## Troubleshooting Common Issues

### "git push" fails - Updates were rejected

**Problem**: Remote has changes you don't have locally.

**Solution**:
```bash
# Option 1: Rebase (clean history)
git pull --rebase origin main
git push

# Option 2: Merge (preserves both histories)
git pull origin main
git push
```

### "git push" fails - Permission denied

**Problem**: SSH keys or HTTPS credentials not configured.

**Solution**:
```bash
# Check remote URL
git remote -v

# For SSH issues
ssh -T git@github.com  # Test SSH connection

# Switch to HTTPS if needed
git remote set-url origin https://github.com/user/repo.git

# Switch to SSH if needed
git remote set-url origin git@github.com:user/repo.git
```

### Committed to wrong branch

**Problem**: Made commits on main instead of feature branch.

**Solution**:
```bash
# 1. Create feature branch (commits come with it)
git branch feature-branch

# 2. Reset main to match origin
git reset --hard origin/main

# 3. Switch to feature branch
git checkout feature-branch

# 4. Push feature branch
git push -u origin feature-branch
```

### Need to undo last commit

**Commit not pushed yet**:
```bash
# Keep changes staged
git reset --soft HEAD~1

# Keep changes unstaged
git reset HEAD~1

# Discard changes completely
git reset --hard HEAD~1
```

**Commit already pushed**:
```bash
# Revert (creates new commit)
git revert HEAD
git push

# Force reset (dangerous, avoid on shared branches)
git reset --hard HEAD~1
git push --force-with-lease
```

### Accidentally committed sensitive data

**CRITICAL**: Act immediately.

**If not pushed**:
```bash
# Remove file from last commit
git rm --cached <sensitive-file>
git commit --amend --no-edit

# Add to .gitignore
echo "<sensitive-file>" >> .gitignore
git add .gitignore
git commit -m "Add sensitive file to .gitignore"
```

**If already pushed**:
```bash
# 1. Remove from repository
git rm --cached <sensitive-file>
git commit -m "Remove sensitive data"

# 2. Force push (WARNING: coordinate with team)
git push --force

# 3. Rotate compromised credentials immediately

# 4. Consider using git-filter-repo for complete history rewrite
# See: https://github.com/newren/git-filter-repo
```

---

## Advanced Operations

### Interactive Rebase

**Clean up commits before pushing**:
```bash
# Rebase last 3 commits
git rebase -i HEAD~3

# Editor opens with:
# pick abc1234 First commit
# pick def5678 Second commit
# pick ghi9012 Third commit

# Options:
# pick = keep commit as-is
# reword = change commit message
# squash = combine with previous commit
# fixup = combine with previous, discard message
# drop = remove commit
```

### Cherry-Pick Specific Commits

**Apply specific commits to current branch**:
```bash
# Cherry-pick single commit
git cherry-pick abc1234

# Cherry-pick multiple commits
git cherry-pick abc1234 def5678

# Cherry-pick range
git cherry-pick abc1234..def5678
```

### Stash Changes

**Temporarily save uncommitted changes**:
```bash
# Stash all changes
git stash

# Stash with message
git stash save "WIP: feature X"

# List stashes
git stash list

# Apply most recent stash
git stash apply

# Apply and remove stash
git stash pop

# Apply specific stash
git stash apply stash@{2}

# Clear all stashes
git stash clear
```

### Bisect to Find Bugs

**Binary search through commits to find when bug was introduced**:
```bash
# Start bisect
git bisect start

# Mark current commit as bad
git bisect bad

# Mark known good commit
git bisect good abc1234

# Git checks out middle commit, test it
# ... run tests ...

# If test passes
git bisect good

# If test fails
git bisect bad

# Git continues binary search
# ... repeat until found ...

# End bisect
git bisect reset
```

---

## Git Safety Best Practices

### Before Destructive Operations

**Always create backup branch**:
```bash
# Before rebase, force push, or reset
git branch backup-$(date +%Y%m%d-%H%M%S)
```

### Use --force-with-lease Instead of --force

**Safer force push**:
```bash
# BAD: Overwrites remote regardless of changes
git push --force

# GOOD: Fails if remote has changes you don't have
git push --force-with-lease
```

### Verify Before Pushing

```bash
# Review what will be pushed
git log origin/main..HEAD

# Review changes
git diff origin/main...HEAD

# Review commit messages
git log --oneline origin/main..HEAD
```

---

## Git Configuration Tips

### Useful Aliases

```bash
# Add to ~/.gitconfig
[alias]
    st = status
    co = checkout
    br = branch
    ci = commit
    unstage = reset HEAD --
    last = log -1 HEAD
    lg = log --oneline --decorate --graph --all
```

### Recommended Settings

```bash
# Set default branch name
git config --global init.defaultBranch main

# Set pull strategy
git config --global pull.rebase true

# Enable rerere (reuse recorded resolution)
git config --global rerere.enabled true

# Set editor
git config --global core.editor "vim"
```

---

## References

- [Git Documentation](https://git-scm.com/doc)
- [GitHub CLI Documentation](https://cli.github.com/manual/)
- [Atlassian Git Tutorials](https://www.atlassian.com/git/tutorials)
