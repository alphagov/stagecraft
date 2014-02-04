from __future__ import unicode_literals
from django.contrib import admin
import reversion
from stagecraft.apps.datasets.models.data_group import DataGroup


class DataGroupAdmin(reversion.VersionAdmin):
    pass

admin.site.register(DataGroup, DataGroupAdmin)
