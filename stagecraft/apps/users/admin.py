from __future__ import unicode_literals
from django.contrib import admin
from django.db import models
import reversion
from stagecraft.apps.users.models import User
from stagecraft.apps.datasets.models.data_set import DataSet


class DataSetInline(admin.StackedInline):
    model = DataSet
    fields = ('name',)
    extra = 0


class UserAdmin(reversion.VersionAdmin):
    search_fields = ['email']
    list_display = ('email',)
    list_per_page = 30

admin.site.register(User, UserAdmin)
