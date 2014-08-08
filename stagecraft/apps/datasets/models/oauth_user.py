from __future__ import unicode_literals

from django.db import models
from django.utils.encoding import python_2_unicode_compatible

import dbarray


@python_2_unicode_compatible
class OAuthUser(models.Model):
    access_token = models.CharField(max_length=255, unique=True)
    uid = models.CharField(max_length=255, db_index=True)
    email = models.EmailField()
    permissions = dbarray.CharArrayField(max_length=255)

    expires_at = models.DateTimeField()

    def __str__(self):
        return "{}".format(self.uid)

    class Meta:
        app_label = 'datasets'
