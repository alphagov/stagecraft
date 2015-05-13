import json

from django.http import HttpResponse
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_GET
from django.views.decorators.cache import never_cache

from stagecraft.libs.authorization.http import permission_required
from stagecraft.libs.validation.validation import is_uuid

from stagecraft.apps.datasets.models import DataGroup, DataType
from .models import Transform, TransformType

from stagecraft.libs.views.resource import ResourceView


def resolve_data_reference(reference):
    if 'data-group' in reference:
        try:
            data_group = DataGroup.objects.get(name=reference['data-group'])
        except DataGroup.DoesNotExist:
            data_group = None
    else:
        data_group = None

    if 'data-type' in reference:
        try:
            data_type = DataType.objects.get(name=reference['data-type'])
        except DataType.DoesNotExist:
            data_type = None
    else:
        data_type = None

    return data_group, data_type


class TransformTypeView(ResourceView):

    model = TransformType
    schema = {
        "$schema": "http://json-schema.org/schema#",
        "type": "object",
        "properties": {
            "name": {
                "type": "string",
            },
            "function": {
                "type": "string",
                "format": "function_name",
            },
            "schema": {
                "type": "object",
            }
        },
        "required": ["name", "function", "schema"],
        "additionalProperties": False,
    }

    permissions = {
        'get': None,
        'post': 'transforms',
        'put': 'transforms',
    }

    @method_decorator(never_cache)
    def get(self, request, **kwargs):
        return super(TransformTypeView, self).get(request, **kwargs)

    def update_model(self, model, model_json, request):
        model.name = model_json['name']
        model.function = model_json['function']
        model.schema = model_json['schema']

    @staticmethod
    def serialize(model):
        return {
            'id': str(model.id),
            'name': model.name,
            'schema': model.schema,
            'function': model.function,
        }


class TransformView(ResourceView):

    model = Transform
    schema = {
        "$schema": "http://json-schema.org/schema#",
        "type": "object",
        "properties": {
            "type_id": {
                "type": "string",
                "format": "uuid",
            },
            "input": {
                "type": "object",
                "properties": {
                    "data-group": {
                        "type": "string",
                        "format": "slug",
                    },
                    "data-type": {
                        "type": "string",
                        "format": "slug",
                    },
                },
                "required": ["data-type"],
                "additionalProperties": False,
            },
            "query-parameters": {
                "type": "object",
            },
            "options": {
                "type": "object",
            },
            "output": {
                "type": "object",
                "properties": {
                    "data-group": {
                        "type": "string",
                        "format": "slug",
                    },
                    "data-type": {
                        "type": "string",
                        "format": "slug",
                    },
                },
                "required": ["data-type"],
                "additionalProperties": False,
            },
        },
        "required": [
            "type_id", "input", "query-parameters",
            "options", "output"
        ],
        "additionalProperties": False,
    }

    permissions = {
        'get': None,
        'post': 'transforms',
        'put': 'transforms',
    }

    @method_decorator(never_cache)
    def get(self, request, **kwargs):
        return super(TransformView, self).get(request, **kwargs)

    def update_model(self, model, model_json, request):
        try:
            transform_type = TransformType.objects.get(
                id=model_json['type_id'])
        except TransformType.DoesNotExist:
            return HttpResponse('transform type was not found', status=400)

        (input_group, input_type) = resolve_data_reference(model_json['input'])

        if input_type is None:
            return HttpResponse(
                'input requires at least a data-type (that exists)',
                status=400)

        (output_group, output_type) = \
            resolve_data_reference(model_json['output'])

        if output_type is None:
            return HttpResponse(
                'output requires at least a data-type (that exists)',
                status=400)

        model.type = transform_type
        model.input_group = input_group
        model.input_type = input_type
        model.query_parameters = model_json['query-parameters']
        model.options = model_json['options']
        model.output_group = output_group
        model.output_type = output_type

        return None

    @staticmethod
    def serialize(model):
        out = {
            'id': str(model.id),
            'type': {
                'id': str(model.type.id),
                'function': model.type.function,
            },
            'input': {
                'data-type': model.input_type.name,
            },
            'query-parameters': model.query_parameters,
            'options': model.options,
            'output': {
                'data-type': model.output_type.name,
            }
        }

        if model.input_group is not None:
            out['input']['data-group'] = model.input_group.name
        if model.output_group is not None:
            out['output']['data-group'] = model.output_group.name

        return out
