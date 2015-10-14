from __future__ import absolute_import
import os
from celery import Celery

os.environ.setdefault(
    "DJANGO_SETTINGS_MODULE", "stagecraft.settings.production")

from django.conf import settings

celery_app = Celery('collectors')

celery_app.config_from_object('django.conf:settings')
celery_app.autodiscover_tasks(lambda: settings.INSTALLED_APPS)
