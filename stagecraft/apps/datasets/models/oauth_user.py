from __future__ import unicode_literals

from collections import OrderedDict

from django.db import models
from django.utils.encoding import python_2_unicode_compatible
from south.utils.datetime_utils import datetime, timedelta

import dbarray


class OAuthUserManager(models.Manager):
    def get_by_access_token(self, access_token):
        try:
            oauth_user = self.get(access_token=access_token)
            if oauth_user.expires_at < datetime.now():
                oauth_user.delete()
                return
            return oauth_user
        except OAuthUser.DoesNotExist:
            pass

    def cache_user(self, access_token, user):
        oauth_user = OAuthUser(
            access_token=access_token,
            uid=user['uid'],
            email=user['email'],
            permissions=user['permissions'],
            expires_at=datetime.now() + timedelta(minutes=15))
        oauth_user.save()

    def purge_user(self, uid):
        self.filter(uid=uid).delete()


@python_2_unicode_compatible
class OAuthUser(models.Model):
    access_token = models.CharField(max_length=255, unique=True)
    uid = models.CharField(max_length=255, db_index=True)
    email = models.EmailField()
    permissions = dbarray.CharArrayField(max_length=255)
    expires_at = models.DateTimeField()

    objects = OAuthUserManager()

    def __str__(self):
        return "{}".format(self.uid)

    def serialize(self):
        return OrderedDict([
            ('uid', self.uid),
            ('email', self.email),
            ('permissions', self.permissions),
        ])

    class Meta:
        app_label = 'datasets'
