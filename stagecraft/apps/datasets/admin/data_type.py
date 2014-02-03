from __future__ import unicode_literals
from django.contrib import admin
from stagecraft.apps.datasets.models.data_type import DataType


class DataTypeAdmin(admin.ModelAdmin):
    pass

admin.site.register(DataType, DataTypeAdmin)
