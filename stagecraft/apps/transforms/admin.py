from django.contrib import admin

from stagecraft.apps.transforms.models import TransformType, Transform


class TransformTypeAdmin(admin.ModelAdmin):
    list_display = ('name',)


class TransformAdmin(admin.ModelAdmin):
    list_display = (
        'input_group', 'input_type', 'output_group', 'output_type',)
    filter_horizontal = ('owners',)


admin.site.register(TransformType, TransformTypeAdmin)
admin.site.register(Transform, TransformAdmin)
