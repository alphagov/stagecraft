from __future__ import unicode_literals

import logging

from reversion.admin import VersionAdmin

logger = logging.getLogger(__name__)

from django.contrib import admin, messages
from django.conf import settings
from django.core.urlresolvers import reverse
from django.shortcuts import redirect

from stagecraft.apps.datasets.models.data_set import DataSet
from performanceplatform.client.data_set import DataSet as DataSetClient

class DataSetAdmin(VersionAdmin):

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

    DO_NOT_DELETE = ('transactional_services_summaries', )

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

    def has_delete_permission(self, request, obj=None):
        if obj:
            if obj in self.DO_NOT_DELETE:
                return False
            data_set = DataSet.objects.get(name=obj)
            for m in data_set.modules:
                if m.dashboard.published:
                    return False
            return True
        return super(DataSetAdmin, self).has_delete_permission(request, obj)

    def response_change(self, request, model):
        if '_empty_dataset' in request.POST:
            if '_confirmed' in request.POST:
                client = DataSetClient.from_group_and_type(
                    settings.BACKDROP_WRITE_URL + '/data',
                    model.data_group.name,
                    model.data_type.name,
                    token=model.bearer_token,
                )
                client.empty_data_set()
                self.message_user(request, 'Dataset emptied')
            else:
                self.message_user(request, message='Check \"Confirm\" to empty dataset!', level=messages.ERROR)

            return redirect(
                reverse('admin:{}_{}_change'.format(model._meta.app_label, model._meta.model_name), args=[model.pk])
            )
        else:
            return super(DataSetAdmin, self).response_change(request, model)

    def render_change_form(self, request, context, *args, **kwargs):
        if kwargs['obj']:
            dashboard_titles = []

            data_set = DataSet.objects.get(name=kwargs['obj'])
            if data_set.name in self.DO_NOT_DELETE:
                dashboard_titles.append(
                    'This dashboard should never be deleted.')
            else:
                for m in data_set.modules:
                    if m.dashboard.published:
                        dashboard_titles.append(m.dashboard.title)

            extra = {
                'dashboard_titles': sorted(set(dashboard_titles))
            }

            context.update(extra)
        return super(DataSetAdmin, self).render_change_form(
            request, context, *args, **kwargs)

    change_form_template = 'data_set/change_form.html'

    readonly_after_created = set(['name', 'data_group', 'data_type'])
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
