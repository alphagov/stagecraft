from __future__ import unicode_literals

import logging
logger = logging.getLogger(__name__)

from django.contrib import admin
from django.contrib import messages

import reversion

from stagecraft.apps.datasets.models.data_set import DataSet
from stagecraft.libs.backdrop_client import BackdropError


class DataSetAdmin(reversion.VersionAdmin):

    """
    All methods in this class are overriding VersionAdmin methods
    See http://stackoverflow.com/a/20450852

    `log_change` and `log_addition` methods:
      - are used by VersionAdmin to create revision
      - we are overriding here to stop a revision if the model fails to save

    `changelist_view` method:
      - is the view where you see a list of datasets, which you are
      redirected to after deletion and add and change, so is a good place for
      showing error messages
    """

    class Media:
        css = {
            "all": ("admin/css/datasets.css",),
        }
        js = ("admin/js/datasets.js",)

    def __init__(self, *args, **kwargs):
        super(DataSetAdmin, self).__init__(*args, **kwargs)
        self.successful_save = None
        self.exception = None

    # Get fields that are only editable on creation
    def get_readonly_fields(self, request, obj=None):
        if obj:  # record already exists
            return DataSet.READONLY_FIELDS
        else:
            return set()

    def save_model(self, request, *args, **kwargs):
        self._try_change_model(
            lambda: super(DataSetAdmin, self).save_model(
                request, *args, **kwargs))

    def delete_model(self, request, obj, *args, **kwargs):
        self._try_change_model(
            lambda: super(DataSetAdmin, self).delete_model(
                request, obj, *args, **kwargs))

    def _try_change_model(self, model_func):
        """
        If an external Backdrop exception happens when changing the model,
        store the exception for later use by the log_ methods and the
        changelist_view.
        """
        try:
            model_func()
        except BackdropError as e:
            self.successful_save = False
            logger.exception(e)
            self.exception = e
        else:
            self.successful_save = True

    def log_addition(self, *args, **kwargs):
        if self.successful_save is True:
            super(DataSetAdmin, self).log_addition(*args, **kwargs)
        else:
            logger.warning("save(..) failed, blocking log_addition(..)")

    def log_change(self, *args, **kwargs):
        if self.successful_save is True:
            super(DataSetAdmin, self).log_change(*args, **kwargs)
        else:
            logger.warning("save(..) failed, blocking log_change(..)")

    def log_deletion(self, *args, **kwargs):
        if self.successful_save is True:
            super(DataSetAdmin, self).log_deletion(*args, **kwargs)
        else:
            logger.warning("save(..) failed, blocking log_deletion(..)")

    def changelist_view(self, request, *args, **kwargs):
        """
        Base admin class method override. Despite the name, this is the main
        list view
        """
        if self.successful_save is False:
            _clear_most_recent_message(request)
            messages.error(request, str(self.exception))
        return super(DataSetAdmin, self).changelist_view(
            request, *args, **kwargs)

    search_fields = ['name']
    list_display = ('name', 'data_group', 'data_type', 'data_location')


def _clear_most_recent_message(request):
    storage = messages.get_messages(request)
    # Calling __iter__() causes messages to be transferred from
    # storage._queued_messages to storage._loaded_messages. See
    # django.contrib.messages.storage.base:BaseStorage

    storage.__iter__()
    if len(storage) > 0:
        storage._loaded_messages.pop(-1)

admin.site.register(DataSet, DataSetAdmin)
