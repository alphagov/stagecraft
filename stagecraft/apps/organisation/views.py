import json

from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_GET

from stagecraft.libs.authorization.http import permission_required
from stagecraft.libs.validation.validation import is_uuid
from .models import Node, NodeType


def json_response(obj):
    return HttpResponse(
        json.dumps(obj),
        content_type='application/json'
    )


@csrf_exempt
def root_nodes(request):
    if request.method == 'GET':
        return list_nodes(request)
    elif request.method == 'POST':
        return add_node(request)
    else:
        return HttpResponse('', status=405)


def list_nodes(request):
    query_parameters = {
        'name': request.GET.get('name', None),
        'abbreviation': request.GET.get('abbreviation', None),
    }
    filter_args = {
        "{}__iexact".format(k): v
        for (k, v) in query_parameters.items() if v is not None
    }

    nodes = Node.objects.filter(**filter_args)
    serialized = [node.serialize() for node in nodes]

    return json_response(serialized)


@permission_required('organisation')
def add_node(user, request):
    """ Add a node

    Request format

    {
        "name": "required string",
        "type_id": "required string",
        "abbreviation": "optional string",
        "parent_id": "optional uuuid"
    }


    Arguments:
        user: a signon user
        request: a django request object containing json of the form specified

    """
    try:
        node_settings = json.loads(request.body)
    except ValueError:
        return HttpResponse('bad json', status=400)

    if 'name' not in node_settings or 'type_id' not in node_settings:
        return HttpResponse('need name and type_id', status=400)

    type_id = node_settings['type_id']
    if not is_uuid(type_id):
        return HttpResponse('type_id has to be a uuid', status=400)

    try:
        node_type = NodeType.objects.get(id=type_id)
    except NodeType.DoesNotExist:
        return HttpResponse('no NodeType found', status=400)

    if 'parent_id' in node_settings:
        parent_id = node_settings['parent_id']
        if not is_uuid(parent_id):
            return HttpResponse('parent_id has to be a uuid', status=400)

        try:
            parent_node = Node.objects.get(id=parent_id)
        except Node.DoesNotExist:
            return HttpResponse('parent not found', status=400)
    else:
        parent_node = None

    node = Node(
        name=node_settings['name'],
        abbreviation=node_settings.get('abbreviation', None),
        typeOf=node_type,
        parent=parent_node
    )
    node.save()

    return json_response(node.serialize())


@require_GET
def node_ancestors(request, node_id):
    try:
        node = Node.objects.get(id=node_id)
    except Node.DoesNotExist:
        return HttpResponse('node not found', 404)

    include_self = request.GET.get('self', 'false') == 'true'
    nodes = node.get_ancestors(include_self=include_self)
    serialized = [node.serialize() for node in nodes]

    return json_response(serialized)


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

    node_types = NodeType.objects.filter(**filter_args)
    serialized = [node_type.serialize() for node_type in node_types]

    return json_response(serialized)


@permission_required('organisation')
def add_type(user, request):
    try:
        type_settings = json.loads(request.body)
    except ValueError:
        return HttpResponse('bad json', status=400)

    if 'name' not in type_settings:
        return HttpResponse('need name', status=400)

    node_type = NodeType(name=type_settings['name'])
    node_type.save()

    return json_response(node_type.serialize())
