import copy
import jsonschema

from django.core.validators import RegexValidator
from django.db import models

from dbarray import TextArrayField
from jsonfield import JSONField
from jsonschema.validators import validator_for
from uuidfield import UUIDField

from stagecraft.apps.datasets.models import DataSet

from .dashboard import Dashboard


class ModuleType(models.Model):
    id = UUIDField(auto=True, primary_key=True, hyphenate=True)

    name_validator = RegexValidator(
        '^[a-z_]+$',
        message='Module type name can only contain lowercase '
                'letters, numbers or underscores',
    )
    name = models.CharField(
        max_length=25,
        unique=True,
        validators=[
            name_validator
        ]
    )

    schema = JSONField()

    class Meta:
        app_label = 'dashboards'

    def validate_schema(self):
        validator_for(self.schema).check_schema(self.schema)
        return True

    def serialize(self):
        return {
            'id': str(self.id),
            'name': self.name,
            'schema': self.schema,
        }


class Module(models.Model):
    id = UUIDField(auto=True, primary_key=True, hyphenate=True)
    type = models.ForeignKey(ModuleType)
    dashboard = models.ForeignKey(Dashboard)
    data_set = models.ForeignKey(DataSet, null=True)

    slug_validator = RegexValidator(
        '^[-a-z0-9]+$',
        message='Slug can only contain lower case letters, numbers or hyphens'
    )
    slug = models.CharField(
        max_length=60,
        validators=[
            slug_validator
        ]
    )

    title = models.CharField(max_length=60)
    description = models.CharField(max_length=200)
    info = TextArrayField()

    options = JSONField()
    query_parameters = JSONField(null=True)

    order = models.IntegerField()

    def validate_options(self):
        jsonschema.validate(self.options, self.type.schema)
        return True

    def validate_query_parameters(self):
        jsonschema.validate(self.query_parameters, query_param_schema)
        return True

    def spotlightify(self):
        out = copy.deepcopy(self.options)
        out['module-type'] = self.type.name
        out['slug'] = self.slug
        out['title'] = self.title
        out['description'] = self.description
        out['info'] = self.info

        if self.data_set is not None:
            out['data-source'] = {
                'data-group': self.data_set.data_group.name,
                'data-type': self.data_set.data_type.name,
            }

            if self.query_parameters is not None:
                out['data-source']['query-params'] = self.query_parameters

        return out

    def serialize(self):
        out = {
            'id': str(self.id),
            'type': {
                'id': str(self.type.id),
            },
            'dashboard': {
                'id': str(self.dashboard.id),
            },
            'slug': self.slug,
            'title': self.title,
            'description': self.description,
            'info': self.info,
            'options': self.options,
            'query_parameters': self.query_parameters,
        }

        if self.data_set is not None:
            out['data_set'] = {
                'id': self.data_set.id,
            }
        else:
            out['data_set'] = None

        return out

    class Meta:
        app_label = 'dashboards'
        unique_together = ('dashboard', 'slug')


query_param_schema = {
    "type": "object",
    "properties": {
        "period": {
            "type": "string",
            "enum": [
                "hour",
                "day",
                "week",
                "month",
                "quarter"
            ]
        },
        "start_at": {
            "type": "string",
        },
        "end_at": {
            "type": "string",
        },
        "duration": {
            "type": "integer",
        },
        "sort_by": {
            "type": "string",
        },
        "group_by": {
            "oneOf": [
                {
                    "type": "string",
                },
                {
                    "type": "array",
                    "items": {
                        "type": "string"
                    }
                }
            ]
        },
        "collect": {
            "type": "array",
            "items": {
                "type": "string",
                "pattern": ":(sum|mean|set)$"
            }
        },
        "filter_by": {
            "type": "array",
            "items": {
                "type": "string"
            }
        }
    }
}
