from django.utils.decorators import method_decorator
from stagecraft.libs.views.resource import ResourceView
import json

from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from jsonschema.exceptions import SchemaError, ValidationError
from django.core.exceptions import ValidationError as DjangoValidationError
from django.views.decorators.cache import never_cache
from django.db import DataError

from stagecraft.apps.datasets.models import DataSet
from stagecraft.libs.authorization.http import permission_required
from stagecraft.libs.validation.validation import is_uuid

from ..models import Dashboard, Module, ModuleType


def json_response(obj):
    return HttpResponse(
        json.dumps(obj),
        content_type='application/json'
    )


REQUIRED_KEYS = set(['type_id', 'slug', 'title', 'description', 'info',
                     'options', 'order'])


@csrf_exempt
@never_cache
def modules_on_dashboard(request, identifier):

    try:
        if is_uuid(identifier):
            dashboard = Dashboard.objects.get(id=identifier)
        else:
            dashboard = Dashboard.objects.get(slug=identifier)
    except Dashboard.DoesNotExist:
        return HttpResponse('dashboard does not exist', status=404)

    if request.method == 'GET':
        return list_modules_on_dashboard(request, dashboard)
    elif request.method == 'POST':
        return add_module_to_dashboard_view(request, dashboard)
    else:
        return HttpResponse('', status=405)


def list_modules_on_dashboard(request, dashboard):
    modules = Module.objects.filter(dashboard=dashboard)
    serialized = [module.serialize() for module in modules]

    return json_response(serialized)


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


@permission_required('dashboard')
def add_module_to_dashboard_view(user, request, dashboard):
    if request.META.get('CONTENT_TYPE', '').lower() != 'application/json':
        return HttpResponse('bad content type', status=415)

    try:
        module_settings = json.loads(request.body)
    except ValueError:
        return HttpResponse('bad json', status=400)

    try:
        module = add_module_to_dashboard(dashboard, module_settings)
    except ValueError as e:
        return HttpResponse(e.message, status=400)

    return json_response(module.serialize())


class ModuleView(ResourceView):
    model = Module

    @csrf_exempt
    @never_cache
    def get(self, request, **kwargs):
        return super(ModuleView, self).get(request, **kwargs)

    def post(self, request, **kwargs):
        # block direct creation of modules for now.
        return HttpResponse('', status=405)

    def put(self, request, **kwargs):
        # block direct creation of modules for now.
        return HttpResponse('', status=405)

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

    permissions = {
        'get': None,
        'post': 'dashboard',
        'put': 'dashboard',
    }

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
