from django.contrib import admin

from stagecraft.apps.transforms.models import TransformType, Transform


class TransformTypeAdmin(admin.ModelAdmin):
    list_display = ('name',)


class TransformAdmin(admin.ModelAdmin):
    list_display = ('input_type', 'output_type',)


admin.site.register(TransformType, TransformTypeAdmin)
admin.site.register(Transform, TransformAdmin)
