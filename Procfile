web: ./venv/bin/gunicorn stagecraft.wsgi:application --bind 127.0.0.1:3103 --workers 4
worker: ./venv/bin/python manage.py celery --settings=stagecraft.settings.production celery worker -E -l debug
beat: ./venv/bin/python manage.py celery --settings=stagecraft.settings.production -l debug
celerycam: ./venv/bin/python manage.py celerycam --settings=stagecraft.settings.production
