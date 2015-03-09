"""
WSGI config for stagecraft project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/1.6/howto/deployment/wsgi/
"""

import os
os.environ.setdefault("DJANGO_SETTINGS_MODULE",
                      "stagecraft.settings.production")

from django.core.wsgi import get_wsgi_application
import gc
import logging
import sys

logger = logging.getLogger('gunicorn.error')


class writer(object):

    def write(self, data):
        logger.info(data)

sys.stderr = writer()
gc.set_debug(gc.DEBUG_STATS)
application = get_wsgi_application()
