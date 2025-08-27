#!/usr/bin/env bash
set -euo pipefail

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
# Prefer an explicit Alembic config path since our CWD is /app (only the app dir is mounted)
export ALEMBIC_CONFIG="${ALEMBIC_CONFIG:-/alembic.ini}"
alembic -c "$ALEMBIC_CONFIG" upgrade head

# Launch app
exec uv run uvicorn main:app --host 0.0.0.0 --port 8000 --proxy-headers