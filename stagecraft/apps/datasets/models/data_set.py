from __future__ import unicode_literals

from collections import OrderedDict

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.db import transaction
from django.db.models.query import QuerySet

from django.utils.encoding import python_2_unicode_compatible

from .data_group import DataGroup
from .data_type import DataType

from stagecraft.libs.backdrop_client import (delete_data_set,
                                             BackdropNotFoundError)
from stagecraft.libs.schemas import get_schema

from ..helpers.validators import data_set_name_validator

import reversion
import logging


def generate_data_set_name(data_group_name, data_type_name):
    return '_'.join((data_group_name,
                     data_type_name)).replace('-', '_')


class ImmutableFieldError(ValidationError):
    pass


class DataSetQuerySet(QuerySet):

    def delete(self):
        for record in self.all():
            record.delete()


class DataSetManager(models.Manager):

    def get_query_set(self):
        return DataSetQuerySet(self.model, using=self._db)


@python_2_unicode_compatible
class DataSet(models.Model):
    # used in clean() below to prevent ORM model changes like
    # e.g. modifying a name after the data_set has been created
    READONLY_AFTER_CREATED = set(
        ['name', 'capped_size'])

    objects = DataSetManager()

    name = models.SlugField(
        blank=True,
        max_length=200, unique=True,
        validators=[data_set_name_validator],
        help_text="""
        This will be automatically generated to use the
        format 'data_group_data_type'
        e.g. `carers_allowance_customer_satisfaction`
        """
    )
    created = models.DateTimeField(auto_now_add=True,
                                   verbose_name='created (UTC)')
    modified = models.DateTimeField(auto_now=True,
                                    verbose_name='modified (UTC)')
    owners = models.ManyToManyField('users.User')
    data_group = models.ForeignKey(
        DataGroup,
        on_delete=models.PROTECT,
        help_text="""
        - Normally this will be the name of the service<br/>
        - e.g. 'carers-allowance'<br/>
        - Add a data group first if it doesn't already exist</br>
        (This should match the slug on GOV.UK when possible)</br>
        - Use hyphens to separate words.
        """
    )
    data_type = models.ForeignKey(
        DataType,
        on_delete=models.PROTECT,
        help_text="""
        The type of data this data-set will be collecting.
        e.g. 'customer-satisfaction' </br>
        - Use hyphens to separate words.
        """
    )

    raw_queries_allowed = models.BooleanField(default=True, editable=False)
    bearer_token = models.CharField(
        max_length=255, blank=True, null=False,
        default="",
        help_text="""
        - If it's for an internal collector or customer-satisfaction,
        copy the token from another data-set of the same data type.<br/>
        - If it's for a new type then copy from a data-set of the same
        collector, or from a content data-set in the case of new content
        data-sets. (If you're not sure what this means ask a developer).<br/>
        - Otherwise, generate a new token with the link provided.
        """
    )
    upload_format = models.CharField(
        max_length=255, blank=True,
        help_text="""
        [OPTIONAL FIELD] Only fill in this field if
        data is being uploaded via the admin app.</br>
        - Write 'excel' or 'csv'
        """
    )
    upload_filters = models.TextField(
        blank=True,
        help_text="""
        A comma separated list of filters.
        If users manually upload CSV files you can leave this blank.<br/>
        If users manually upload Excel files with the data in the first
        sheet (a common scenario) this should be
        "backdrop.core.upload.filters.first_sheet_filter".<br/>
        Other possible values are:
        "backdrop.contrib.evl_upload_filters.ceg_volumes",
        "backdrop.contrib.evl_upload_filters.channel_volumetrics",
        "backdrop.contrib.evl_upload_filters.customer_satisfaction",
        "backdrop.contrib.evl_upload_filters.service_failures",
        "backdrop.contrib.evl_upload_filters.service_volumetrics" and
        "backdrop.contrib.evl_upload_filters.volumetrics"
        """
    )  # a comma delimited list
    auto_ids = models.TextField(
        blank=True,
        help_text="""
        [OPTIONAL FIELD] If you're doing a CSV or Excel upload, and the data
        may be cumulative, you should complete this field to avoid the risk of
        duplicate records.</br>
        Write a comma separated list of fields to turn into a unique id, eg:
        <code>_timestamp,service,channel</code></br>
        This should list every field name that, when combined, could identify a
        unique record. If this is left blank Backdrop won't be able to identify
        duplicate records which will result in double counting.
        """
    )  # a comma delimited list
    queryable = models.BooleanField(
        default=True,
        help_text="""
        Leave this ticked unless told otherwise.
        """
    )
    realtime = models.BooleanField(
        default=False,
        help_text="""
        Tick this box if this data-set is collecting realtime data.
        e.g. current visitor counts
        """
    )
    capped_size = models.PositiveIntegerField(
        null=True, blank=True,
        default=None,
        help_text="""
        [OPTIONAL FIELD] Only fill this in if the data-set is realtime.<br/>
        Set this to 4194304 (4mb), which gives us just over two weeks of data.
        """
    )
    max_age_expected = models.PositiveIntegerField(
        null=True, blank=True,
        default=60 * 60 * 24,
        help_text="""
        [OPTIONAL FIELD] How often do you expect the data to be updated?
        (<strong>in seconds</strong>)<br/>
        This is used for monitoring so we can tell when data hasn't been
        updated. If this is left blank the data-set will not be monitored.<br/>
        Commonly used values are:<br/>
        - <strong>360</strong> (every 5 minutes)<br/>
        - <strong>9000</strong> (for hourly data)<br/>
        - <strong>180000</strong> (for daily data)<br/>
        - <strong>1300000</strong> (for weekly data)<br/>
        - <strong>5200000</strong> (for monthly data)<br/>
        - <strong>15600000</strong> (for quarterly data)<br/>
        You can choose your own value if the ones above don't work for your
        case.
        """
    )
    published = models.BooleanField(
        default=False,
        help_text="""
        Set to published if this data-set should be publicly available
        """
    )

    def __str__(self):
        return "{}".format(self.name)

    def data_location(self):
        path = '{backdrop_url}/data/{data_group}/{data_type}'.format(
            backdrop_url=settings.BACKDROP_URL,
            data_group=self.data_group,
            data_type=self.data_type)
        return '<a href="{0}?limit=10">{0}</a>'.format(path)
    data_location.allow_tags = True

    def serialize(self):
        def make_list(string):
            return [x.strip() for x in string.split(',')] if string else []

        token_or_null = self.bearer_token

        upload_filters_list = make_list(self.upload_filters)
        auto_ids_list = make_list(self.auto_ids)

        return OrderedDict([
            ('name',                self.name),
            ('data_group',          self.data_group.name),
            ('data_type',           self.data_type.name),
            ('raw_queries_allowed', self.raw_queries_allowed),
            ('bearer_token',        token_or_null),
            ('upload_format',       self.upload_format),
            ('upload_filters',      upload_filters_list),
            ('auto_ids',            auto_ids_list),
            ('queryable',           self.queryable),
            ('realtime',            self.realtime),
            ('capped_size',         self.capped_size),
            ('max_age_expected',    self.max_age_expected),
            ('published',           self.published),
            ('schema',              get_schema(
                self.data_group.name, self.data_type.name)),
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
                               for k in self.READONLY_AFTER_CREATED}
            bad_fields = [v for v in self.READONLY_AFTER_CREATED
                          if previous_values[v] != getattr(self, v)]

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
        is_new = self.pk is None
        if is_new:
            self.name = self.generate_data_set_name()
        super(DataSet, self).save(*args, **kwargs)

    def generate_data_set_name(self):
        return generate_data_set_name(
            self.data_group.name,
            self.data_type.name)

    @property
    def is_capped(self):
        # Actually mongo's limit for cap size minimum is currently 4096 :-(
        return (self.capped_size is not None
                and self.capped_size > 0)

    def delete(self, *args, **kwargs):
        try:
            delete_data_set(self.name)
        except BackdropNotFoundError:
            # if the dataset doesn't exist in backdrop, safe to delete it from
            # stagecraft
            logger = logging.getLogger(__name__)
            logger.warning(
                'Deleting data_set {} that doesnt exist in backdrop'.format(
                    self.name
                )
            )
        super(DataSet, self).delete(*args, **kwargs)

    class Meta:
        app_label = 'datasets'
        unique_together = ['data_group', 'data_type']
        ordering = ['name']

reversion.register(DataSet)
