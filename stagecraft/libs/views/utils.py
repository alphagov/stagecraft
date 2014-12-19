import json

from django.utils.cache import patch_response_headers
from functools import wraps
from uuid import UUID
from django.http import HttpResponseBadRequest


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


def build_400(logger, request, message):
    error = {'status': 'error',
             'message': message}
    logger.error(error)

    error["errors"] = [
        create_error(request, 400, detail=error['message'])
    ]

    return HttpResponseBadRequest(to_json(error))


def create_error(request, status, code='', title='', detail=''):
    """creates a JSON API error - http://jsonapi.org/format/#errors

    "status" - The HTTP status code applicable to this problem,
               expressed as a string value.
    "code" - An application-specific error code, expressed as a
             string value.
    "title" - A short, human-readable summary of the problem. It
              SHOULD NOT change from occurrence to occurrence of
              the problem, except for purposes of localization.
    "detail" - A human-readable explanation specific to this
               occurrence of the problem.
    """
    return {
        'id': request.META.get('HTTP_REQUEST_ID', ''),
        'status': str(status),
        'code': code,
        'title': title,
        'detail': detail,
    }
