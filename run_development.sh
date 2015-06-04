#!/bin/bash -e

# Usage: run_development.sh [port]
#
# This will not mess with your virtualenv - you have to manage that yourself.

export DJANGO_SETTINGS_MODULE="stagecraft.settings.development"

python manage.py migrate --noinput

exec python manage.py runserver 0.0.0.0:${1-3204}
