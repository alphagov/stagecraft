from __future__ import unicode_literals
from django.utils.encoding import python_2_unicode_compatible
from django.db import models

from stagecraft.apps.datasets.models.data_group import DataGroup
from stagecraft.apps.datasets.models.data_type import DataType


@python_2_unicode_compatible
class DataSet(models.Model):
    # used in save() below and by DataSetAdmin
    READONLY_FIELDS = set(['name', 'capped_size'])

    name = models.SlugField(max_length=50, unique=True)
    data_group = models.ForeignKey(DataGroup, on_delete=models.PROTECT)
    data_type = models.ForeignKey(DataType, on_delete=models.PROTECT)
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

    def save(self, *args, **kwargs):
        if self.pk is not None:  # record already exists
            old = DataSet.objects.get(pk=self.pk).__dict__
            new = self.__dict__
            bad_fields = [i for i in READONLY_FIELDS if new[i] != old[i]]
            if len(bad_fields) > 0:
                bad_fields_csv = ', '.join(bad_fields)
                raise Exception('{} cannot be modified'.format(bad_fields_csv))
        super(DataSet, self).save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        raise Exception("Data Sets cannot be deleted")

    class Meta:
        app_label = 'datasets'
        unique_together = ['data_group', 'data_type']
