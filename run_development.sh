#!/bin/bash
export DJANGO_SETTINGS_MODULE="stagecraft.settings.development"

python manage.py runserver 0.0.0.0:8080
