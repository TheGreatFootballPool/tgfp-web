# Git Hooks

This directory contains git hooks that are shared across the team via the repository.

## Setup

To activate these hooks, run:

```bash
scripts/setup_git_hooks.sh
```

This configures git to use hooks from this directory instead of `.git/hooks/`.

## Available Hooks

### pre-push

**Purpose:** Ensures `config/version.env` is updated before pushing code changes.

**Behavior:**
- Checks if you're pushing any code changes (excluding `config/version.env` itself)
- If code changes are detected, verifies that `config/version.env` was also modified
- Blocks the push if the version wasn't updated
- Allows the push if only documentation or non-code files changed

**Bypass:**
If you need to bypass this check (not recommended), use:
```bash
git push --no-verify
```

**Why this matters:**
- Ensures all deployed code has a proper version number
- Helps with debugging and tracking which version is running in production
- Prevents accidentally deploying code without version tracking

## Adding New Hooks

1. Create a new executable script in this directory (e.g., `pre-commit`)
2. Make it executable: `chmod +x .githooks/your-hook`
3. Commit the hook to the repository
4. Team members will get it automatically after running `scripts/setup_git_hooks.sh`
