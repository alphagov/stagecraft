from __future__ import unicode_literals
from django.utils.encoding import python_2_unicode_compatible
from django.db import models
from stagecraft.apps.datasets.models import DataSet
from collections import OrderedDict

import reversion


@python_2_unicode_compatible
class User(models.Model):

    email = models.EmailField(
        max_length=254,
        unique=True,
        help_text=""""""
    )

    data_sets = models.ManyToManyField(DataSet, blank=True)

    def serialize(self):
        def get_names(data_sets):
            return [data_set.name for data_set in data_sets]

        return OrderedDict([
            ('email',     self.email),
            ('data_sets', get_names(self.data_sets.all()))
        ])

    def api_object(self):
        """
        Just the parts of a user object we would want to return
        """
        return {
            'email': self.email
        }

    def __str__(self):
        return "{}".format(self.email)

    class Meta:
        app_label = 'users'
        ordering = ['email']


reversion.register(User)
