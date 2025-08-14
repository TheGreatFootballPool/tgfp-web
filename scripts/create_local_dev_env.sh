ENV="local_dev"
cd "$(dirname "$0")" || exit
cd ..
APP_ENV=${ENV} op inject -f -i config/op.env -o app/.env
echo "ENVIRONMENT=${ENV}" >> app/.env

source config/version.env
NEW_VERSION="${MAJOR}.${MINOR}.${PATCH}"
echo "APP_VERSION=${NEW_VERSION}" >> app/.env.dev
