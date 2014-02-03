from __future__ import unicode_literals
from django.contrib import admin
from stagecraft.apps.datasets.models.data_group import DataGroup


class DataGroupAdmin(admin.ModelAdmin):
    pass

admin.site.register(DataGroup, DataGroupAdmin)
