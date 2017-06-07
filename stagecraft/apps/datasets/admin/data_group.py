from __future__ import unicode_literals

from django.contrib import admin
from reversion.admin import VersionAdmin

from stagecraft.apps.datasets.models.data_group import DataGroup
from stagecraft.apps.datasets.models.data_set import DataSet


class DataSetInline(admin.StackedInline):
    model = DataSet
    fields = ('name', 'data_type',)
    readonly_fields = ('name', 'data_type',)
    extra = 0

    def has_delete_permission(self, request, obj=None):
        return False


class DataGroupAdmin(VersionAdmin):
    search_fields = ['name']
    list_display = ('name',)
    inlines = [
        DataSetInline
    ]


admin.site.register(DataGroup, DataGroupAdmin)
