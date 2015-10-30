from django.contrib import admin

from .models import NodeType, Node


class NodeTypeAdmin(admin.ModelAdmin):
    list_display = ('name',)


class ParentInline(admin.TabularInline):
    model = Node.parents.through
    verbose_name = 'Parent relationship'
    verbose_name_plural = 'Parents'
    extra = 1
    fk_name = 'from_node'


class NodeAdmin(admin.ModelAdmin):
    list_display = ('name', 'abbreviation', 'typeOf',)
    list_filter = ('typeOf',)
    search_fields = ('name', 'abbreviation',)
    inlines = (ParentInline,)
    exclude = ('parents',)
    ordering = ('name', )


admin.site.register(NodeType, NodeTypeAdmin)
admin.site.register(Node, NodeAdmin)
