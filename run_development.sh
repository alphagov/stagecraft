#!/bin/bash
export DJANGO_SETTINGS_MODULE="stagecraft.settings.development"

if [ -d "venv" ]; then
    source venv/bin/activate
fi

python manage.py runserver 0.0.0.0:8080

