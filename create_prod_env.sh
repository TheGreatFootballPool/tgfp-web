#!/usr/bin/env bash
cd "$(dirname "$0")" || exit
APP_ENV=production op inject -f -i op.env -o app/.env
echo "ENVIRONMENT=production" >> app/.env