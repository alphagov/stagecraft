from __future__ import unicode_literals
from django.utils.encoding import python_2_unicode_compatible
from django.db import models
# from django.db import transaction
from stagecraft.apps.datasets.models import DataSet

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

    def __str__(self):
        return "{}".format(self.name)

    class Meta:
        app_label = 'datasets'
        ordering = ['email']


reversion.register(BackdropUser)
