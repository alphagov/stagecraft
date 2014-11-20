import copy
import jsonschema
from jsonschema import Draft3Validator

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

    # should run on normal validate
    def validate_schema(self):
        validator_for(self.schema, Draft3Validator).check_schema(self.schema)
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
    data_set = models.ForeignKey(DataSet, null=True, blank=True)
    parent = models.ForeignKey("self", null=True, blank=True)

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
    description = models.CharField(max_length=200, blank=True)
    info = TextArrayField(blank=True)

    options = JSONField(blank=True)
    query_parameters = JSONField(null=True, blank=True)

    order = models.IntegerField()

    # should run on normal validate
    def validate_options(self):
        jsonschema.validate(self.options, self.type.schema)
        return True

    # should run on normal validate
    def validate_query_parameters(self):
        jsonschema.validate(self.query_parameters, query_param_schema)
        return True

    # Override to perform custom validation
    def clean(self, *args, **kwargs):
        """
        Part of the interface used by the Admin UI to validate fields - see
        the docs for calling function full_clean() at
        https://docs.djangoproject.com/en/1.7/ref/models/instances/#django.db.models.Model.full_clean

        We define our own validation in here.
        """
        # Ensure that any group_by query parameters use a list rather than
        # scalar value
        if self.query_parameters:
            group_by = self.query_parameters.get('group_by')
            if group_by and type(group_by) is not list:
                self.query_parameters['group_by'] = [group_by]
                self.validate_query_parameters()

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
            out['data_group'] = self.data_set.data_group.name
            out['data_type'] = self.data_set.data_type.name
        else:
            out['data_set'] = None

        if self.parent is not None:
            out['parent'] = {
                'id': str(self.parent.id)
            }
        else:
            out['parent'] = None

        out['modules'] = []
        if self.module_set.exists():
            for module in self.module_set.all().order_by('order'):
                out['modules'].append(module.serialize())

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
                "pattern": ":(sum|mean|set|count)$"
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
