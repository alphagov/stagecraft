from stagecraft.libs.views.utils import(
    to_json,
    long_cache,
    create_error,
    build_400)
from stagecraft.libs.authorization.http import permission_required
import logging

from django.http import (HttpResponse,
                         HttpResponseNotFound)
from django.views.decorators.cache import never_cache
from django.views.decorators.vary import vary_on_headers
from django.utils.decorators import method_decorator

from stagecraft.apps.datasets.models import(
    DataSet,
    DataGroup,
    DataType)
from stagecraft.apps.users.models import User
from stagecraft.apps.transforms.models import Transform
from stagecraft.apps.transforms.views import TransformView

logger = logging.getLogger(__name__)

from stagecraft.libs.views.resource import ResourceView


class InstanceExistsError(Exception):
    pass


class DataSetView(ResourceView):
    model = DataSet
    list_filters = {
        'data-group': 'data_group__name',
        'data_group': 'data_group__name',
        'data-type': 'data_type__name',
        'data_type': 'data_type__name',
    }
    id_fields = {
        'name': '[\w-]+',
    }
    generated_id = False
    schema = {
        "$schema": "http://json-schema.org/schema#",
        "type": "object",
        "properties": {
            "bearer_token": {
                "type": "string"
            },
            "capped_size": {
                "type": "string"
            },
            "data_type": {
                "type": "string"
            },
            "realtime": {
                "type": "boolean"
            },
            "auto_ids": {
                "type": "string"
            },
            "queryable": {
                "type": "boolean"
            },
            "upload_format": {
                "type": "string"
            },
            "published": {
                "type": "boolean"
            },
            "upload_filters": {
                "type": "string"
            },
            "max_age_expected": {
                "type": "number"
            },
            "data_group": {
                "type": "string"
            },
            "raw_queries_allowed": {
                "type": "boolean"
            },
        },
        "required": ["data_type", "data_group"],
        "additionalProperties": False,
    }

    permissions = {
        'get': 'signin',
        'post': 'signin',
        'put': 'signin',
    }

    def list(self, request, **kwargs):
        '''
        Override ResourceView's list function (called by its 'get' function)
        so that the retrieval of all data sets can be optimised
        by eager loading data group and type associations.
        '''
        queryset = super(DataSetView, self).list(request, **kwargs)
        return queryset.select_related('data_group', 'data_type')

    @method_decorator(never_cache)
    @method_decorator(vary_on_headers('Authorization'))
    def get(self, request, **kwargs):
        return super(DataSetView, self).get(
            request,
            **kwargs)

    @method_decorator(never_cache)
    @method_decorator(vary_on_headers('Authorization'))
    def post(self, request, **kwargs):
        return super(DataSetView, self).post(request, **kwargs)

    def update_model(self, model, model_json, request):
        try:
            data_group = DataGroup.objects.get(name=model_json['data_group'])
            data_type = DataType.objects.get(name=model_json['data_type'])
            model_json['data_group'] = data_group
            model_json['data_type'] = data_type
            for (key, value) in model_json.items():
                setattr(model, key, value)
        except DataGroup.DoesNotExist:
            return build_400(
                logger,
                request,
                "No data group with name '{}' found"
                .format(model_json['data_group']))
        except DataType.DoesNotExist:
            return build_400(
                logger,
                request,
                "No data type with name '{}' found"
                .format(model_json['data_type']))

    @staticmethod
    def serialize(model):
        # I know this should be properly extracted out but for now.
        return model.serialize()


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

    users = User.objects.filter(
        data_sets__name=dataset_name
    )

    if users:
        json_str = to_json(
            [u.api_object() for u in users]
        )
    else:
        json_str = to_json([])

    return HttpResponse(json_str, content_type='application/json')


def health_check(request):
    num_data_sets = DataSet.objects.count()
    json_response = to_json(
        {'message': 'Got {} data sets.'.format(num_data_sets)})
    return HttpResponse(json_response, content_type='application/json')
