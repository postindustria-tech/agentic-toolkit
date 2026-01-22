#!/bin/bash
# Example: Session Completion with Beads Integration
# This script demonstrates session completion with beads issue tracking

set -e  # Exit on error

echo "=== Session Completion with Beads ==="
echo

# Step 1: Check incomplete work
echo "Step 1: Check incomplete work"
echo "In-progress tasks:"
bd list --status=in_progress

read -p "Any tasks to handle? (y/n): " handle_tasks

if [ "$handle_tasks" = "y" ]; then
    echo
    echo "Options:"
    echo "  1. Close completed tasks"
    echo "  2. Update task status"
    echo "  3. Skip for now"
    read -p "Choose (1-3): " task_option

    case $task_option in
        1)
            read -p "Enter task IDs to close (space-separated): " task_ids
            bd close $task_ids
            echo "✅ Closed tasks: $task_ids"
            ;;
        2)
            read -p "Enter task ID to update: " task_id
            read -p "Enter new description: " description
            bd update $task_id --description="$description"
            echo "✅ Updated task: $task_id"
            ;;
        3)
            echo "Skipping task handling"
            ;;
    esac
fi
echo

# Step 2: File new issues for remaining work
echo "Step 2: File new issues"
read -p "Any follow-up work to track? (y/n): " create_issues

if [ "$create_issues" = "y" ]; then
    while true; do
        read -p "Issue title (or 'done' to finish): " title
        [ "$title" = "done" ] && break

        read -p "Issue type (feature/bug/task): " type
        read -p "Priority (0-4): " priority

        bd create --title="$title" --type=$type --priority=$priority
        echo "✅ Created issue: $title"
    done
fi
echo

# Step 3: Run quality gates
echo "Step 3: Run quality gates"
read -p "Did you change code? (y/n): " code_changed

if [ "$code_changed" = "y" ]; then
    echo "Running quality gates..."
    make quality
    echo "✅ All quality gates passed!"
else
    echo "Skipping quality gates (no code changes)"
fi
echo

# Step 4: Git + Beads workflow
echo "Step 4: Git + Beads workflow"

# 4a. Check status
echo "Current status:"
git status
echo

# 4b. Stage changes
read -p "Enter files to stage (or '.' for all): " files_to_stage
git add $files_to_stage
echo "✅ Staged: $files_to_stage"
echo

# 4c. Sync beads (commits .beads/issues.jsonl)
echo "Syncing beads..."
bd sync
echo "✅ Beads synced"
echo

# 4d. Commit code changes
read -p "Enter commit message (one line): " commit_msg

git commit -m "$commit_msg

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>"

echo "✅ Committed"
echo

# 4e. Sync beads again (ensure consistency)
echo "Syncing beads again..."
bd sync
echo "✅ Beads synced"
echo

# 4f. Push to remote
echo "Pushing to remote..."
git push
echo "✅ Pushed successfully!"
echo

# Step 5: Verify
echo "Step 5: Verify completion"

# Git status
echo "Git status:"
git status

if git diff-index --quiet HEAD --; then
    echo "✅ Working tree clean"
else
    echo "⚠️  Working tree has uncommitted changes"
fi

if git status | grep -q "Your branch is up to date"; then
    echo "✅ Up to date with remote"
else
    echo "⚠️  Not up to date with remote"
fi
echo

# Beads status
echo "Beads status:"
bd sync --status

echo "In-progress tasks:"
bd list --status=in_progress

echo
echo "=== Session Complete ==="
echo
echo "Summary:"
echo "  - Code committed and pushed"
echo "  - Beads synced with git"
echo "  - Working tree clean"
echo "  - Ready for next session"
