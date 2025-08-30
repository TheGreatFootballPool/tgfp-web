#!/usr/bin/env bash
set -euo pipefail

# Move to repo root (one level up from scripts/)
cd "$(dirname "$0")/.."

# Load env vars from config/.env.dev
if [ -f "config/.env.dev" ]; then
  # shellcheck disable=SC2046
  export $(grep -vE '^\s*#' config/.env.dev | xargs -I{} echo {})
else
  echo "❌ config/.env.dev not found"
  exit 1
fi

# Run alembic upgrade
alembic upgrade head