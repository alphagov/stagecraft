# preview/staging/production all use the same config with the exception of the
# environment-specific secrets

#
# See https://docs.djangoproject.com/en/1.6/howto/deployment/checklist/
#

import os

from os.path import abspath, dirname, join as pjoin

from .common import *
from .environment_specific_settings import *

DEBUG = False

TEMPLATE_DEBUG = False

CSRF_COOKIE_SECURE = True  # avoid transmitting the CSRF cookie over HTTP

SESSION_COOKIE_SECURE = True  # avoid transmitting the session cookie over HTTP

USE_DEVELOPMENT_USERS = False

ALLOWED_HOSTS = [
    '*',
]

APP_HOSTNAME = 'stagecraft{0}'.format(ENV_HOSTNAME)

APP_ROOT = 'https://{0}'.format(APP_HOSTNAME)
GOVUK_ROOT = os.getenv('GOVUK_WEBSITE_ROOT')

BASE_DIR = abspath(pjoin(dirname(__file__), '..', '..'))
STATIC_URL = '{0}/stagecraft/'.format(os.getenv('GOVUK_ASSET_HOST'))
STATIC_ROOT = abspath(pjoin(BASE_DIR, 'public', 'stagecraft'))

BACKDROP_PUBLIC_URL = 'https://www{0}'.format(PUBLIC_HOSTNAME)
BACKDROP_READ_URL = 'https://backdrop-read.{0}'.format(
    os.getenv('GOVUK_APP_DOMAIN'))
BACKDROP_WRITE_URL = 'https://backdrop-write.{0}'.format(
    os.getenv('GOVUK_APP_DOMAIN'))

SIGNON_URL = 'https://signon.{0}'.format(os.getenv('GOVUK_APP_DOMAIN'))

VARNISH_CACHES = [
    ('http://frontend-app-1', 7999),
    ('http://frontend-app-2', 7999),
]

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
    'filters': {
        'additional_fields': {
            '()': 'stagecraft.libs.request_logger.middleware.AdditionalFieldsFilter',  # noqa
        }
    },
    'handlers': {
        'null': {
            'level': 'INFO',
            'class': 'django.utils.log.NullHandler',
        },
        'logfile': {
            'level': 'DEBUG',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': BASE_DIR + "/log/stagecraft.log",
            'maxBytes': 4 * 1024 * 1024,
            'backupCount': 2,
            'formatter': 'standard',
            'filters': ['additional_fields'],
        },
        'json_log': {
            'level': 'DEBUG',
            'class': 'logging.FileHandler',
            'filename': BASE_DIR + "/log/production.json.log",
            'formatter': 'logstash_json',
        },
        'json_audit_log': {
            'level': 'DEBUG',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': BASE_DIR + "/log/audit/stagecraft.json.log",
            'maxBytes': 4 * 1024 * 1024,
            'backupCount': 2,
            'formatter': 'logstash_json',
            'filters': ['additional_fields'],
        },
    },
    'loggers': {
        '': {
            'level': 'WARN',
            'handlers': ['logfile', 'json_log'],
        },
        'django.request': {
            'handlers': ['logfile', 'json_log'],
            'level': 'INFO',
            'propagate': True,  # also handle in parent handler
        },

        'stagecraft.apps': {
            'handlers': ['logfile', 'json_log'],
            'level': 'INFO',
            'propagate': True,
        },
        'stagecraft.libs': {
            'handlers': ['logfile', 'json_log'],
            'level': 'INFO',
            'propagate': True,
        },
        'stagecraft.audit': {
            'handlers': ['json_audit_log'],
            'level': 'DEBUG',
            'propagate': True,
        },
    },
}
