from __future__ import unicode_literals

from collections import OrderedDict
import logging

from django.db import models, IntegrityError, InternalError
from django.utils.encoding import python_2_unicode_compatible
from django.utils import timezone
from datetime import timedelta
from django_statsd.clients import statsd

import dbarray


log = logging.getLogger(__name__)


class OAuthUserManager(models.Manager):

    def get_by_access_token(self, access_token):
        try:
            oauth_user = self.get(access_token=access_token)
            if oauth_user.expires_at < timezone.now():
                oauth_user.delete()
                return
            return oauth_user
        except OAuthUser.DoesNotExist:
            pass
        except InternalError as e:
            statsd.incr('oauth_user.internal_error.count')
            log.error(e)

    def cache_user(self, access_token, user):
        oauth_user = OAuthUser(
            access_token=access_token,
            uid=user['uid'],
            email=user['email'],
            permissions=user['permissions'],
            expires_at=timezone.now() + timedelta(minutes=15))
        try:
            oauth_user.save()
        except IntegrityError:
            # can happen if another request completed in the meantime
            # in which case, we can just trust what's in there
            pass
        except InternalError as e:
            statsd.incr('oauth_user.internal_error.count')
            log.error(e)

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
