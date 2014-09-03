import logging
import jsonschema

from django.core.validators import RegexValidator
from django.db import models

from dbarray import CharArrayField
from jsonfield import JSONField
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
    info = CharArrayField(max_length=255)

    options = JSONField()
    query_parameters = JSONField(null=True)

    def validate_options(self):
        logging.info(self.type.schema)
        logging.info(self.options)

        jsonschema.validate(self.options, self.type.schema)
        return True

    def validate_query_parameters(self):
        try:
            jsonschema.validate(self.query_parameters, query_param_schema)
        except Exception as err:
            logging.info(err)
            raise err
        return True

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
