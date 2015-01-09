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
    BackdropUser,
    DataGroup,
    DataType,
    generate_data_set_name)
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
    id_field = 'name'
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

    @method_decorator(permission_required('signin'))
    @method_decorator(never_cache)
    @method_decorator(vary_on_headers('Authorization'))
    def get(self, user, request, **kwargs):
        kwargs['user'] = user
        return super(DataSetView, self).get(
            request,
            **kwargs)

    @method_decorator(permission_required('signin'))
    @method_decorator(never_cache)
    @method_decorator(vary_on_headers('Authorization'))
    def post(self, user, request, **kwargs):
        model_json, err = self._validate_json(request)
        if err:
            return err
        try:
            data_group = DataGroup.objects.get(name=model_json['data_group'])
            data_type = DataType.objects.get(name=model_json['data_type'])
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
        model_json['data_group'] = data_group
        model_json['data_type'] = data_type
        name = generate_data_set_name(data_group, data_type)
        model_json['name'] = name
        kwargs['model_json'] = model_json
        try:
            return super(DataSetView, self).post(user, request, **kwargs)
        except InstanceExistsError:
            return build_400(
                logger,
                request,
                "A data set with the name '{}' already exists"
                .format(name))

    def _get_or_create_model(self, model_json):
        model = super(DataSetView, self)._get_or_create_model(model_json)
        # update should work if the following two lines are removed.
        if model.pk:
            raise InstanceExistsError
        return model
        # Don't yet support update with data sets.

    def update_model(self, model, model_json):
        for (key, value) in model_json.items():
            setattr(model, key, value)
        model.save()

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
