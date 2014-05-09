# encoding: utf-8
# See https://docs.djangoproject.com/en/1.6/topics/testing/tools/

from __future__ import unicode_literals

from django.test import TestCase

from django.core.exceptions import ValidationError

from nose.tools import assert_raises

from stagecraft.apps.datasets.models import BackdropUser


class BackdropUserTestCase(TestCase):
    def test_user_email_must_be_unique(self):
        a = BackdropUser.objects.create(email='email@email.com')
        a.validate_unique()

        b = BackdropUser(email='email@email.com')
        assert_raises(ValidationError, lambda: b.validate_unique())
