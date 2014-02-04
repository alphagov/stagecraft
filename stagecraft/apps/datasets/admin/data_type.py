from __future__ import unicode_literals
from django.contrib import admin
import reversion
from stagecraft.apps.datasets.models.data_type import DataType


class DataTypeAdmin(reversion.VersionAdmin):
    pass

admin.site.register(DataType, DataTypeAdmin)
