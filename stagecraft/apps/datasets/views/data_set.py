import json
import logging
from functools import wraps

from django.conf import settings
from django.http import (HttpResponse, HttpResponseBadRequest,
                         HttpResponseNotFound, HttpResponseForbidden)
from django.views.decorators.vary import vary_on_headers
from django.utils.cache import patch_response_headers

from stagecraft.apps.datasets.models import DataSet
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
def detail(request, name):
    try:
        data_set = DataSet.objects.get(name=name)
    except DataSet.DoesNotExist:
        error = {'status': 'error',
                 'message': "No Data Set named '{}' exists".format(name)}
        logger.warn(error)
        return HttpResponseNotFound(to_json(error))

    json_str = to_json(data_set.serialize())

    return HttpResponse(json_str, content_type='application/json')


@token_required(settings.STAGECRAFT_DATA_SET_QUERY_TOKEN)
@long_cache
@vary_on_headers('Authorization')
def list(request, data_group=None, data_type=None):
    def get_filter_kwargs(key_map, query_params):
        """Return Django filter kwargs from query parameters"""
        return {key_map[k]: v for k, v in query_params if k in key_map}

    # map filter parameter names to query string keys
    key_map = {
        'data-group': 'data_group__name',
        'data_group': 'data_group__name',
        'data-type': 'data_type__name',
        'data_type': 'data_type__name',
    }

    # 400 if any query string keys were not in allowed set
    if not set(request.GET).issubset(key_map):
        unrecognised = set(request.GET).difference(key_map)
        unrecognised_text = ', '.join("'{}'".format(i) for i in unrecognised)
        error = {'status': 'error',
                 'message': 'Unrecognised parameter(s) ({}) were provided'
                            .format(str(unrecognised_text))}
        logger.error(error)
        return HttpResponseBadRequest(to_json(error))

    filter_kwargs = get_filter_kwargs(key_map, request.GET.items())
    data_sets = DataSet.objects.filter(**filter_kwargs)
    json_str = to_json([ds.serialize() for ds in data_sets])

    return HttpResponse(json_str, content_type='application/json')


def health_check(request):
    num_data_sets = DataSet.objects.count()
    json_response = to_json(
        {'message': 'Got {} data sets.'.format(num_data_sets)})
    return HttpResponse(json_response, content_type='application/json')


def to_json(what):
    return json.dumps(what, indent=1)
