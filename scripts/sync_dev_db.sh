#!/usr/bin/env bash
set -euo pipefail

###
# Mandatory ENV variables that must exist in the .env file
# PRODUCTION_MONGO_URI
# Make sure your developement docker instance is running locally

cd "$(dirname "$0")" || exit
# move to the project root
cd ..

# ---------- Load .env first in cwd ----------

set -a
. config/.env.dev
set +a

COMPOSE_FILE="compose.dev.yml"
DB_NAME="tgfp"
MONGO_IMAGE="mongo:6"
DEV_SERVICE="mongo"

# ---------- Stream dump → restore (drops dev collections first) ----------
docker run --rm -i "${MONGO_IMAGE}" bash -lc \
  "mongodump --uri='${PRODUCTION_MONGO_URI}' --archive --gzip" \
| docker compose -f "${COMPOSE_FILE}" exec -T "${DEV_SERVICE}" \
  mongorestore --archive --gzip --drop --nsFrom="${DB_NAME}.*" --nsTo="${DB_NAME}.*"

