# preview/staging/production all use the same config with the exception of the
# environment-specific secrets

#
# See https://docs.djangoproject.com/en/1.6/howto/deployment/checklist/
#

from .common import *

PAAS = load_paas_settings()

DEBUG = bool(os.getenv('DEBUG'))  # use as integer 1|0
SECRET_KEY = os.getenv('SECRET_KEY')
ENV_HOSTNAME = os.getenv('ENV_HOSTNAME')
PUBLIC_HOSTNAME = os.getenv('PUBLIC_HOSTNAME')
BROKER_URL = PAAS.get('REDIS_URL') or os.getenv('REDIS_URL')

CSRF_COOKIE_SECURE = True  # avoid transmitting the CSRF cookie over HTTP

SESSION_COOKIE_SECURE = True  # avoid transmitting the session cookie over HTTP

USE_DEVELOPMENT_USERS = False

FERNET_USE_HKDF = bool(int(os.getenv('FERNET_USE_HKDF') or 0))  # set as 0 or 1
FERNET_KEYS = [
    os.getenv('FERNET_KEY')
]

ALLOWED_HOSTS = [
    '*',
]

APP_HOSTNAME = 'stagecraft-{0}'.format(ENV_HOSTNAME)

APP_ROOT = 'https://{0}'.format(APP_HOSTNAME)
GOVUK_WEBSITE_ROOT = os.getenv('GOVUK_WEBSITE_ROOT')

BASE_DIR = abspath(pjoin(dirname(__file__), '..', '..'))
STATIC_URL = os.getenv('STATIC_URL')
STATIC_ROOT = abspath(pjoin(BASE_DIR, 'assets/'))

BACKDROP_READ_URL = "https://performance-platform-backdrop-read-staging.cloudapps.digital"
BACKDROP_WRITE_URL = "https://performance-platform-backdrop-write-staging.cloudapps.digital"

STAGECRAFT_COLLECTION_ENDPOINT_TOKEN = os.getenv('STAGECRAFT_COLLECTION_ENDPOINT_TOKEN')
TRANSFORMED_DATA_SET_TOKEN = os.getenv('TRANSFORMED_DATA_SET_TOKEN')
MIGRATION_SIGNON_TOKEN = os.getenv('MIGRATION_SIGNON_TOKEN')

SIGNON_URL = 'https://signon.{0}'.format(os.getenv('GOVUK_APP_DOMAIN'))
SIGNON_CLIENT_ID = os.getenv('SIGNON_CLIENT_ID')

VARNISH_CACHES = [
    ('http://frontend-app-1', 7999),
    ('http://frontend-app-2', 7999),
]

DATABASE_URL = urlparse(os.environ.get('DATABASE_URL') or PAAS.get('DATABASE_URL') or '')
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'NAME': DATABASE_URL.path[1:],
        'USER': DATABASE_URL.username,
        'PASSWORD': DATABASE_URL.password,
        'HOST': DATABASE_URL.hostname,
        'PORT': DATABASE_URL.port,
    }
}

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
            'class': 'logging.NullHandler',
        },
        'logfile': {
            'level': 'WARNING',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': BASE_DIR + "/log/stagecraft.log",
            'maxBytes': 4 * 1024 * 1024,
            'backupCount': 2,
            'formatter': 'standard',
            'filters': ['additional_fields'],
        },
        'json_log': {
            'level': 'WARNING',
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
            'level': 'DEBUG',
            'handlers': ['logfile', 'json_log'],
        },
        'django.request': {
            'handlers': ['logfile', 'json_log'],
            'level': 'DEBUG',
            'propagate': True,  # also handle in parent handler
        },

        'stagecraft.apps': {
            'handlers': ['logfile', 'json_log'],
            'level': 'DEBUG',
            'propagate': True,
        },
        'stagecraft.libs': {
            'handlers': ['logfile', 'json_log'],
            'level': 'DEBUG',
            'propagate': True,
        },
        'stagecraft.audit': {
            'handlers': ['json_audit_log'],
            'level': 'DEBUG',
            'propagate': True,
        },
    },
}
