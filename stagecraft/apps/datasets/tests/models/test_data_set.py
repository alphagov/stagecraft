# encoding: utf-8
# See https://docs.djangoproject.com/en/1.6/topics/testing/tools/

from __future__ import unicode_literals

import random
import string

import mock

from contextlib import contextmanager

from nose.tools import assert_raises, assert_equal

from django.core.exceptions import ValidationError
from django.db.models.deletion import ProtectedError
from django.test import TestCase, TransactionTestCase

from stagecraft.libs.backdrop_client import (
    disable_backdrop_connection, BackdropNotFoundError)
from stagecraft.apps.datasets.models import DataGroup, DataSet, DataType
from stagecraft.apps.datasets.models.data_set import ImmutableFieldError


class DataSetTestCase(TestCase):
    fixtures = ['datasets_testdata.json']

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

    def test_create_produces_a_name(self):
        with _make_temp_data_group_and_type() as (data_group, data_type):
            data_set1 = DataSet.objects.create(
                data_group=data_group,
                data_type=data_type)

            assert_equal(
                "{}_{}".format(data_group.name, data_type.name),
                data_set1.name)

    def test_saving_existing_doesnt_change_the_name(self):
        with _make_temp_data_group_and_type() as (data_group, data_type):
            data_set1 = DataSet.objects.get(name='set2')
            data_set1.save()

            assert_equal('set2', data_set1.name)

    @disable_backdrop_connection
    @mock.patch('stagecraft.apps.datasets.models.data_set.delete_data_set')
    def test_create_and_delete(self, delete_data_set):
        with _make_temp_data_group_and_type() as (data_group, data_type):

            data_set1 = DataSet.objects.create(
                data_group=data_group,
                data_type=data_type)

            assert_equal(1, len(DataSet.objects.filter(name=data_set1.name)))

            data_set1.delete()

            assert_equal(0, len(DataSet.objects.filter(name=data_set1.name)))

    def test_data_set_name_must_be_unique(self):
        a = DataSet.objects.create(
            data_group=self.data_group1,
            data_type=self.data_type1)

        a.validate_unique()

        b = DataSet(
            data_group=self.data_group1,
            data_type=self.data_type1)
        assert_raises(ValidationError, lambda: b.validate_unique())

    def test_upload_filters_are_serialised_as_a_list(self):
        data_set1 = DataSet.objects.create(
            data_group=self.data_group1,
            data_type=self.data_type1,
            upload_filters='aa.aa,bb.bb')

        assert_equal(data_set1.serialize()['upload_filters'],
                     ['aa.aa', 'bb.bb'])

    def test_auto_ids_are_serialised_as_a_list(self):
        data_set1 = DataSet.objects.create(
            data_group=self.data_group1,
            data_type=self.data_type1,
            auto_ids='aa,bb')

        assert_equal(data_set1.serialize()['auto_ids'], ['aa', 'bb'])

    def test_data_group_data_type_combo_must_be_unique(self):
        data_set1 = DataSet.objects.create(
            data_group=self.data_group1,
            data_type=self.data_type1)

        data_set1.validate_unique()

        data_set2 = DataSet(
            data_group=self.data_group1,
            data_type=self.data_type1)
        assert_raises(ValidationError, lambda: data_set2.validate_unique())

    def test_name_cannot_be_changed(self):
        data_set = DataSet.objects.create(
            data_group=self.data_group1,
            data_type=self.data_type1)

        data_set.name = 'Fred'
        assert_raises(ImmutableFieldError, data_set.save)

    def test_name_can_be_set_on_creation(self):
        DataSet.objects.create(
            name='Barney',
            data_group=self.data_group1,
            data_type=self.data_type1)

    def test_capped_size_cannot_be_changed(self):
        data_set = DataSet.objects.create(
            data_group=self.data_group1,
            data_type=self.data_type1)

        data_set.capped_size = 42
        assert_raises(ImmutableFieldError, data_set.save)

    def test_capped_size_can_be_set_on_creation(self):
        DataSet.objects.create(
            data_group=self.data_group1,
            data_type=self.data_type1,
            capped_size=42)

    def test_cant_delete_referenced_data_group(self):
        refed_data_group = DataGroup.objects.create(name='refed_data_group')
        DataSet.objects.create(
            data_group=refed_data_group,
            data_type=self.data_type1)

        assert_raises(ProtectedError, lambda: refed_data_group.delete())

    def test_cant_delete_referenced_data_type(self):
        refed_data_type = DataType.objects.create(name='refed_data_type')
        DataSet.objects.create(
            data_group=self.data_group1,
            data_type=refed_data_type)

        assert_raises(ProtectedError, lambda: refed_data_type.delete())

    def test_bearer_token_defaults_to_blank(self):
        data_set = DataSet.objects.create(
            data_group=self.data_group1,
            data_type=self.data_type1)
        assert_equal('', data_set.bearer_token)

    def test_that_empty_bearer_token_serializes_to_null(self):
        data_set = DataSet.objects.create(
            data_group=self.data_group1,
            data_type=self.data_type1,
            bearer_token='')
        assert_equal(None, data_set.serialize()['bearer_token'])

    def test_clean_raise_immutablefield_name_change(self):
        data_set = DataSet.objects.create(
            data_group=self.data_group1,
            data_type=self.data_type1)
        data_set.name = "abc"
        assert_raises(ImmutableFieldError, lambda: data_set.clean())

    def test_clean_raise_immutablefield_cappedsize_change(self):
        data_set = DataSet.objects.create(
            data_group=self.data_group1,
            data_type=self.data_type1)
        data_set.capped_size = 1000
        assert_raises(ImmutableFieldError, lambda: data_set.clean())

    def test_clean_not_raise_immutablefield_no_change(self):
        data_set = DataSet.objects.create(
            data_group=self.data_group1,
            data_type=self.data_type1)
        data_set.clean()

    def test_clean_not_raise_immutablefield_normal_change(self):
        new_data_type = DataType.objects.create(name='new_data_type')
        data_set = DataSet.objects.create(
            data_group=self.data_group1,
            data_type=self.data_type1)
        data_set.data_type = new_data_type
        data_set.clean()


