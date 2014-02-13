from __future__ import unicode_literals

from collections import OrderedDict

from django.utils.encoding import python_2_unicode_compatible
from django.db import models
from django.db import transaction

from stagecraft.apps.datasets.models.data_group import DataGroup
from stagecraft.apps.datasets.models.data_type import DataType

from stagecraft.libs.backdrop_client import create_dataset, BackdropError


@python_2_unicode_compatible
class DataSet(models.Model):
    name = models.SlugField(max_length=50, unique=True)
    data_group = models.ForeignKey(DataGroup)
    data_type = models.ForeignKey(DataType)
    raw_queries_allowed = models.BooleanField(default=True)
    bearer_token = models.CharField(max_length=255, blank=True)
    upload_format = models.CharField(max_length=255, blank=True)
    upload_filters = models.TextField(blank=True)  # a comma delimited list
    auto_ids = models.TextField(blank=True)  # a comma delimited list
    queryable = models.BooleanField(default=True)
    realtime = models.BooleanField(default=False)
    capped_size = models.PositiveIntegerField(null=True, blank=True,
                                              default=None)
    max_age_expected = models.PositiveIntegerField(null=True, blank=True,
                                                   default=60 * 60 * 24)

    def __str__(self):
        return "DataSet({})".format(self.name)

    def serialize(self):
        return OrderedDict([
            ('name',                self.name),
            ('data_group',          self.data_group.name),
            ('data_type',           self.data_type.name),
            ('raw_queries_allowed', self.raw_queries_allowed),
            ('bearer_token',        self.bearer_token),
            ('upload_format',       self.upload_format),
            ('upload_filters',      self.upload_filters),
            ('auto_ids',            self.auto_ids),
            ('queryable',           self.queryable),
            ('realtime',            self.realtime),
            ('capped_size',         self.capped_size),
            ('max_age_expected',    self.max_age_expected),
        ])

    @transaction.atomic
    def save(self, *args, **kwargs):
        super(DataSet, self).save(*args, **kwargs)
        size_bytes = self.capped_size if self.is_capped else 0
        # Backdrop can't be rolled back dude.
        # Ensure this is the final action of the save method.
        create_dataset(self.name, size_bytes)

    @property
    def is_capped(self):
        # Actually mongo's limit for cap size minimum is currently 4096 :-(
        return (self.capped_size is not None
                and self.capped_size > 0)

    class Meta:
        app_label = 'datasets'
        unique_together = ['data_group', 'data_type']
