
import json

from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from jsonschema.exceptions import SchemaError

from stagecraft.libs.authorization.http import permission_required
from ..models import ModuleType


def json_response(obj):
    return HttpResponse(
        json.dumps(obj),
        content_type='application/json'
    )


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


@csrf_exempt
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