def test_character_allowed_in_name():
    for character in 'a1_':
        yield _assert_name_is_valid, character * 10


def test_character_not_allowed_in_name():
    for character in 'A!"£$%^&*()=+-':
        yield _assert_name_not_valid, character * 10


def _random_name():
    return ''.join(random.choice(string.ascii_lowercase) for i in range(50))


@contextmanager
def _make_temp_data_group_and_type():
    data_group = DataGroup.objects.create(name=_random_name())
    data_type = DataType.objects.create(name=_random_name())

    yield data_group, data_type


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


class BackdropIntegrationTestCase(TransactionTestCase):

    """
    Test that delete_data_set() from stagecraft.libs.backdrop_client is
    called appropriately on model deletion, and that Stagecraft responds
    appropriately.
    """

    @mock.patch('stagecraft.apps.datasets.models.data_set.delete_data_set')
    def test_backdrop_is_called_on_model_delete(self, mock_delete_data_set):
        with _make_temp_data_group_and_type() as (data_group, data_type):
            data_set = DataSet.objects.create(
                data_group=data_group,
                data_type=data_type)

            data_set.delete()
        mock_delete_data_set.assert_called_once_with(data_set.name)

    @mock.patch('stagecraft.apps.datasets.models.data_set.delete_data_set')
    def test_data_set_deleted_when_backdrop_404s(self, mock_delete_data_set):
        mock_delete_data_set.side_effect = BackdropNotFoundError
        with _make_temp_data_group_and_type() as (data_group, data_type):
            data_set = DataSet.objects.create(
                data_group=data_group,
                data_type=data_type)

            try:
                data_set.delete()
            except BackdropNotFoundError:
                self.fail('Deleting dataset raised a 404 error')
        mock_delete_data_set.assert_called_once_with(data_set.name)
        assert_equal(0, len(DataSet.objects.filter(name=data_set.name)))

    @mock.patch('stagecraft.apps.datasets.models.data_set.delete_data_set')
    def test_backdrop_is_called_on_query_set_delete(self,
                                                    mock_delete_data_set):
        with _make_temp_data_group_and_type() as (data_group, data_type):
            data_set = DataSet.objects.create(
                name='test_data_set_006',
                data_group=data_group,
                data_type=data_type)

            DataSet.objects.all().delete()

        mock_delete_data_set.assert_called_once_with(data_set.name)
