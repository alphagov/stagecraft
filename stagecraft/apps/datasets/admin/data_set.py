from __future__ import unicode_literals

import logging
logger = logging.getLogger(__name__)

from django.contrib import admin

import reversion

from django.conf import settings
from django.core.urlresolvers import reverse
from django.shortcuts import redirect
from performanceplatform.client.data_set import DataSet as DataSetClient

from stagecraft.apps.datasets.models.data_set import DataSet


class DataSetAdmin(reversion.VersionAdmin):

    """
    All methods in this class are overriding VersionAdmin methods
    See http://stackoverflow.com/a/20450852

    `log_change` and `log_addition` methods:
      - are used by VersionAdmin to create revision
      - we are overriding here to stop a revision if the model fails to save

    `response_add` and `response_change` methods:
      - by default in the base class they generate a success message
      - we are overriding here to generate a different message
        if the model fails to save

    """

    actions = None

    class Media:
        css = {
            "all": ("admin/css/datasets.css",),
        }
        js = ("admin/js/datasets.js",)

    # Get fields that are only editable on creation
    def get_readonly_fields(self, request, obj=None):
        if obj:  # record already exists
            return self.readonly_after_created
        else:
            return self.readonly_fields

    def response_change(self, request, model):
        if '_empty_dataset' in request.POST:
            client = DataSetClient.from_group_and_type(
                settings.BACKDROP_WRITE_URL + '/data',
                model.data_group.name,
                model.data_type.name,
                token=model.bearer_token,
            )
            client.empty_data_set()
            return redirect(reverse(
                'admin:{}_{}_change'.format(
                    model._meta.app_label, model._meta.model_name
                ), args=[model.pk]))
        else:
            return super(DataSetAdmin, self).response_change(request, model)

    change_form_template = 'data_set/change_form.html'

    readonly_after_created = set(
        ['name', 'data_group', 'data_type', 'capped_size'])
    readonly_fields = ('name', )
    search_fields = ['name']
    list_display = ('name', 'data_group', 'data_type', 'data_location',
                    'created', 'modified', 'published')
    filter_horizontal = ('owners',)

    fields = (
        'data_group',
        'data_type',
        'name',
        'published',
        'bearer_token',
        'upload_format',
        'upload_filters',
        'auto_ids',
        'queryable',
        'realtime',
        'capped_size',
        'max_age_expected',
        'owners'
    )

admin.site.register(DataSet, DataSetAdmin)
