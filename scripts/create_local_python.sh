#!/usr/bin/env bash
# scripts/setup_dev_env.sh

set -e

PROJECT_ROOT="$(cd -- "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
VENV_DIR="$PROJECT_ROOT/.venv"
REQS="$PROJECT_ROOT/config/requirements.txt"

python3 -m venv "$VENV_DIR"
uv pip install -r "$REQS" --python "$VENV_DIR/bin/python"

echo "✅ Virtual env ready at $VENV_DIR"
echo "→ Add $VENV_DIR/bin/python as interpreter in PyCharm"