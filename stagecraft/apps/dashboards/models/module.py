from __future__ import unicode_literals
import copy
import jsonschema
import uuid
from jsonschema import Draft3Validator, SchemaError

from django.core.validators import RegexValidator
from django.db import models

from dbarray import TextArrayField
from jsonfield import JSONField

from stagecraft.apps.datasets.models import DataSet

from .dashboard import Dashboard


class ModuleManager(models.Manager):

    def get_queryset(self):
        return super(ModuleManager, self).get_queryset().select_related(
            'data_set__data_group', 'data_set__data_type',
            'type')

    def for_user(self, user):
        return self.get_queryset().filter(dashboard__owners=user)


class ModuleType(models.Model):
    id = models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True)

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

    schema = JSONField(default={})

    class Meta:
        app_label = 'dashboards'

    # should run on normal validate
    def validate(self):
        try:
            Draft3Validator.check_schema(self.schema)
        except SchemaError as err:
            return 'schema is invalid: {}'.format(err)

        return None

    def serialize(self):
        return {
            'id': str(self.id),
            'name': self.name,
            'schema': self.schema,
        }


class Module(models.Model):
    id = models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True)
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

    options = JSONField(blank=True, default={})
    query_parameters = JSONField(null=True, blank=True)

    order = models.IntegerField()

    objects = ModuleManager()

    def _get_owners(self):
        return self.dashboard.owners

    owners = property(_get_owners)

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
        def listify_group_by(query_parameters):
            group_by = query_parameters.get('group_by')
            if group_by and type(group_by) is not list:
                query_parameters['group_by'] = [group_by]
                return True
            return False

        # group_by can be part of query_parameters
        if self.query_parameters:
            if listify_group_by(self.query_parameters):
                self.validate_query_parameters()

        # group_by can be part of query_parameters in tabs
        if self.options:
            tabs = self.options.get('tabs')
            if tabs:
                for tab in tabs:
                    query_parameters = tab.get('data-source',
                                               {}).get('query-params', {})
                    if query_parameters:
                        listify_group_by(query_parameters)
            self.validate_options()

    def _parent_id_as_dict(self):
        if self.parent is not None:
            return {'id': str(self.parent.id)}
        else:
            return None

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

        out['modules'] = [
            m.spotlightify() for m in self.module_set.all().order_by('order')]

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

        out['parent'] = self._parent_id_as_dict()

        out['modules'] = [
            m.serialize() for m in self.module_set.all().order_by('order')]

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
