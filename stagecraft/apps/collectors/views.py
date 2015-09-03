import logging
from operator import xor
from django.views.decorators.csrf import csrf_exempt

from stagecraft.apps.collectors.models import Provider, DataSource, \
    CollectorType, Collector
from stagecraft.apps.datasets.models import DataSet
from stagecraft.libs.views.resource import ResourceView, UUID_RE_STRING
from stagecraft.libs.views.utils import add_items_to_model
from stagecraft.apps.collectors.tasks import run_collector as \
    run_collector_task
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from stagecraft.libs.authorization.http import permission_required
from stagecraft.libs.views.resource import user_missing_model_permission
from stagecraft.libs.views.utils import create_http_error

logger = logging.getLogger(__name__)
logger.setLevel('ERROR')


def add_provider_to_model(model, model_json, request):
    try:
        provider = Provider.objects.get(id=model_json['provider_id'])
        model_json['provider'] = provider
        add_items_to_model(model, model_json)
    except Provider.DoesNotExist:
        message = "No provider with id '{}' found".format(
            model_json['provider_id'])
        return create_http_error(400, message, request, logger=logger)


class ProviderView(ResourceView):
    model = Provider

    schema = {
        "$schema": "http://json-schema.org/schema#",
        "type": "object",
        "properties": {
            "slug": {
                "type": "string",
            },
            "name": {
                "type": "string"
            },
            "credentials_schema": {
                "type": "object"
            }
        },
        "required": ["name", "slug"],
        "additionalProperties": False,
    }

    id_fields = {
        'id': UUID_RE_STRING,
        'slug': '[\w-]+',
    }
    list_filters = {
        "name": "name__iexact"
    }

    def update_model(self, model, model_json, request, parent):
        add_items_to_model(model, model_json)

    @staticmethod
    def serialize(model):
        return {
            'id': str(model.id),
            'slug': model.slug,
            'name': model.name,
            'credentials_schema': model.credentials_schema
        }


class DataSourceView(ResourceView):
    model = DataSource

    schema = {
        "$schema": "http://json-schema.org/schema#",
        "type": "object",
        "properties": {
            "slug": {
                "type": "string"
            },
            "name": {
                "type": "string"
            },
            "provider_id": {
                "type": "string",
                "format": "uuid"
            },
            "credentials": {
                "type": "object"
            }
        },
        "required": ["name", "slug", "provider_id"],
        "additionalProperties": False,
    }

    id_fields = {
        'id': UUID_RE_STRING,
        'slug': '[\w-]+',
    }
    list_filters = {
        "name": "name__iexact"
    }

    def update_model(self, model, model_json, request, parent):
        return add_provider_to_model(model, model_json, request)

    @staticmethod
    def serialize(model):
        return {
            'id': str(model.id),
            'slug': model.slug,
            'name': model.name,
            'provider': {
                'id': str(model.provider.id),
                'slug': model.provider.slug,
                'name': model.provider.name
            }
        }


class CollectorTypeView(ResourceView):
    model = CollectorType

    schema = {
        "$schema": "http://json-schema.org/schema#",
        "type": "object",
        "properties": {
            "slug": {
                "type": "string"
            },
            "name": {
                "type": "string"
            },
            "provider_id": {
                "type": "string",
                "format": "uuid"
            },
            "entry_point": {
                "type": "string"
            },
            "query_schema": {
                "type": "object"
            },
            "options_schema": {
                "type": "object"
            }
        },
        "required": ["name", "slug", "provider_id", "entry_point"],
        "additionalProperties": False,
    }

    id_fields = {
        'id': UUID_RE_STRING,
        'slug': '[\w-]+',
    }
    list_filters = {
        "name": "name__iexact"
    }

    def update_model(self, model, model_json, request, parent):
        return add_provider_to_model(model, model_json, request)

    @staticmethod
    def serialize(model):
        return {
            'id': str(model.id),
            'slug': model.slug,
            'name': model.name,
            'entry_point': model.entry_point,
            'query_schema': model.query_schema,
            'options_schema': model.options_schema,
            'provider': {
                'id': str(model.provider.id),
                'slug': model.provider.slug,
                'name': model.provider.name
            }
        }


class CollectorView(ResourceView):
    model = Collector

    schema = {
        "$schema": "http://json-schema.org/schema#",
        "type": "object",
        "properties": {
            "slug": {
                "type": "string"
            },
            "type_id": {
                "type": "string",
                "format": "uuid"
            },
            "data_source_id": {
                "type": "string",
                "format": "uuid"
            },
            "data_set": {
                "type": "object"
            },
            "query": {
                "type": "object"
            },
            "options": {
                "type": "object"
            }
        },
        "required": ["slug", "type_id", "data_source_id", "data_set"],
        "additionalProperties": False,
    }

    id_fields = {
        'id': UUID_RE_STRING,
        'slug': '[\w-]+',
    }
    list_filters = {
        "name": "name__iexact"
    }

    def update_model(self, model, model_json, request, parent):
        try:
            collector_type = CollectorType.objects.get(
                id=model_json['type_id'])
            data_source = DataSource.objects.get(
                id=model_json['data_source_id'])
            data_set = DataSet.objects.get(
                data_group__name=model_json['data_set']['data_group'],
                data_type__name=model_json['data_set']['data_type'])
            model_json['type'] = collector_type
            model_json['data_source'] = data_source
            model_json['data_set'] = data_set

            add_items_to_model(model, model_json)
        except CollectorType.DoesNotExist:
            message = "No collector type with id '{}' found".format(
                model_json['type_id'])
            return create_http_error(400, message, request, logger=logger)
        except DataSource.DoesNotExist:
            message = "No data source with id '{}' found".format(
                model_json['data_source_id'])
            return create_http_error(400, message, request, logger=logger)
        except DataSet.DoesNotExist:
            message = "No data set with data group '{}' and data type '{}' " \
                      "found".format(model_json['data_set']['data_group'],
                                     model_json['data_set']['data_type'])
            return create_http_error(400, message, request, logger=logger)

    @staticmethod
    def serialize(model):
        return {
            'id': str(model.id),
            'slug': model.slug,
            'name': model.name,
            'query': model.query,
            'options': model.options,
            'entry_point': model.type.entry_point,
            'type': {
                'id': str(model.type.id),
                'slug': model.type.slug,
                'name': model.type.name
            },
            'data_source': {
                'id': str(model.data_source.id),
                'slug': model.data_source.slug,
                'name': model.data_source.name
            },
            'data_set': {
                'data_type': model.data_set.data_type.name,
                'data_group': model.data_set.data_group.name,
                'bearer_token': model.data_set.bearer_token
            },
            'provider': {
                'id': str(model.type.provider.id),
                'slug': model.type.provider.slug,
                'name': model.type.provider.name
            }
        }


@csrf_exempt
@permission_required(set(['collector', 'admin']))
def run_collector(user, request, slug):
    start_at = request.GET.get('start_at', None)
    end_at = request.GET.get('end_at', None)
    collector = get_object_or_404(Collector, slug=slug)

    if user_missing_model_permission(user, collector):
        return create_http_error(404, 'Not Found', request)

    if xor(bool(start_at), bool(end_at)):
        message = 'You must either specify a both start date and an end ' \
                  'date for the collector run, or neither'
        return create_http_error(400, message, request)
    elif start_at and end_at:
        run_collector_task.delay(slug, start_at, end_at)
    else:
        run_collector_task.delay(slug)
    return HttpResponse('', content_type='application/json')
