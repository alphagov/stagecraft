from __future__ import unicode_literals

from django.db import models
from django.utils.encoding import python_2_unicode_compatible

from ..helpers.validators import data_type_name_validator


@python_2_unicode_compatible
class DataType(models.Model):
    name = models.SlugField(max_length=60, unique=True,
                            validators=[data_type_name_validator])
    description = models.TextField(blank=True)

    def __str__(self):
        return "{}".format(self.name)

    class Meta:
        app_label = 'datasets'
        ordering = ['name']
