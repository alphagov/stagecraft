from __future__ import unicode_literals
from django.contrib import admin
import reversion
from stagecraft.apps.datasets.models.data_set import DataSet


class DataSetAdmin(reversion.VersionAdmin):
    pass

admin.site.register(DataSet, DataSetAdmin)
