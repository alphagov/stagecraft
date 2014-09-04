import json

from django.utils.cache import patch_response_headers
from functools import wraps
from uuid import UUID


class JsonEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, UUID):
            return '{}'.format(obj)

        if hasattr(obj, 'serialize'):
            return obj.serialize()

        return json.JSONEncoder.default(self, obj)


def long_cache(a_view):
    @wraps(a_view)
    def _wrapped_view(request, *args, **kwargs):
        response = a_view(request, *args, **kwargs)
        patch_response_headers(response, 86400 * 365)
        return response
    return _wrapped_view


def to_json(what):
    return json.dumps(what, indent=1, cls=JsonEncoder)
