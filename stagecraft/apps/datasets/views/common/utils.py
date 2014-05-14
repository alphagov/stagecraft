import json
from stagecraft.libs.validation.validation import extract_bearer_token
import logging
from django.http import (HttpResponseForbidden)
from django.utils.cache import patch_response_headers
from functools import wraps

logger = logging.getLogger(__name__)


def _authorized(given_token, correct_token):
    if given_token == correct_token:
        return True

    logger.warn("Bad token. Got: '{}'".format(given_token))
    return False


def token_required(correct_token):
    def decorator(a_view):
        def _wrapped_view(request, *args, **kwargs):
            if _authorized(extract_bearer_token(request), correct_token):
                return a_view(request, *args, **kwargs)
            error = {'status': 'error',
                     'message': 'Forbidden: invalid or no token given.'}
            return HttpResponseForbidden(to_json(error))
        return _wrapped_view
    return decorator


def long_cache(a_view):
    @wraps(a_view)
    def _wrapped_view(request, *args, **kwargs):
        response = a_view(request, *args, **kwargs)
        patch_response_headers(response, 86400 * 365)
        return response
    return _wrapped_view


def to_json(what):
    return json.dumps(what, indent=1)
