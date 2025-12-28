#!/usr/bin/env bash
set -euo pipefail

# --- Config ---------------------------------------------------------------
PG16_BIN="${PG16_BIN:-/opt/homebrew/opt/postgresql@16/bin}"  # adjust if needed
JOBS="${JOBS:-4}"

# URIs
PROD_URI="postgresql+psycopg://tgfp:tgfp@tgfp-prod:5432/tgfp"
DEV_URI="postgresql+psycopg://tgfp:tgfp@localhost:6432/tgfp"

# Strip "+psycopg" (CLI tools expect plain postgresql:)
PROD_PG="${PROD_URI/postgresql+psycopg:/postgresql:}"
DEV_PG="${DEV_URI/postgresql+psycopg:/postgresql:}"

die(){ echo "ERROR: $*" >&2; exit 1; }
need_bin() { command -v "$1" >/dev/null 2>&1 || die "Missing: $1"; }

# --- Checks ---------------------------------------------------------------
need_bin "$PG16_BIN/pg_dump"
need_bin "$PG16_BIN/pg_restore"
need_bin "$PG16_BIN/psql"

# --- Temp dump dir (auto-clean) ------------------------------------------
DUMP_DIR="$(mktemp -d /tmp/tgfp_dump.XXXXXX)"
cleanup() { rm -rf "$DUMP_DIR"; }
trap cleanup EXIT

echo "Using:"
"$PG16_BIN/pg_dump" --version
"$PG16_BIN/pg_restore" --version
"$PG16_BIN/psql" --version
echo "Temp dump dir: $DUMP_DIR"

# --- Recreate DEV database (avoid locks) ----------------------------------
echo "Recreating DEV database to avoid locks..."
DEV_SUPER="$(echo "$DEV_PG" | sed -E 's#/tgfp$#/postgres#')"  # connect to 'postgres'
"$PG16_BIN/psql" "$DEV_SUPER" -v ON_ERROR_STOP=1 <<'SQL'
ALTER DATABASE tgfp WITH ALLOW_CONNECTIONS false;
SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE datname = 'tgfp';
DROP DATABASE IF EXISTS tgfp WITH (FORCE);
CREATE DATABASE tgfp OWNER tgfp;
SQL

# --- Dump from PROD (directory format, parallel) --------------------------
echo "Dumping from PROD (tgfp-prod) -> $DUMP_DIR ..."
"$PG16_BIN/pg_dump" -Fd \
  --no-owner --no-privileges \
  --jobs="$JOBS" \
  --file="$DUMP_DIR" \
  "$PROD_PG"

# --- Restore to DEV (parallel) --------------------------------------------
echo "Restoring into DEV (localhost:6432) with $JOBS jobs..."
"$PG16_BIN/pg_restore" \
  --clean --if-exists \
  --no-owner --no-privileges \
  --jobs="$JOBS" \
  --verbose \
  --dbname="$DEV_PG" \
  "$DUMP_DIR"

echo "✅ Sync complete: PROD (tgfp-prod) → DEV (localhost:6432)"
