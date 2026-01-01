#!/bin/bash

# Setup git hooks from .githooks directory
# This script configures git to use hooks stored in the repository

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
REPO_ROOT="$(dirname "$SCRIPT_DIR")"

echo "Setting up git hooks..."

# Configure git to use .githooks directory
cd "$REPO_ROOT" || exit
git config core.hooksPath .githooks

echo "✓ Git hooks configured successfully!"
echo ""
echo "Active hooks:"
ls -1 .githooks/
echo ""
echo "To disable hooks temporarily, use: git push --no-verify"
