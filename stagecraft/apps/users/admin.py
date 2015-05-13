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
    list_display = ('email', 'number_of_datasets_user_has_access_to',)
    list_per_page = 30
    filter_horizontal = ('data_sets',)

    def queryset(self, request):
        return User.objects.annotate(
            dataset_count=models.Count('data_sets')
        )

    def number_of_datasets_user_has_access_to(self, obj):
        return obj.dataset_count

    number_of_datasets_user_has_access_to.admin_order_field = 'dataset_count'


admin.site.register(User, UserAdmin)
