# encoding: utf-8
# See https://docs.djangoproject.com/en/1.6/topics/testing/tools/

from __future__ import unicode_literals

from django.test import TestCase

from django.core.exceptions import ValidationError

from nose.tools import assert_raises

from stagecraft.apps.datasets.models import DataGroup


class DataGroupTestCase(TestCase):
    def test_data_group_name_must_be_unique(self):
        a = DataGroup.objects.create(name='foo')
        a.validate_unique()

        b = DataGroup(name='foo')
        assert_raises(ValidationError, lambda: b.validate_unique())


def test_character_allowed_in_name():
    for character in 'a1-':
        yield _assert_name_is_valid, character * 10


def test_character_not_allowed_in_name():
    for character in 'A!"£$%^&*()=+_':
        yield _assert_name_not_valid, character * 10


def _assert_name_is_valid(name):
    DataGroup(name=name).full_clean()


def _assert_name_not_valid(name):
    assert_raises(
        ValidationError,
        lambda: DataGroup(name=name).full_clean())
