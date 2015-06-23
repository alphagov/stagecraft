from django.utils.decorators import method_decorator
from stagecraft.libs.views.resource import ResourceView, UUID_RE_STRING
import json

from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from jsonschema.exceptions import ValidationError
from django.core.exceptions import ValidationError as DjangoValidationError
from django.views.decorators.cache import never_cache
from django.db import DataError

from stagecraft.apps.datasets.models import DataSet
from stagecraft.libs.validation.validation import is_uuid

from ..models import Dashboard, Module, ModuleType
from stagecraft.libs.views.utils import create_http_error
from stagecraft.libs.authorization.http import _get_resource_role_permissions


def json_response(obj):
    return HttpResponse(
        json.dumps(obj),
        content_type='application/json'
    )


REQUIRED_KEYS = set(['type_id', 'slug', 'title', 'description', 'info',
                     'options', 'order'])


def add_module_to_dashboard(dashboard, module_settings, parent_module=None):

    def make_error(msg_part):
        return "Error in module {0} (slug '{1}') - message: '{2}'".format(
            module_settings['order'], module_settings['slug'], msg_part)

    missing_keys = REQUIRED_KEYS - set(module_settings.keys())
    if len(missing_keys) > 0:
        raise ValueError('missing keys: {}'.format(', '.join(missing_keys)))

    try:
        module_type = ModuleType.objects.get(id=module_settings['type_id'])
    except(ModuleType.DoesNotExist, DataError):
        raise ValueError(make_error('module type was not found'))

    if module_settings.get('id'):
        try:
            module = Module.objects.get(id=module_settings['id'])
        except Module.DoesNotExist:
            msg = 'module with id {} not found'.format(module_settings['id'])
            raise ValueError(make_error(msg))
    else:
        module = Module()

    module.dashboard = dashboard
    module.type = module_type
    module.slug = module_settings['slug']
    module.title = module_settings['title']
    module.description = module_settings['description']
    module.info = module_settings['info']
    module.options = module_settings['options']
    module.order = module_settings['order']

    if parent_module is not None:
        module.parent = parent_module
    else:
        module.parent = None

    try:
        module.validate_options()
    except ValidationError as err:
        msg = 'options field failed validation: {}'.format(err.message)
        raise ValueError(make_error(msg))

    if module_settings.get('data_group') and module_settings.get('data_type'):
        try:
            data_set = DataSet.objects.get(
                data_group__name=module_settings['data_group'],
                data_type__name=module_settings['data_type'],
            )
        except DataSet.DoesNotExist:
            raise ValueError(make_error('data set does not exist'))

        module.data_set = data_set
        module.query_parameters = module_settings.get('query_parameters', {})

        try:
            module.validate_query_parameters()
        except ValidationError as err:
            msg = 'Query parameters not valid: {}'.format(err.message)
            raise ValueError(make_error(msg))
    elif module_settings.get('query_parameters'):
        raise ValueError(make_error('query_parameters but no data set'))

    try:
        module.full_clean()
    except DjangoValidationError as err:
        messages = [
            '{}: {}'.format(k, ' '.join(v))
            for k, v in err.message_dict.items()
        ]
        msg = "\n".join(messages)
        raise ValueError(make_error(msg))

    module.save()

    return module


