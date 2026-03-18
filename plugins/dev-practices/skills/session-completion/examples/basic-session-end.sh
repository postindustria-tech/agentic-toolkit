#!/bin/bash
# Example: Basic Session Completion Workflow
# This script demonstrates the standard session completion process

set -e  # Exit on error

echo "=== Session Completion Workflow ==="
echo

# Step 1: Check current status
echo "Step 1: Check current status"
git status
echo

# Step 2: Run verification if code changed
echo "Step 2: Run verification steps"
read -p "Did you change code? (y/n): " code_changed

if [ "$code_changed" = "y" ]; then
    echo "Running quality gates..."

    # Example: Python project
    if [ -f "pyproject.toml" ]; then
        echo "  - Running ruff..."
        ruff check .
        echo "  - Running mypy..."
        mypy src/
        echo "  - Running pytest..."
        pytest tests/ -v -m "not slow and not e2e"
    fi

    # Example: JavaScript project
    if [ -f "package.json" ]; then
        echo "  - Running ESLint..."
        npm run lint
        echo "  - Running TypeScript..."
        npm run type-check
        echo "  - Running tests..."
        npm test
    fi

    # Example: Rust project
    if [ -f "Cargo.toml" ]; then
        echo "  - Running rustfmt..."
        cargo fmt --check
        echo "  - Running clippy..."
        cargo clippy
        echo "  - Running tests..."
        cargo test
    fi

    echo "✅ All verification steps passed!"
else
    echo "Skipping verification (no code changes)"
fi
echo

# Step 3: Stage changes
echo "Step 3: Stage changes"
read -p "Enter files to stage (or '.' for all): " files_to_stage
git add $files_to_stage
echo "✅ Staged: $files_to_stage"
echo

# Step 4: Commit changes
echo "Step 4: Commit changes"
read -p "Enter commit message (one line): " commit_msg

git commit -m "$commit_msg

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>"

echo "✅ Committed"
echo

# Step 5: Push to remote
echo "Step 5: Push to remote"
read -p "Ready to push? (y/n): " ready_push

if [ "$ready_push" = "y" ]; then
    echo "Pushing to remote..."
    git push
    echo "✅ Pushed successfully!"
else
    echo "⚠️  Push skipped - remember to push manually!"
    exit 1
fi
echo

# Step 6: Verify
echo "Step 6: Verify completion"
git status

# Check if working tree is clean
if git diff-index --quiet HEAD --; then
    echo "✅ Working tree clean"
else
    echo "⚠️  Working tree has uncommitted changes"
fi

# Check if up to date with remote
if git status | grep -q "Your branch is up to date"; then
    echo "✅ Up to date with remote"
else
    echo "⚠️  Not up to date with remote"
fi

echo
echo "=== Session Complete ==="
