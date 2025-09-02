#!/usr/bin/env bash

set -euo pipefail
# Enable xtrace if requested
[[ "${TGFP_DEBUG_MIGRATIONS:-0}" == "1" ]] && set -x

# Wait for DB
python - <<'PY'
import os, time, psycopg
url = os.environ["DATABASE_URL"].replace("+psycopg", "")
for _ in range(60):
    try:
        with psycopg.connect(url, connect_timeout=3) as _conn:
            break
    except Exception:
        time.sleep(1)
else:
    raise SystemExit("DB not reachable")
PY


# Run migrations (safe to call every start)
# Use an explicit Alembic config path relative to the app dir
export ALEMBIC_CONFIG="${ALEMBIC_CONFIG:-/app/alembic.ini}"

# (Optional) show current revision before/after when TGFP_DEBUG_MIGRATIONS=1
if [[ "${TGFP_DEBUG_MIGRATIONS:-0}" == "1" ]]; then
  echo "→ Using ALEMBIC_CONFIG=$ALEMBIC_CONFIG"
  echo "→ Alembic 'current' BEFORE upgrade:"
  uv run alembic -c "$ALEMBIC_CONFIG" current || true
fi

uv run alembic -c "$ALEMBIC_CONFIG" upgrade head

if [[ "${TGFP_DEBUG_MIGRATIONS:-0}" == "1" ]]; then
  echo "→ Alembic 'current' AFTER upgrade:"
  uv run alembic -c "$ALEMBIC_CONFIG" current || true
fi

# Launch app
exec uv run uvicorn main:app --host 0.0.0.0 --port 8000 --proxy-headers