class ModuleView(ResourceView):
    model = Module

    id_fields = {
        'id': UUID_RE_STRING,
        'slug': '[\w-]+',
    }

    list_filters = {
        'name': 'name__iexact'
    }

    schema = {
        "$schema": "http://json-schema.org/schema#",
        "type": "object",
        "properties": {
            "name": {
                "type": "string",
            },
            "type_id": {
                "type": "string",
            },
            "dashboard": {
                "type": "string",
            },
            "data_group": {
                "type": "string",
            },
            "data_type": {
                "type": "string",
            },
            "parent": {
                "type": "string",
            },
            "slug": {
                "type": "string",
            },
            "title": {
                "type": "string",
            },
            "description": {
                "type": "string",
            },
            "info": {
                "type": "array",
            },
            "options": {
                "type": "object",
            },
            "query_parameters": {
                "type": "object",
            },
            "order": {
                "type": "integer",
            },
            "objects": {
                "type": "string",
            },
            "modules": {
                "type": "array"
            }
        },
        "required": ["type_id", "slug", "title", "order"],
        "additionalProperties": False,
    }

    permissions = _get_resource_role_permissions('Module')

    def list(self, request, **kwargs):
        query_set = super(ModuleView, self).list(request, **kwargs)

        if 'parent' in kwargs:
            query_set = query_set.filter(dashboard=kwargs['parent'].id)

        return query_set

    @csrf_exempt
    @method_decorator(never_cache)
    def get(self, request, **kwargs):
        return super(ModuleView, self).get(request, **kwargs)

    @csrf_exempt
    @method_decorator(never_cache)
    def put(self, request, **kwargs):
        return create_http_error(
            405,
            "Can't put to a resource,"
            "update only supported through dashboard",
            request)

    def update_model(self, model, model_json, request, parent):

        try:
            module_type = ModuleType.objects.get(id=model_json['type_id'])
        except ModuleType.DoesNotExist:
            return create_http_error(404, 'module type not found', request)

        if parent is None:
            return create_http_error(404, 'no parent dashboard found', request)
        try:
            dashboard = Dashboard.objects.get(id=parent.id)
        except Dashboard.DoesNotExist:
            return create_http_error(404, 'dashboard not found', request)

        model.type = module_type
        model.dashboard = dashboard
        model.slug = model_json['slug']
        model.title = model_json['title']
        model.description = model_json['description']
        model.info = model_json['info']
        model.options = model_json['options']
        model.order = model_json['order']

        if model_json.get('data_group') and model_json.get('data_type'):
            try:
                data_set = DataSet.objects.get(
                    data_group__name=model_json['data_group'],
                    data_type__name=model_json['data_type'],
                )
            except DataSet.DoesNotExist:
                return create_http_error(400, 'data set does not exit',
                                         request)

            model.data_set = data_set
            model.query_parameters = model_json.get('query_parameters', {})

            try:
                model.validate_query_parameters()
            except ValidationError as err:
                msg = 'Query parameters not valid: {}'.format(err.message)
                return create_http_error(400, msg, request)
        elif model_json.get('query_parameters'):
            return create_http_error(400, 'query parameters but not data set',
                                     request)

    def update_relationships(self, model, model_json, request, parent):
        if 'parent_id' in model_json:
            parent_id = model_json['parent_id']
            if not is_uuid(parent_id):
                return create_http_error(400, 'parent_id has to be a uuid',
                                         request)

            try:
                parent_node = Dashboard.objects.get(id=parent_id)
            except Dashboard.DoesNotExist:
                return create_http_error(400, 'parent not found', request)

            model.parents.add(parent_node)

    @staticmethod
    def serialize(model):
        return model.serialize()


class ModuleTypeView(ResourceView):
    model = ModuleType

    id_fields = {
        'name': '[\w-]+',
    }

    schema = {
        "$schema": "http://json-schema.org/schema#",
        "type": "object",
        "properties": {
            "name": {
                "type": "string",
            },
            "schema": {
                "type": "object",
            }
        },
        "required": ["name", "schema"],
        "additionalProperties": False,
    }

    list_filters = {
        'name': 'name__iexact'
    }

    permissions = _get_resource_role_permissions('ModuleType')

    @method_decorator(never_cache)
    def get(self, request, **kwargs):
        return super(ModuleTypeView, self).get(request, **kwargs)

    def update_model(self, model, model_json, request, parent):
        for (key, value) in model_json.items():
            setattr(model, key, value)

    @staticmethod
    def serialize(model):
        return {
            'id': str(model.id),
            'name': model.name,
            'schema': model.schema,
        }
