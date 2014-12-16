from stagecraft.libs.views.utils import to_json, long_cache, create_error
from stagecraft.libs.authorization.http import permission_required
import logging

from django.http import (HttpResponse, HttpResponseBadRequest,
                         HttpResponseNotFound)
from django.views.decorators.cache import never_cache
from django.views.decorators.vary import vary_on_headers
from django.utils.decorators import method_decorator

from stagecraft.apps.datasets.models import DataSet, BackdropUser
from stagecraft.apps.transforms.models import Transform
from stagecraft.apps.transforms.views import TransformView

logger = logging.getLogger(__name__)

from stagecraft.libs.views.resource import ResourceView


class DataSetView(ResourceView):
    model = DataSet
    list_filters = {
        'data-group': 'data_group__name',
        'data_group': 'data_group__name',
        'data-type': 'data_type__name',
        'data_type': 'data_type__name',
    }
    id_field = 'name'

    @method_decorator(permission_required('signin'))
    @method_decorator(never_cache)
    @method_decorator(vary_on_headers('Authorization'))
    def get(self, user, request, **kwargs):
        name = kwargs.get(self.id_field, None)
        if name is not None:
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
                         'message': "No Data Set named '{}' exists".
                         format(name)}
                logger.warn(error)

                error["errors"] = [
                    create_error(request, 404, detail=error['message'])]

                return HttpResponseNotFound(to_json(error))
        else:
            return self.list(user, request)

        json_str = to_json(data_set.serialize())

        return HttpResponse(json_str, content_type='application/json')

    def list(self, user, request):
        # 400 if any query string keys were not in allowed set
        if not set(request.GET).issubset(self.list_filters):
            unrecognised = set(request.GET).difference(self.list_filters)
            unrecognised_text = ', '.join(
                "'{}'".format(i) for i in unrecognised)
            error = {'status': 'error',
                     'message': 'Unrecognised parameter(s) ({}) were provided'
                                .format(str(unrecognised_text))}
            logger.error(error)

            error["errors"] = [
                create_error(request, 400, detail=error['message'])
            ]

            return HttpResponseBadRequest(to_json(error))

        try:
            filter_kwargs = {}
            if 'admin' not in user['permissions']:
                filter_kwargs['backdropuser'] = BackdropUser.objects.filter(
                    email=user['email'])

            data_sets = super(DataSetView, self).list(
                request, additional_filters=filter_kwargs).order_by('pk')
            json_str = to_json([ds.serialize() for ds in data_sets])
        except BackdropUser.DoesNotExist:
            json_str = '[]'

        return HttpResponse(json_str, content_type='application/json')


@never_cache
def transform(request, name):
    try:
        data_set = DataSet.objects.get(name=name)
    except DataSet.DoesNotExist:
        error = {'status': 'error',
                 'message': "No Data Set named '{}' exists".format(name)}
        logger.warn(error)

        error["errors"] = [create_error(request, 404, detail=error['message'])]

        return HttpResponseNotFound(to_json(error))

    data_set_transforms = Transform.objects.filter(
        input_group=data_set.data_group,
        input_type=data_set.data_type)
    data_type_transforms = Transform.objects.filter(
        input_group=None,
        input_type=data_set.data_type)

    transforms = data_set_transforms | data_type_transforms

    serialized_transforms = [TransformView.serialize(t) for t in transforms]

    return HttpResponse(
        to_json(serialized_transforms),
        content_type='application/json')


@permission_required('dashboard')
@never_cache
def dashboard(user, request, name):
    try:
        data_set = DataSet.objects.get(name=name)
    except DataSet.DoesNotExist:
        error = {'status': 'error',
                 'message': "No Data Set named '{}' exists".format(name)}
        logger.warn(error)

        error["errors"] = [create_error(request, 404, detail=error['message'])]

        return HttpResponseNotFound(to_json(error))

    modules = data_set.module_set.distinct('dashboard')
    dashboards = [m.dashboard for m in modules]

    json_str = to_json([d.serialize() for d in dashboards])
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


def health_check(request):
    num_data_sets = DataSet.objects.count()
    json_response = to_json(
        {'message': 'Got {} data sets.'.format(num_data_sets)})
    return HttpResponse(json_response, content_type='application/json')
