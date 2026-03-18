#!/bin/bash
# Example: Session Completion with GitHub Issues Integration
# This script demonstrates session completion with GitHub Issues

set -e  # Exit on error

echo "=== Session Completion with GitHub Issues ==="
echo

# Step 1: Check incomplete work
echo "Step 1: Check incomplete work"
echo "Your in-progress issues:"
gh issue list --assignee @me --state open --label "in-progress"

read -p "Any issues to handle? (y/n): " handle_issues

if [ "$handle_issues" = "y" ]; then
    echo
    echo "Options:"
    echo "  1. Remove 'in-progress' label from completed work"
    echo "  2. Add comment to issue"
    echo "  3. Skip for now"
    read -p "Choose (1-3): " issue_option

    case $issue_option in
        1)
            read -p "Enter issue number: " issue_num
            gh issue edit $issue_num --remove-label "in-progress"
            echo "✅ Removed in-progress label from #$issue_num"
            ;;
        2)
            read -p "Enter issue number: " issue_num
            read -p "Enter comment: " comment
            gh issue comment $issue_num --body "$comment"
            echo "✅ Added comment to #$issue_num"
            ;;
        3)
            echo "Skipping issue handling"
            ;;
    esac
fi
echo

# Step 2: Create new issues for remaining work
echo "Step 2: Create new issues"
read -p "Any follow-up work to track? (y/n): " create_issues

if [ "$create_issues" = "y" ]; then
    while true; do
        read -p "Issue title (or 'done' to finish): " title
        [ "$title" = "done" ] && break

        read -p "Issue body: " body
        read -p "Labels (comma-separated, e.g., 'enhancement,help wanted'): " labels

        gh issue create --title "$title" --body "$body" --label "$labels"
        echo "✅ Created issue: $title"
    done
fi
echo

# Step 3: Run quality gates
echo "Step 3: Run quality gates"
read -p "Did you change code? (y/n): " code_changed

if [ "$code_changed" = "y" ]; then
    echo "Running quality gates..."

    # Example: Node.js project
    if [ -f "package.json" ]; then
        npm run lint
        npm run type-check
        npm test
    fi

    # Example: Python project
    if [ -f "pyproject.toml" ]; then
        ruff check .
        mypy src/
        pytest tests/ -v -m "not slow"
    fi

    echo "✅ All quality gates passed!"
else
    echo "Skipping quality gates (no code changes)"
fi
echo

# Step 4: Git workflow with GitHub Issues integration
echo "Step 4: Git workflow"

# 4a. Check status
echo "Current status:"
git status
echo

# 4b. Stage changes
read -p "Enter files to stage (or '.' for all): " files_to_stage
git add $files_to_stage
echo "✅ Staged: $files_to_stage"
echo

# 4c. Commit with optional issue auto-close
echo "Commit options:"
echo "  - Include 'Closes #123' to auto-close issue on push"
echo "  - Include 'Fixes #123' to auto-close issue on push"
echo "  - Include 'Resolves #123' to auto-close issue on push"
echo

read -p "Enter commit message (one line): " commit_msg
read -p "Close any issues? (enter issue numbers like '123 456', or leave empty): " close_issues

if [ -n "$close_issues" ]; then
    # Build closes line
    closes_line=""
    for issue in $close_issues; do
        closes_line="${closes_line}Closes #${issue}"$'\n'
    done

    git commit -m "$commit_msg

$closes_line
Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>"
else
    git commit -m "$commit_msg

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>"
fi

echo "✅ Committed"
echo

# 4d. Push to remote (auto-closes issues)
echo "Pushing to remote..."
git push
echo "✅ Pushed successfully!"

if [ -n "$close_issues" ]; then
    echo "✅ Issues auto-closed: $close_issues"
fi
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

# GitHub Issues status
echo "Your open issues:"
gh issue list --assignee @me --state open

echo
echo "=== Session Complete ==="
echo
echo "Summary:"
echo "  - Code committed and pushed"
echo "  - GitHub Issues updated"
echo "  - Working tree clean"
echo "  - Ready for next session"
