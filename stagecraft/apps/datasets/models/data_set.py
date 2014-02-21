from __future__ import unicode_literals

from collections import OrderedDict

from django.core.exceptions import ValidationError
from django.db import models
from django.db import transaction

from django.utils.encoding import python_2_unicode_compatible

from stagecraft.apps.datasets.models.data_group import DataGroup
from stagecraft.apps.datasets.models.data_type import DataType

from stagecraft.libs.backdrop_client import create_dataset


class DeleteNotImplementedError(NotImplementedError):
    pass


class ImmutableFieldError(ValidationError):
    pass


@python_2_unicode_compatible
class DataSet(models.Model):
    # used in clean() below and by DataSetAdmin
    READONLY_FIELDS = set(['name', 'capped_size'])

    name = models.SlugField(max_length=50, unique=True)
    data_group = models.ForeignKey(DataGroup, on_delete=models.PROTECT)
    data_type = models.ForeignKey(DataType, on_delete=models.PROTECT)
    raw_queries_allowed = models.BooleanField(default=True)
    bearer_token = models.CharField(max_length=255, blank=False, null=True)
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

    def clean(self, *args, **kwargs):
        """
        Part of the interface used by the Admin UI to validate fields - see
        the docs for calling function full_clean()

        We define our own validation in here to ensure that fields we consider
        "read only" can only be set (on creation)

        Raise a ImmutableFieldError if a read only field has been modified.
        """
        super(DataSet, self).clean(*args, **kwargs)

        existing = self._get_existing()

        if existing is not None:
            previous_values = {k: existing.__dict__[k]
                               for k in self.READONLY_FIELDS}
            bad_fields = [v for v in self.READONLY_FIELDS
                          if previous_values != getattr(self, v)]

            if len(bad_fields) > 0:
                bad_fields_csv = ', '.join(bad_fields)
                raise ImmutableFieldError('{} cannot be modified'
                                          .format(bad_fields_csv))

    def _get_existing(self):
        if self.pk is not None:
            return DataSet.objects.get(pk=self.pk)

    @transaction.atomic
    def save(self, *args, **kwargs):
        self.clean()
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

    def delete(self, *args, **kwargs):
        raise DeleteNotImplementedError("Data Sets cannot be deleted")

    class Meta:
        app_label = 'datasets'
        unique_together = ['data_group', 'data_type']
