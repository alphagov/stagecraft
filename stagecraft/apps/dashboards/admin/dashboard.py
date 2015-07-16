from __future__ import unicode_literals
from django.contrib import admin
from stagecraft.apps.dashboards.models import Dashboard


class DashboardAdmin(admin.ModelAdmin):
    list_display = ('title',)
    ordering = ('title',)
    fields = ('title', 'owners')
    readonly_fields = ('title',)
    filter_horizontal = ('owners',)

admin.site.register(Dashboard, DashboardAdmin)
