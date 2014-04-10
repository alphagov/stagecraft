from __future__ import unicode_literals
from django.utils.encoding import python_2_unicode_compatible
from django.db import models


@python_2_unicode_compatible
class DataType(models.Model):
    name = models.SlugField(max_length=50, unique=True)

    def __str__(self):
        return "DataType({})".format(self.name)

    class Meta:
        app_label = 'datasets'
        ordering = ['name']
