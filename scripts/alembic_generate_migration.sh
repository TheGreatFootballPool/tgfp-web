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

# Migration message (default: "sync models")
MSG="${1:-sync models}"

# Locate Alembic versions directory
guess_versions_dir() {
  if [ -d "alembic/versions" ]; then
    echo "alembic/versions"
  elif [ -d "migrations/versions" ]; then
    echo "migrations/versions"
  else
    # Try to parse script_location from alembic.ini and append /versions
    if [ -f "alembic.ini" ]; then
      local loc
      loc="$(awk -F= '/^[[:space:]]*script_location[[:space:]]*=/ {gsub(/[[:space:]]/,"",$2); print $2}' alembic.ini || true)"
      if [ -n "$loc" ] && [ -d "$loc/versions" ]; then
        echo "$loc/versions"
        return
      fi
    fi
    echo "❌ Could not find Alembic versions directory. Ensure alembic.ini script_location has a /versions subfolder." >&2
    exit 1
  fi
}

VERSIONS_DIR="$(guess_versions_dir)"

# Create a unique temporary rev id for the probe
PROBE_REV="probe_$(date +%s%N)"

# Generate a probe revision inside the real versions dir (so Alembic is happy)
alembic revision --autogenerate --rev-id "$PROBE_REV" -m "[probe] $MSG" >/dev/null

# Find the created probe file (format: <rev>_<slug>.py)
PROBE_FILE="$(ls -1 "${VERSIONS_DIR}/${PROBE_REV}_"*.py 2>/dev/null | head -n 1 || true)"
if [[ -z "${PROBE_FILE:-}" ]]; then
  echo "ℹ️  Probe did not produce a file (nothing to do)."
  exit 0
fi

# Heuristic: If file contains no Alembic ops, it's effectively a no-op autogenerate
if ! grep -q 'op\.' "$PROBE_FILE"; then
  rm -f "$PROBE_FILE"
  echo "✅ No schema changes detected. Skipping migration."
  exit 0
fi

# Changes detected: remove probe and create a real migration with your message
rm -f "$PROBE_FILE"
echo "🛠  Changes detected. Creating migration..."
alembic revision --autogenerate -m "$MSG"
echo "✅ Migration created."