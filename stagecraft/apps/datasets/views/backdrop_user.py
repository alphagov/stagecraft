import json
import logging
from functools import wraps

from django.conf import settings
from django.http import (HttpResponse, HttpResponseBadRequest,
                         HttpResponseNotFound, HttpResponseForbidden)
from django.views.decorators.vary import vary_on_headers
from django.utils.cache import patch_response_headers

from stagecraft.apps.datasets.models import BackdropUser
from stagecraft.libs.validation.validation import extract_bearer_token

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


@token_required(settings.STAGECRAFT_DATA_SET_QUERY_TOKEN)
@long_cache
@vary_on_headers('Authorization')
def detail(request, email):
    import pprint as pp
    pp.pprint(request)
    pp.pprint(email)
    pp.pprint("YOLO")
    try:
        backdrop_user = BackdropUser.objects.get(email=email)
    except BackdropUser.DoesNotExist:
        error = {
            'status': 'error',
            'message': "No user with email address '{}' exists".format(email)
        }
        logger.warn(error)
        return HttpResponseNotFound(to_json(error))

    json_str = to_json(backdrop_user.serialize())

    return HttpResponse(json_str, content_type='application/json')


def to_json(what):
    return json.dumps(what, indent=1)
