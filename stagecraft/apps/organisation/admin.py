from django.contrib import admin

from .models import NodeType, Node


class NodeTypeAdmin(admin.ModelAdmin):
    list_display = ('name',)


class NodeAdmin(admin.ModelAdmin):
    list_display = ('name', 'abbreviation',)


admin.site.register(NodeType, NodeTypeAdmin)
admin.site.register(Node, NodeAdmin)
