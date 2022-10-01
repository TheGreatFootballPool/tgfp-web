#!/bin/sh
export FLASK_APP=passenger_wsgi.py
export FLASK_DEBUG=1 
export FLASK_ENV=development
# shellcheck disable=SC2046
# shellcheck disable=SC2086
cd $(dirname $0) || exit
flask run --no-reload
