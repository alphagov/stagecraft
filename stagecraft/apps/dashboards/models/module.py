import logging
import jsonschema

from django.core.validators import RegexValidator
from django.db import models

from dbarray import CharArrayField
from jsonfield import JSONField
from uuidfield import UUIDField

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


class Module(models.Model):
    id = UUIDField(auto=True, primary_key=True, hyphenate=True)
    type = models.ForeignKey(ModuleType)
    dashboard = models.ForeignKey(Dashboard)

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

    def validate_options(self):
        logging.info(self.type.schema)
        logging.info(self.options)

        jsonschema.validate(self.options, self.type.schema)
        return True

    class Meta:
        app_label = 'dashboards'
        unique_together = ('dashboard', 'slug')
