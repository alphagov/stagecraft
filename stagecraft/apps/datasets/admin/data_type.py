from __future__ import unicode_literals

from django.contrib import admin
from reversion.admin import VersionAdmin

from stagecraft.apps.datasets.models.data_set import DataSet
from stagecraft.apps.datasets.models.data_type import DataType


class DataSetInline(admin.StackedInline):
    model = DataSet
    fields = ('name', 'data_group',)
    readonly_fields = ('name', 'data_group',)
    extra = 0

    def has_delete_permission(self, request, obj=None):
        return False


class DataTypeAdmin(VersionAdmin):
    search_fields = ['name']
    list_display = ('name',)
    inlines = [
        DataSetInline
    ]


admin.site.register(DataType, DataTypeAdmin)
