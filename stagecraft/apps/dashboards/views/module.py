
import json

from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from jsonschema.exceptions import SchemaError, ValidationError
from django.core.exceptions import ValidationError as DjangoValidationError
from django.views.decorators.cache import never_cache
from django.db import DataError

from stagecraft.apps.datasets.models import DataSet
from stagecraft.libs.authorization.http import permission_required

from ..models import Dashboard, Module, ModuleType


def json_response(obj):
    return HttpResponse(
        json.dumps(obj),
        content_type='application/json'
    )


required_keys = set(['type_id', 'slug', 'title', 'description', 'info',
                     'options', 'order'])


@csrf_exempt
@never_cache
def modules_on_dashboard(request, dashboard_id):
    try:
        dashboard = Dashboard.objects.get(id=dashboard_id)
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


def add_module_to_dashboard(dashboard, module_settings):
    missing_keys = required_keys - set(module_settings.keys())
    if len(missing_keys) > 0:
        raise ValueError(
            'missing keys: {}'.format(', '.join(missing_keys)))

    try:
        module_type = ModuleType.objects.get(id=module_settings['type_id'])
    except(ModuleType.DoesNotExist, DataError):
        raise ValueError('module type was not found')

    if module_settings.get('id'):
        try:
            module = Module.objects.get(id=module_settings['id'])
        except Module.DoesNotExist as e:
            raise ValueError('module with id {} not found'.format(
                module_data['id']))
    else:
        module = Module(
        )

    module.dashboard = dashboard
    module.type = module_type
    module.slug = module_settings['slug']
    module.title = module_settings['title']
    module.description = module_settings['description']
    module.info = module_settings['info']
    module.options = module_settings['options']
    module.order = module_settings['order']

    try:
        module.validate_options()
    except ValidationError as err:
        raise ValueError(
            'options field failed validation: {}'.format(err.message))

    if module_settings.get('data_group') and module_settings.get('data_type'):
        try:
            data_set = DataSet.objects.get(
                data_group__name=module_settings['data_group'],
                data_type__name=module_settings['data_type'],
            )
        except DataSet.DoesNotExist:
            raise ValueError('data set does not exist')

        module.data_set = data_set
        module.query_parameters = module_settings.get('query_parameters', {})

        try:
            module.validate_query_parameters()
        except ValidationError as err:
            raise ValueError(
                'Query parameters not valid: {}'.format(err.message))
    elif module_settings.get('query_parameters'):
        raise ValueError('query_parameters but no data set')

    try:
        module.full_clean()
    except DjangoValidationError as err:
        messages = [
            '{}: {}'.format(k, ' '.join(v))
            for k, v in err.message_dict.items()
        ]
        message = "\n".join(messages)
        raise ValueError(message)

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


@csrf_exempt
@never_cache
def root_types(request):
    if request.method == 'GET':
        return list_types(request)
    elif request.method == 'POST':
        return add_type(request)
    else:
        return HttpResponse('', status=405)


def list_types(request):
    query_parameters = {
        'name': request.GET.get('name', None),
    }
    filter_args = {
        "{}__iexact".format(k): v
        for (k, v) in query_parameters.items() if v is not None
    }

    module_types = ModuleType.objects.filter(**filter_args)
    serialized = [module_type.serialize() for module_type in module_types]

    return json_response(serialized)


@permission_required('dashboard')
def add_type(user, request):
    if request.META.get('CONTENT_TYPE', '').lower() != 'application/json':
        return HttpResponse('bad content type', status=415)

    try:
        type_settings = json.loads(request.body)
    except ValueError:
        return HttpResponse('bad json', status=400)

    if 'name' not in type_settings or 'schema' not in type_settings:
        return HttpResponse('name and schema fields required', status=400)

    module_type = ModuleType(
        name=type_settings['name'],
        schema=type_settings['schema'])

    try:
        module_type.validate_schema()
    except SchemaError as err:
        return HttpResponse('bad schema: ' + err.message, status=400)

    module_type.save()

    return json_response(module_type.serialize())
