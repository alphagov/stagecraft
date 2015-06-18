from __future__ import unicode_literals
from django.utils.encoding import python_2_unicode_compatible
from django.db import models

import reversion


@python_2_unicode_compatible
class User(models.Model):

    email = models.EmailField(
        max_length=254,
        unique=True,
        help_text=""""""
    )

    def serialize(self):
        return {'email': self.email}

    def api_object(self):
        """
        Just the parts of a user object we would want to return
        """
        return {
            'email': self.email
        }

    def __str__(self):
        return "{}".format(self.email)

    class Meta:
        app_label = 'users'
        ordering = ['email']


reversion.register(User)
