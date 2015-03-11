# preview/staging/production all use the same config with the exception of the
# environment-specific secrets

#
# See https://docs.djangoproject.com/en/1.6/howto/deployment/checklist/
#

from .common import *
from .environment_specific_settings import *

DEBUG = False

TEMPLATE_DEBUG = False

CSRF_COOKIE_SECURE = True  # avoid transmitting the CSRF cookie over HTTP

SESSION_COOKIE_SECURE = True  # avoid transmitting the session cookie over HTTP

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
            'filename': BASE_DIR + "/log/stagecraft.log.json",
            'formatter': 'logstash_json',
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
    },
}
