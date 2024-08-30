ENV="local_dev"
cd "$(dirname "$0")" || exit
cd ..
APP_ENV=${ENV} op inject -f -i config/op.env -o app/.env