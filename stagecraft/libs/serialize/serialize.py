import json

from django.core import serializers
from django.db.models.query import QuerySet


def serialize_to_json(query_set):
    """Return a JSON serialized version of a QuerySet or list of Models"""
    def serialize(query_set):
        serialized = serializers.serialize('python', query_set)
        return [i['fields'] for i in serialized]

    if isinstance(query_set, QuerySet):
        result = serialize(query_set)
    else:
        result = serialize([query_set])[0]

    return json.dumps(result)
