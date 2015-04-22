import logging
import jsonschema
from jsonschema import Draft3Validator, SchemaError, ValidationError

from django.core.validators import RegexValidator
from django.db import models

from jsonfield import JSONField
from uuidfield import UUIDField

from stagecraft.apps.datasets.models import DataGroup, DataType
from stagecraft.apps.dashboards.models.module import query_param_schema

logger = logging.getLogger(__name__)


class TransformType(models.Model):
    id = UUIDField(auto=True, primary_key=True, hyphenate=True)
    name = models.CharField(
        max_length=25,
        unique=True,
    )
    schema = JSONField(default={}, blank=True)

    function_validator = RegexValidator(
        '^[a-z_\.]+$',
        message='Transform function has to consist of lowercase'
                'letters, underscores or dots',
    )
    function = models.CharField(
        max_length=200,
        unique=True,
        validators=[
            function_validator
        ]
    )

    def __str__(self):
        return "{}".format(self.name)

    def validate(self):
        try:
            Draft3Validator.check_schema(self.schema)
        except SchemaError as err:
            return 'schema is invalid: {}'.format(err)

        return None


class Transform(models.Model):
    class Meta:
        unique_together = (
            'type', 'input_group', 'input_type', 'query_parameters',
            'options', 'output_group', 'output_type',
        )

    id = UUIDField(auto=True, primary_key=True, hyphenate=True)
    type = models.ForeignKey(TransformType)

    input_group = models.ForeignKey(
        DataGroup, null=True,
        blank=True, related_name='+',
    )
    input_type = models.ForeignKey(DataType, related_name='+')

    query_parameters = JSONField(default={}, blank=True)
    options = JSONField(default={}, blank=True)

    output_group = models.ForeignKey(
        DataGroup, null=True,
        blank=True, related_name='+',
    )
    output_type = models.ForeignKey(DataType, related_name='+')

    def validate(self):
        try:
            jsonschema.validate(self.query_parameters, query_param_schema)
        except ValidationError as err:
            return 'query parameters are invalid: {}'.format(err)

        try:
            jsonschema.validate(self.options, self.type.schema)
        except ValidationError as err:
            return 'options are invalid: {}'.format(err)

        return None
