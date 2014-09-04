from __future__ import unicode_literals

import uuid
import logging
logger = logging.getLogger(__name__)


def extract_bearer_token(request):
    auth_header = request.META.get('HTTP_AUTHORIZATION', None)
    if auth_header is None:
        logger.debug("No authorization header in request".format(auth_header))
        return None

    return get_valid_token(auth_header)


def get_valid_token(auth_header):
    """
    >>> get_valid_token(u'Bearer some-token') == 'some-token'
    True
    >>> get_valid_token('Bearer ') is None
    True
    >>> get_valid_token('Something Else') is None
    True
    """
    prefix = 'Bearer '
    if not auth_header.startswith(prefix):
        logger.info("Auth header doesn't contain a bearer token: {}".format(
            auth_header))
        return None

    token = auth_header[len(prefix):]
    logger.debug("Got token: '{}'".format(token))
    return token if len(token) else None


def is_uuid(s):
    try:
        uuid.UUID(s)
        return True
    except ValueError:
        return False
