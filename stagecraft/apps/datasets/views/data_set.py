from stagecraft.apps.datasets.views.common.utils import *
import logging

from django.conf import settings
from django.http import (HttpResponse, HttpResponseBadRequest,
                         HttpResponseNotFound)
from django.views.decorators.vary import vary_on_headers

from stagecraft.apps.datasets.models import DataSet

logger = logging.getLogger(__name__)


@permission_required('dataset')
@long_cache
@vary_on_headers('Authorization')
def detail(user, request, name):
    try:
        data_set = DataSet.objects.get(name=name)
    except DataSet.DoesNotExist:
        error = {'status': 'error',
                 'message': "No Data Set named '{}' exists".format(name)}
        logger.warn(error)
        return HttpResponseNotFound(to_json(error))

    json_str = to_json(data_set.serialize())

    return HttpResponse(json_str, content_type='application/json')


@permission_required('dataset')
@long_cache
@vary_on_headers('Authorization')
def list(user, request, data_group=None, data_type=None):
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
    data_sets = DataSet.objects.filter(**filter_kwargs).order_by('pk')
    json_str = to_json([ds.serialize() for ds in data_sets])

    return HttpResponse(json_str, content_type='application/json')


def health_check(request):
    num_data_sets = DataSet.objects.count()
    json_response = to_json(
        {'message': 'Got {} data sets.'.format(num_data_sets)})
    return HttpResponse(json_response, content_type='application/json')
