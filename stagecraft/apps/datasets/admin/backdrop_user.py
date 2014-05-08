from __future__ import unicode_literals
from django.contrib import admin
# from django.db import models
import reversion
from stagecraft.apps.datasets.models.backdrop_user import BackdropUser


class BackdropUserAdmin(reversion.VersionAdmin):
    search_fields = ['email']
    list_display = ('email')

admin.site.register(BackdropUser)
