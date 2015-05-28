from __future__ import unicode_literals
from django.contrib import admin
import reversion
from stagecraft.apps.dashboards.models import Dashboard


class DashboardAdmin(reversion.VersionAdmin):
    list_display = ('title',)
    ordering = ('title',)
    fields = ('title', 'owners')
    readonly_fields = ('title',)

admin.site.register(Dashboard, DashboardAdmin)
