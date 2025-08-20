ENV="development"
cd "$(dirname "$0")" || exit
cd ..
APP_ENV=${ENV} op inject -f -i config/op.env -o config/.env.dev
echo "ENVIRONMENT=${ENV}" >> config/.env.dev

source config/version.env
NEW_VERSION="${MAJOR}.${MINOR}.${PATCH}"
echo "APP_VERSION=${NEW_VERSION}" >> config/.env.dev
