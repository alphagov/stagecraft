from stagecraft.apps.datasets.views.common.utils import (
    to_json, long_cache)
from stagecraft.libs.authorization.http import permission_required
import logging

from django.http import (HttpResponse, HttpResponseBadRequest,
                         HttpResponseNotFound)
from django.views.decorators.cache import never_cache
from django.views.decorators.vary import vary_on_headers

from stagecraft.apps.datasets.models import DataSet, BackdropUser

logger = logging.getLogger(__name__)


@permission_required('signin')
@never_cache
@vary_on_headers('Authorization')
def detail(user, request, name):
    try:
        data_set = DataSet.objects.get(name=name)
        user_is_not_admin = 'admin' not in user['permissions']
        user_is_not_assigned = data_set.backdropuser_set.filter(
            email=user['email']).count() == 0
        if user_is_not_admin and user_is_not_assigned:
            logger.warn("Unauthorized access to '{}' by '{}'".format(
                name, user['email']))
            raise DataSet.DoesNotExist()
    except DataSet.DoesNotExist:
        error = {'status': 'error',
                 'message': "No Data Set named '{}' exists".format(name)}
        logger.warn(error)
        return HttpResponseNotFound(to_json(error))

    json_str = to_json(data_set.serialize())

    return HttpResponse(json_str, content_type='application/json')


@permission_required('admin')
@long_cache
@vary_on_headers('Authorization')
def users(user, request, dataset_name):

    backdrop_users = BackdropUser.objects.filter(
        data_sets__name=dataset_name
    )

    if backdrop_users:
        json_str = to_json(
            [u.api_object() for u in backdrop_users]
        )
    else:
        json_str = to_json([])

    return HttpResponse(json_str, content_type='application/json')


@permission_required('signin')
@never_cache
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

    try:
        filter_kwargs = get_filter_kwargs(key_map, request.GET.items())
        if 'admin' not in user['permissions']:
            filter_kwargs['backdropuser'] = BackdropUser.objects.filter(
                email=user['email'])

        data_sets = DataSet.objects.filter(**filter_kwargs).order_by('pk')
        json_str = to_json([ds.serialize() for ds in data_sets])
    except BackdropUser.DoesNotExist:
        json_str = '[]'

    return HttpResponse(json_str, content_type='application/json')


def health_check(request):
    num_data_sets = DataSet.objects.count()
    json_response = to_json(
        {'message': 'Got {} data sets.'.format(num_data_sets)})
    return HttpResponse(json_response, content_type='application/json')
