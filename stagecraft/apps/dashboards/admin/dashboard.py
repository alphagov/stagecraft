from __future__ import unicode_literals
from django.contrib import admin
from stagecraft.apps.dashboards.models import Dashboard, Link


class DashboardAdmin(admin.ModelAdmin):
    list_display = ('title',)
    ordering = ('title',)
    fields = ('title', 'owners')
    readonly_fields = ('title',)
    filter_horizontal = ('owners',)
    search_fields = ['title']

admin.site.register(Dashboard, DashboardAdmin)


class LinkAdmin(admin.ModelAdmin):
    list_display = ('title', 'link_url', 'link_type', 'dashboard')
    ordering = ('title',)
    fields = ('title', 'url', 'link_type', 'dashboard',)
    search_fields = ['title']

admin.site.register(Link, LinkAdmin)
