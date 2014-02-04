# encoding: utf-8
# See https://docs.djangoproject.com/en/1.6/topics/testing/tools/

from __future__ import unicode_literals

from django.test import TestCase

from django.core.exceptions import ValidationError

from nose.tools import assert_raises

from stagecraft.apps.datasets.models import DataGroup, DataSet, DataType


class DataSetTestCase(TestCase):
    def test_data_set_name_must_be_unique(self):
        datagroup1 = DataGroup.objects.create(name='datagroup1')
        datatype1 = DataType.objects.create(name='datatype1')
        datatype2 = DataType.objects.create(name='datatype2')

        a = DataSet.objects.create(name='foo', data_group=datagroup1,
                                   data_type=datatype1)
        a.validate_unique()

        b = DataSet(name='foo', data_group=datagroup1, data_type=datatype2)
        assert_raises(ValidationError, lambda: b.validate_unique())

    def test_data_group_data_type_combo_must_be_unique(self):
        datagroup1 = DataGroup.objects.create(name='datagroup1')
        datatype1 = DataType.objects.create(name='datatype1')

        dataset1 = DataSet.objects.create(name='dataset1',
                                          data_group=datagroup1,
                                          data_type=datatype1)
        dataset1.validate_unique()

        dataset2 = DataSet(name='dataset2', data_group=datagroup1,
                           data_type=datatype1)
        assert_raises(ValidationError, lambda: dataset2.validate_unique())


def test_character_allowed_in_name():
    for character in 'a1_-':
        yield _assert_name_is_valid, character * 10


def test_character_not_allowed_in_name():
    for character in '!"£$%^&*()=+':
        yield _assert_name_not_valid, character * 10


def _assert_name_is_valid(name):
    datagroup = DataGroup.objects.create(name='datagroup')
    datatype = DataType.objects.create(name='datatype')
    DataSet(name=name, data_group=datagroup, data_type=datatype).full_clean()
    datagroup.delete()
    datatype.delete()


def _assert_name_not_valid(name):
    datagroup = DataGroup.objects.create(name='datagroup')
    datatype = DataType.objects.create(name='datatype')
    assert_raises(
        ValidationError,
        lambda: DataSet(name=name, data_group=datagroup,
                        data_type=datatype).full_clean())
    datagroup.delete()
    datatype.delete()
