import json

from django.core import serializers
from django.http import HttpResponse, Http404
from django.shortcuts import render

from stagecraft.apps.datasets.models import DataSet


def detail(request, name):
    try:
        data_set = DataSet.objects.get(name=name)
    except DataSet.DoesNotExist:
        raise Http404

    serialized = serializers.serialize('python', [data_set])
    result = serialized[0]['fields']
    json_str = json.dumps(result)

    return HttpResponse(json_str, content_type='application/json')


def list(request, data_group=None, data_type=None):
    # map filter parameter names to query string keys
    key_map = {
        'data-group': 'data_group__name',
        'data-type': 'data_type__name',
    }

    # 404 if any query string keys were not in allowed set
    if not set(request.GET).issubset(key_map):
        raise Http404

    # get allowed filter parameters
    kwargs = {key_map[k]: v for k, v in request.GET.items() if k in key_map}

    data_sets = DataSet.objects.filter(**kwargs)
    serialized = serializers.serialize('python', data_sets)
    results = [i['fields'] for i in serialized]
    json_str = json.dumps(results)

    return HttpResponse(json_str, content_type='application/json')
