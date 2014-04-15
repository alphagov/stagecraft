from __future__ import unicode_literals
from django.contrib import admin
from django.db import models
import reversion
from stagecraft.apps.datasets.models.data_type import DataType
from stagecraft.apps.datasets.models.data_set import DataSet


class DataSetInline(admin.StackedInline):
    model = DataSet
    fields = ('name', 'data_group',)
    readonly_fields = ('name', 'data_group',)
    extra = 0

    def has_delete_permission(self, request, obj=None):
        return False


class DataTypeAdmin(reversion.VersionAdmin):
    search_fields = ['name']
    list_display = ('name', 'number_of_datasets',)
    inlines = [
        DataSetInline
    ]

    def queryset(self, request):
        qs = super(DataTypeAdmin, self).queryset(request)
        qs = qs.annotate(models.Count('dataset'))
        return qs

    def number_of_datasets(self, obj):
        return obj.dataset__count

    number_of_datasets.admin_order_field = 'dataset__count'

admin.site.register(DataType, DataTypeAdmin)
