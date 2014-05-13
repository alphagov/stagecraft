from __future__ import unicode_literals
from django.contrib import admin
from django.db import models
import reversion
from stagecraft.apps.datasets.models.backdrop_user import BackdropUser
from stagecraft.apps.datasets.models.data_set import DataSet


class DataSetInline(admin.StackedInline):
    model = DataSet
    fields = ('name',)
    extra = 0


class BackdropUserAdmin(reversion.VersionAdmin):
    search_fields = ['email', 'data_sets']
    list_display = ('email', 'numer_of_datasets_user_has_access_to',)
    list_per_page = 30

    def queryset(self, request):
        return BackdropUser.objects.annotate(
            dataset_count=models.Count('data_sets')
        )

    def numer_of_datasets_user_has_access_to(self, obj):
        return obj.dataset_count

    numer_of_datasets_user_has_access_to.admin_order_field = 'dataset_count'


admin.site.register(BackdropUser, BackdropUserAdmin)
