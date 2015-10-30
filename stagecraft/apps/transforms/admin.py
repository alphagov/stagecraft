from django.contrib import admin

from stagecraft.apps.transforms.models import TransformType, Transform


class TransformTypeAdmin(admin.ModelAdmin):
    list_display = ('name',)


class TransformAdmin(admin.ModelAdmin):
    list_display = (
        'input_group', 'input_type', 'output_group', 'output_type',)
    filter_horizontal = ('owners',)
    search_fields = (
        'input_group__name',
        'input_type__name',
        'output_group__name',
        'output_type__name',)
    ordering = ('input_group', 'input_type', 'output_group', 'output_type',)


admin.site.register(TransformType, TransformTypeAdmin)
admin.site.register(Transform, TransformAdmin)
