#!/usr/bin/env bash
cd "$(dirname "$0")" || exit
APP_ENV=development op inject -f -i op.env -o app/.env
echo "ENVIRONMENT=development" >> app/.env