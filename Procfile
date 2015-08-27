web: ./venv/bin/gunicorn stagecraft.wsgi:application --bind 127.0.0.1:3103 --workers 4
worker: DJANGO_SETTINGS_MODULE=stagecraft.settings.production ./venv/bin/python manage.py celery worker -E -l debug
beat: DJANGO_SETTINGS_MODULE=stagecraft.settings.production ./venv/bin/python manage.py celery beat -l debug
celerycam: DJANGO_SETTINGS_MODULE=stagecraft.settings.production ./venv/bin/python manage.py celerycam
