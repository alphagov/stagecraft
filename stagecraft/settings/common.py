"""
Django settings for stagecraft project.

For more information on this file, see
https://docs.djangoproject.com/en/1.6/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/1.6/ref/settings/
"""

import os
import sys
from os.path import abspath, dirname, join as pjoin

try:
    from urllib.parse import urlparse  # Python 3
except ImportError:
    from urlparse import urlparse  # Python 2

BASE_DIR = abspath(pjoin(dirname(__file__), '..', '..'))

sys.path.append(pjoin(BASE_DIR, 'apps'))
sys.path.append(pjoin(BASE_DIR, 'libs'))

import djcelery

djcelery.setup_loader()

# Defined here for safety, they should also be defined in each environment.
DEBUG = False
TEMPLATE_DEBUG = False

ALLOWED_HOSTS = []

USE_X_FORWARDED_HOST = True
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

STATSD_HOST = 'localhost'
STATSD_PORT = 8125
STATSD_PREFIX = 'pp.apps.stagecraft'
STATSD_MAXUDPSIZE = 512
STATSD_CLIENT = 'django_statsd.clients.normal'


def load_databases_from_environment():
    # eg postgres://user3123:pass123@database.foo.com:6212/db982398
    DATABASE_URL = urlparse(os.environ['DATABASE_URL'])
    return {
        'default': {
            'ENGINE': 'django.db.backends.postgresql_psycopg2',
            'NAME': DATABASE_URL.path[1:],
            'USER': DATABASE_URL.username,
            'PASSWORD': DATABASE_URL.password,
            'HOST': DATABASE_URL.hostname,
            'PORT': DATABASE_URL.port,
        }
    }


# Application definition

INSTALLED_APPS = (
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    'djcelery',
    'reversion',

    'stagecraft.apps.collectors',
    'stagecraft.apps.datasets',
    'stagecraft.apps.dashboards',
    'stagecraft.apps.organisation',
    'stagecraft.apps.transforms',
    'stagecraft.apps.users',
)

MIDDLEWARE_CLASSES = (
    'dogslow.WatchdogMiddleware',
    'django_statsd.middleware.GraphiteRequestTimingMiddleware',
    'stagecraft.libs.request_logger.middleware.RequestLoggerMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',

    'reversion.middleware.RevisionMiddleware',
)

STATSD_PATCHES = (
    'django_statsd.patches.db',
)
ROOT_URLCONF = 'stagecraft.urls'

WSGI_APPLICATION = 'stagecraft.wsgi.application'

# Internationalization
# https://docs.djangoproject.com/en/1.6/topics/i18n/

LANGUAGE_CODE = 'en-gb'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_L10N = True

USE_TZ = True

TEST_RUNNER = 'django_nose.NoseTestSuiteRunner'

NOSE_ARGS = ['-s', '--exclude-dir=stagecraft/settings']

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/1.6/howto/static-files/

STATIC_URL = '/static/'
STATIC_ROOT = abspath(pjoin(BASE_DIR, 'assets'))

DOGSLOW_LOG_TO_FILE = False
DOGSLOW_TIMER = 1
DOGSLOW_LOGGER = 'stagecraft.apps'
DOGSLOW_LOG_LEVEL = 'INFO'

#: Only add pickle to this list if your broker is secured
#: from unwanted access (see userguide/security.html)
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'

CELERY_RESULT_BACKEND = 'djcelery.backends.database.DatabaseBackend'
CELERYBEAT_SCHEDULER = 'djcelery.schedulers.DatabaseScheduler'

ROLES = [
    {
        "role": "collector",
        "permissions": {
            "DataSet": ["get"],
            "Provider": ["get", "post", "put", "delete"],
            "DataSource": ["get", "post", "put", "delete"],
            "CollectorType": ["get", "post", "put", "delete"],
            "Collector": ["get", "post", "put", "delete"]
        }
    },
    {
        "role": "collector-view",
        "permissions": {
            "CollectorType": ["get"],
            "Collector": ["get"]
        }
    },
    {
        "role": "dashboard",
        "permissions": {
            "Dashboard": ["get", "post", "put", "delete"],
            "Module": ["get", "post", "put", "delete"],
            "ModuleType": ["get", "post", "put", "delete"],
        },
    },
    {
        "role": "dashboard-editor",
        "permissions": {
            "Dashboard": ["get", "post", "put"],
            "Module": ["get", "post", "put"],
            "ModuleType": ["get"],
            "DataGroup": ["get", "post"],
            "DataSet": ["get", "post"],
            "Node": ["get"],
            "NodeType": ["get"],
            "Transform": ["get", "post"],
            "TransformType": ["get"],
        },
    },
    {
        "role": "admin",
        "permissions": {
            "Dashboard": ["get", "post", "put", "delete"],
            "Module": ["get", "post", "put", "delete"],
            "ModuleType": ["get", "post", "put", "delete"],
            "DataGroup": ["get", "post", "put", "delete"],
            "DataSet": ["get", "post", "put", "delete"],
            "Node": ["get", "post", "put", "delete"],
            "NodeType": ["get", "post", "put", "delete"],
            "Transform": ["get", "post", "put", "delete"],
            "TransformType": ["get", "post", "put", "delete"],
            "User": ["get", "post", "put", "delete"],
            "Provider": ["get", "post", "put", "delete"],
            "DataSource": ["get", "post", "put", "delete"],
            "CollectorType": ["get", "post", "put", "delete"],
            "Collector": ["get", "post", "put", "delete"],
        },
    },
    {
        "role": "omniscient",
        "permissions": {
        },
    },
    {
        "role": "signin",
        "permissions": {
            "DataGroup": ["get", "post", "put", "delete"],
            "DataSet": ["get", "post", "put", "delete"],
        },
    },
    {
        "role": "organisation",
        "permissions": {
            "Node": ["get", "post", "put", "delete"],
            "NodeType": ["get", "post", "put", "delete"],
        },
    },
    {
        "role": "transforms",
        "permissions": {
            "Transform": ["get", "post", "put", "delete"],
            "TransformType": ["get", "post", "put", "delete"],
        },
    },
    {
        "role": "user",
        "permissions": {
            "User": ["get", "post", "put", "delete"],
        },
    },
    {
        "role": "anon",
        "permissions": {
            "Dashboard": ["get"],
            "Module": ["get"],
            "ModuleType": ["get"],
            "Node": ["get"],
            "NodeType": ["get"],
            "Transform": ["get"],
            "TransformType": ["get"],
        },
    },
]
