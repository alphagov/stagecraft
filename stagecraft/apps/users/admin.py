from __future__ import unicode_literals
from django.contrib import admin
from django import forms
import reversion
from stagecraft.apps.users.models import User
from stagecraft.apps.datasets.models.data_set import DataSet


class DataSetInline(admin.StackedInline):
    model = DataSet
    fields = ('name',)
    extra = 0


class UserAdminForm(forms.ModelForm):
    data_sets = forms.ModelMultipleChoiceField(
        DataSet.objects.all(),
        widget=admin.widgets.FilteredSelectMultiple('Data sets', False),
        required=False,
    )

    def __init__(self, *args, **kwargs):
        super(UserAdminForm, self).__init__(*args, **kwargs)
        if self.instance.pk:
            self.initial['data_sets'] = self.instance.data_sets.values_list(
                'pk', flat=True)

    def save(self, *args, **kwargs):
        instance = super(UserAdminForm, self).save(*args, **kwargs)
        if instance.pk:
            instance.data_sets.clear()
            instance.data_sets.add(*self.cleaned_data['data_sets'])
        return instance


class UserAdmin(reversion.VersionAdmin):
    search_fields = ['email']
    list_display = ('email',)
    list_per_page = 30

    form = UserAdminForm

admin.site.register(User, UserAdmin)
