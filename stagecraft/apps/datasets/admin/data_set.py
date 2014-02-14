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

    `response_add` and `response_change` methods:
      - by default in the base class they generate a success message
      - we are overriding here to generate a different message
        if the model fails to save

    """

    def __init__(self, *args, **kwargs):
        super(DataSetAdmin, self).__init__(*args, **kwargs)
        self.successful_save = False
        self.exception = None

    # Get fields that are only editable on creation
    def get_readonly_fields(self, request, obj=None):
        if obj:  # record already exists
            return DataSet.READONLY_FIELDS
        else:
            return set()

    def save_model(self, request, *args, **kwargs):
        try:
            super(DataSetAdmin, self).save_model(request, *args, **kwargs)
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

    def response_add(self, request, obj, *args, **kwargs):
        """
        Generate the HTTP response for an add action.
        """
        if self.successful_save is True:
            # The base response_add() emits an appropriate success message
            return super(DataSetAdmin, self).response_add(
                request, obj, *args, **kwargs)

        messages.error(request, "Failed to create: {}".format(
            repr(self.exception)))
        return self.response_post_save_add(request, obj)

    def response_change(self, request, obj, *args, **kwargs):
        """
        Generate the HTTP response for a save action.
        """
        if self.successful_save is True:
            # The base response_change() emits an appropriate success message
            return super(DataSetAdmin, self).response_change(
                request, obj, *args, **kwargs)

        messages.error(request, "Failed to modify: {}".format(
            repr(self.exception)))
        return self.response_post_save_change(request, obj)

admin.site.register(DataSet, DataSetAdmin)
