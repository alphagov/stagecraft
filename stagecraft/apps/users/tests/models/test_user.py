# encoding: utf-8
# See https://docs.djangoproject.com/en/1.6/topics/testing/tools/

from __future__ import unicode_literals

from django.test import TestCase

from django.core.exceptions import ValidationError

from nose.tools import assert_raises, assert_equal

from stagecraft.apps.datasets.models import DataSet
from stagecraft.apps.users.models import User


class UserTestCase(TestCase):
    fixtures = ['test_import_users_datasets.json']

    def test_user_email_must_be_unique(self):
        a = User.objects.create(email='email@email.com')
        a.validate_unique()

        b = User(email='email@email.com')
        assert_raises(ValidationError, lambda: b.validate_unique())

    def test_serialize_returns_serialized_user(self):
        a = User.objects.create(email='email@blah.net')
        expected_response = {'email': 'email@blah.net'}

        assert_equal(a.serialize(), expected_response)
