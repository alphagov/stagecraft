"""
Django settings for stagecraft project.

For more information on this file, see
https://docs.djangoproject.com/en/1.6/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/1.6/ref/settings/
"""

from .common import *

import os

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/1.6/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = '^10-$qwyu##ivl7f48^mit5e8a-8q#6ceb5i5&zk86)$^(^rmn'

DEBUG = True
TEMPLATE_DEBUG = True

APP_HOSTNAME = 'stagecraft.perfplat.dev'

SIGNON_URL = 'http://signon.dev.gov.uk'
USE_DEVELOPMENT_USERS = True
DEVELOPMENT_USERS = {
    'development-oauth-access-token':
    {
        "email": "some.user@digital.cabinet-office.gov.uk",
        "name": "Some User",
        "organisation_slug": "cabinet-office",
        "permissions": [
            "signin",
            "dataset",
            "user"
        ],
        "uid": "00000000-0000-0000-0000-000000000000"
    }
}

VARNISH_CACHES = [
    ('http://development-1', 7999)
]

ALLOWED_HOSTS = [  # required if DEBUG is False
    'localhost',
    APP_HOSTNAME,
]

# Application definition

INSTALLED_APPS += (
    'django_nose',
)

MIDDLEWARE_CLASSES += (
)

# Database
# https://docs.djangoproject.com/en/1.6/ref/settings/#databases

if os.environ.get('USE_SQLITE', 'false') != 'false':
    print("INFO: Using local SQLite database (USE_SQLITE=true)")
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': os.path.join(BASE_DIR, 'db.sqlite3'),
        }
    }
elif os.environ.get('DATABASE_URL'):
    DATABASES = load_databases_from_environment()
    print(DATABASES)
else:
    print("INFO: Using PostgreSQL database (USE_SQLITE=false)")
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.postgresql_psycopg2',
            'NAME': 'stagecraft',
            'USER': 'stagecraft',
            'PASSWORD': 'securem8',
            'HOST': 'postgresql-primary',  # localhost
            'PORT': '5432',
        }
    }


BACKDROP_URL = 'http://localhost:3039'
STAGECRAFT_COLLECTION_ENDPOINT_TOKEN = 'dev-create-endpoint-token'

LOGGING = {
    'version': 1,
    'disable_existing_loggers': True,
    'formatters': {
        'standard': {
            'format': ("[%(asctime)s] %(levelname)s [%(name)s:%(lineno)s]"
                       " %(message)s"),
            'datefmt': "%d-%b-%y %H:%M:%S"
        },
        'logstash_json': {
            '()': 'logstash_formatter.LogstashFormatter',
            'fmt': '{"extra": {"@tags": ["application", "stagecraft"]}}',
        },
    },
    'handlers': {
        'null': {
            'level': 'DEBUG',
            'class': 'django.utils.log.NullHandler',
        },
        'logfile': {
            'level': 'DEBUG',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': BASE_DIR + "/log/stagecraft.log",
            'maxBytes': 4 * 1024 * 1024,
            'backupCount': 2,
            'formatter': 'standard',
        },
        'database_log': {
            'level': 'DEBUG',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': BASE_DIR + "/log/database_queries.log",
            'maxBytes': 4 * 1024 * 1024,
            'backupCount': 2,
            'formatter': 'standard',
        },
        'json_log': {
            'level': 'DEBUG',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': BASE_DIR + "/log/stagecraft.log.json",
            'maxBytes': 4 * 1024 * 1024,
            'backupCount': 2,
            'formatter': 'logstash_json',
        },
        'console': {
            'level': 'INFO',
            'class': 'logging.StreamHandler',
            'formatter': 'standard'
        },
    },
    'loggers': {
        'django.request': {
            'handlers': ['console', 'logfile', 'json_log'],
            'level': 'INFO',
            'propagate': True,  # also handle in parent handler
        },

        'django.db.backends': {
            'handlers': ['database_log'],
            'level': 'DEBUG',
            'propagate': False,
        },

        'stagecraft.apps': {
            'handlers': ['console', 'logfile', 'json_log'],
            'level': 'DEBUG',
            'propagate': True,
        },
        'stagecraft.libs': {
            'handlers': ['console', 'logfile', 'json_log'],
            'level': 'DEBUG',
            'propagate': True,
        },
    },
}
