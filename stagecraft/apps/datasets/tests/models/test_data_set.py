# encoding: utf-8
# See https://docs.djangoproject.com/en/1.6/topics/testing/tools/

from __future__ import unicode_literals

from contextlib import contextmanager

from nose.tools import assert_raises

from django.test import TestCase
from django.core.exceptions import ValidationError

from stagecraft.apps.datasets.models import DataGroup, DataSet, DataType


class DataSetTestCase(TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data_group1 = DataGroup.objects.create(name='data_group1')
        cls.data_type1 = DataType.objects.create(name='data_type1')
        cls.data_type2 = DataType.objects.create(name='data_type2')

    @classmethod
    def tearDownClass(cls):
        cls.data_group1.delete()
        cls.data_type1.delete()
        cls.data_type2.delete()

    def test_data_set_name_must_be_unique(self):
        a = DataSet.objects.create(
            name='foo',
            data_group=self.data_group1,
            data_type=self.data_type1)

        a.validate_unique()

        b = DataSet(
            name='foo',
            data_group=self.data_group1,
            data_type=self.data_type2)

        assert_raises(ValidationError, lambda: b.validate_unique())

    def test_data_group_data_type_combo_must_be_unique(self):
        data_set1 = DataSet.objects.create(
            name='data_set1',
            data_group=self.data_group1,
            data_type=self.data_type1)

        data_set1.validate_unique()

        data_set2 = DataSet(
            name='data_set2',
            data_group=self.data_group1,
            data_type=self.data_type1)
        assert_raises(ValidationError, lambda: data_set2.validate_unique())


def test_character_allowed_in_name():
    for character in 'a1_-':
        yield _assert_name_is_valid, character * 10


def test_character_not_allowed_in_name():
    for character in '!"£$%^&*()=+':
        yield _assert_name_not_valid, character * 10


@contextmanager
def _make_temp_data_group_and_type():
    data_group = DataGroup.objects.create(name='tmp_data_group')
    data_type = DataType.objects.create(name='tmp_data_type')

    yield data_group, data_type

    data_group.delete()
    data_type.delete()


def _assert_name_is_valid(name):
    with _make_temp_data_group_and_type() as (data_group, data_type):
        DataSet(
            name=name,
            data_group=data_group,
            data_type=data_type).full_clean()


def _assert_name_not_valid(name):
    with _make_temp_data_group_and_type() as (data_group, data_type):
        assert_raises(
            ValidationError,
            lambda: DataSet(
                name=name,
                data_group=data_group,
                data_type=data_type).full_clean())
