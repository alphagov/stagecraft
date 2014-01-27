#
# See https://docs.djangoproject.com/en/1.6/howto/deployment/checklist/
#

from common import *

import os

DEBUG = False
TEMPLATE_DEBUG = False

try:
    SECRET_KEY = os.environ['SECRET_KEY']
except KeyError:
    with open('/etc/stagecraft/secret_key.txt') as f:
        SECRET_KEY = os.read().strip()

ALLOWED_HOSTS = []  # TODO: set this.

CSRF_COOKIE_SECURE = True  # avoid transmitting the CSRF cookie over HTTP

SESSION_COOKIE_SECURE = True  # avoid transmitting the session cookie over HTTP
