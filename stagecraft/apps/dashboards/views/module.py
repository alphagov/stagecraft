
import json

from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from jsonschema.exceptions import SchemaError, ValidationError

from stagecraft.apps.datasets.models import DataSet
from stagecraft.libs.authorization.http import permission_required

from ..models import Dashboard, Module, ModuleType


def json_response(obj):
    return HttpResponse(
        json.dumps(obj),
        content_type='application/json'
    )


required_keys = ['type_id', 'slug', 'title', 'description', 'info', 'options']


@csrf_exempt
def modules_on_dashboard(request, dashboard_id):
    try:
        dashboard = Dashboard.objects.get(id=dashboard_id)
    except Dashboard.DoesNotExist:
        return HttpResponse('dashboard does not exist', status=404)

    if request.method == 'GET':
        return list_modules_on_dashboard(request, dashboard)
    elif request.method == 'POST':
        return add_module_to_dashboard(request, dashboard)
    else:
        return HttpResponse('', status=405)


def list_modules_on_dashboard(request, dashboard):
    modules = Module.objects.filter(dashboard=dashboard)
    serialized = [module.serialize() for module in modules]

    return json_response(serialized)


@permission_required('dashboard')
def add_module_to_dashboard(user, request, dashboard):
    if request.META.get('CONTENT_TYPE', '').lower() != 'application/json':
        return HttpResponse('bad content type', status=415)

    try:
        module_settings = json.loads(request.body)
    except ValueError:
        return HttpResponse('bad json', status=400)

    if any(key not in module_settings for key in required_keys):
        return HttpResponse(
            'missing keys from: {}'.format(', '.join(required_keys)),
            status=400
        )

    try:
        module_type = ModuleType.objects.get(id=module_settings['type_id'])
    except ModuleType.DoesNotExist:
        return HttpResponse('module type was not found', status=400)

    module = Module(
        dashboard=dashboard,
        type=module_type,

        slug=module_settings['slug'],
        title=module_settings['title'],
        description=module_settings['description'],
        info=module_settings['info'],
        options=module_settings['options'],
    )

    try:
        module.validate_options()
    except ValidationError as err:
        return HttpResponse(
            'options field failed validation: {}'.format(err.message),
            status=400)

    if 'data_set_id' in module_settings:
        try:
            data_set = DataSet.objects.get(id=module_settings['data_set_id'])
        except DataSet.DoesNotExist:
            return HttpResponse('data set does not exist', status=400)

        module.data_set = data_set
        module.query_parameters = module_settings.get('query_parameters', {})

        try:
            module.validate_query_parameters()
        except ValidationError as err:
            return HttpResponse(
                'Query parameters not valid: {}'.format(err.message),
                status=400)
    elif 'query_parameters' in module_settings:
        return HttpResponse('query_parameters but no data set', status=400)

    module.save()

    return json_response(module.serialize())


@csrf_exempt
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
