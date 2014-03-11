from logging import getLogger
logger = getLogger(__name__)


def extract_bearer_token(request):
    auth_header = request.META.get('Authorization')
    return get_valid_token(auth_header)


def get_valid_token(auth_header):
    """
    >>> get_valid_token(u'Bearer some-token')
    u'some-token'
    >>> get_valid_token('Bearer ') is None
    True
    >>> get_valid_token('Something Else') is None
    True
    """
    prefix = 'Bearer '
    if auth_header is None or not auth_header.startswith(prefix):
        return None
    token = auth_header[len(prefix):]
    return token if len(token) else None
