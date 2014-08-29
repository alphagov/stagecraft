import json

from django.utils.cache import patch_response_headers
from functools import wraps


def long_cache(a_view):
    @wraps(a_view)
    def _wrapped_view(request, *args, **kwargs):
        response = a_view(request, *args, **kwargs)
        patch_response_headers(response, 86400 * 365)
        return response
    return _wrapped_view


def to_json(what):
    return json.dumps(what, indent=1)
