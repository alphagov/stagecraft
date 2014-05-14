from __future__ import unicode_literals
from django.db import transaction
from django.utils.encoding import python_2_unicode_compatible
from django.db import models
from stagecraft.apps.datasets.models import DataSet
from collections import OrderedDict
from stagecraft.libs.purge_varnish import purge
from ..helpers.calculate_purge_urls import get_backdrop_user_path_queries

import reversion


@python_2_unicode_compatible
class BackdropUser(models.Model):

    """Users of backdrop admin, as opposed to Stagecraft users"""

    email = models.EmailField(
        max_length=254,
        unique=True,
        help_text=""""""
    )

    data_sets = models.ManyToManyField(DataSet)

    def serialize(self):
        def get_names(data_sets):
            return [data_set.name for data_set in data_sets]

        return OrderedDict([
            ('email',     self.email),
            ('data_sets', get_names(self.data_sets.all()))
        ])

    @transaction.atomic
    def save(self, *args, **kwargs):
        super(BackdropUser, self).save(*args, **kwargs)
        # Backdrop can't be rolled back dude.
        # Ensure this is the final action of the save method.
        purge(get_backdrop_user_path_queries(self))

    def delete(self, *args, **kwargs):
        super(BackdropUser, self).delete(*args, **kwargs)
        purge(get_backdrop_user_path_queries(self))

    def __str__(self):
        return "{}".format(self.email)

    class Meta:
        app_label = 'datasets'
        ordering = ['email']


reversion.register(BackdropUser)
