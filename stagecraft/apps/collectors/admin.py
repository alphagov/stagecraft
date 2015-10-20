from operator import xor
from django import forms
from django.contrib import admin
from django.contrib.admin import widgets
from django.contrib.admin.helpers import ActionForm
from django.core.checks import messages
from django.forms import Select, ModelChoiceField, ModelForm
from django.forms.models import ModelChoiceIterator
from django.forms.fields import ChoiceField
from django.utils.encoding import force_text
from django.utils.html import format_html
from django.utils.safestring import mark_safe
from datetime import datetime

from stagecraft.apps.collectors import models
from stagecraft.apps.collectors.tasks import run_collector


class SelectWithData(Select):

    def __init__(self, attrs=None, choices=(), **kwargs):
        super(SelectWithData, self).__init__(attrs, **kwargs)
        self.choices = list(choices)

    def render_option(self, selected_choices, option_value, option_label):
        if option_value is None or option_value == '':
            option_value = ('', '')
        id = force_text(option_value[0])
        provider_id = option_value[1]
        if id in selected_choices:
            selected_html = mark_safe(' selected="selected"')
            if not self.allow_multiple_selected:
                selected_choices.remove(id)
        else:
            selected_html = ''

        return format_html('<option data-id="{}" value="{}"{}>{}</option>',
                           provider_id,
                           id,
                           selected_html,
                           force_text(option_label))


class CollectorModelChoiceIterator(ModelChoiceIterator):

    def __init__(self, field):
        self.field = field
        self.queryset = field.queryset

    def __iter__(self):
        if self.field.empty_label is not None:
            yield ("", self.field.empty_label)
        for obj in self.queryset.iterator():
            yield self.choice(obj)

    def choice(self, obj):
        return ((self.field.prepare_value(obj), obj.provider.id),
                self.field.label_from_instance(obj))


class CollectorModelChoiceField(ModelChoiceField):

    def __init__(self, *args, **kwargs):
        kwargs['widget'] = SelectWithData()
        super(CollectorModelChoiceField, self).__init__(*args, **kwargs)

    def _get_choices(self):
        if hasattr(self, '_choices'):
            return self._choices

        return CollectorModelChoiceIterator(self)

    choices = property(_get_choices, ChoiceField._set_choices)


class CollectorAdminForm(ModelForm):

    def __init__(self, *args, **kwargs):
        super(CollectorAdminForm, self).__init__(*args, **kwargs)
        self.fields['type'] = CollectorModelChoiceField(
            queryset=models.CollectorType.objects.all())
        self.fields['data_source'] = CollectorModelChoiceField(
            queryset=models.DataSource.objects.all())

    class Meta:
        model = models.Collector
        fields = '__all__'


class CollectorActionForm(ActionForm):
    start_date = forms.DateField(required=False)
    end_date = forms.DateField(required=False)


def run_now(modeladmin, request, queryset):
    start_date = request.POST['start_date']
    end_date = request.POST['end_date']

    if xor(bool(start_date), bool(end_date)):
        message = "You must either specify a both start date and an end " \
                  "date for the collector run, or neither"
        modeladmin.message_user(request, message, messages.ERROR)
    else:
        start_at = None
        end_at = None

        if start_date and end_date:
            start_at = datetime.strptime(start_date, '%Y-%m-%d')
            end_at = datetime.strptime(end_date, '%Y-%m-%d')

        for collector in queryset:
            try:
                run_collector(collector.slug, start_at=start_at, end_at=end_at)
            except SystemExit:
                message = "An exception has occurred. " \
                          "Please check you are not trying to backfill a " \
                          "realtime collector"
                modeladmin.message_user(request, message, messages.ERROR)

run_now.short_description = "Run collector"


@admin.register(models.Collector)
class CollectorAdmin(admin.ModelAdmin):

    class Media:
        js = ('admin/js/filterselect.js',)

    form = CollectorAdminForm
    action_form = CollectorActionForm
    filter_horizontal = ('owners',)
    actions = [run_now]


@admin.register(models.DataSource)
class DataSourceAdmin(admin.ModelAdmin):
    filter_horizontal = ('owners',)
