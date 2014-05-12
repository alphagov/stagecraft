from __future__ import unicode_literals
from django.utils.encoding import python_2_unicode_compatible
from django.db import models
from stagecraft.apps.datasets.models import DataSet
from collections import OrderedDict

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
        import pprint as pp

        def get_name(item):
            return item.name

        pp.pprint("HI MOM")
        pp.pprint(map(get_name, self.data_sets.all()))

        return OrderedDict([
            ('email',     self.email),
            ('data_sets', map(get_name, self.data_sets.all()))
        ])

    def __str__(self):
        return "{}".format(self.email)

    class Meta:
        app_label = 'datasets'
        ordering = ['email']


reversion.register(BackdropUser)
