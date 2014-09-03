
import json

from django.http import HttpResponse

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


def add_type(request):
    return HttpResponse('{}')
