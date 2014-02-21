# encoding: utf-8
# See https://docs.djangoproject.com/en/1.6/topics/testing/tools/

from __future__ import unicode_literals

import mock

from contextlib import contextmanager

from nose.tools import assert_raises, assert_equal

from django.core.exceptions import ValidationError, ObjectDoesNotExist
from django.db.models.deletion import ProtectedError
from django.db.models.manager import Manager
from django.test import TestCase, TransactionTestCase

from stagecraft.apps.datasets.models import DataGroup, DataSet, DataType
from stagecraft.apps.datasets.models.data_set import (
    DeleteNotImplementedError, ImmutableFieldError)
from stagecraft.libs.backdrop_client import BackdropError


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

    # intercept call to backdrop_client.create_dataset
    @mock.patch('stagecraft.apps.datasets.models.data_set.create_dataset')
    def test_data_set_name_must_be_unique(self, mocked):
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

    @mock.patch('stagecraft.apps.datasets.models.data_set.create_dataset')
    def test_data_group_data_type_combo_must_be_unique(self, mocked):
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

    @mock.patch('stagecraft.apps.datasets.models.data_set.create_dataset')
    def test_name_cannot_be_changed(self, mocked):
        data_set = DataSet.objects.create(
            name='data_set',
            data_group=self.data_group1,
            data_type=self.data_type1)

        data_set.name = 'Fred'
        assert_raises(ImmutableFieldError, data_set.save)

    @mock.patch('stagecraft.apps.datasets.models.data_set.create_dataset')
    def test_name_can_be_set_on_creation(self, mocked):
        data_set = DataSet.objects.create(
            name='Barney',
            data_group=self.data_group1,
            data_type=self.data_type1)

    @mock.patch('stagecraft.apps.datasets.models.data_set.create_dataset')
    def test_capped_size_cannot_be_changed(self, mocked):
        data_set = DataSet.objects.create(
            name='data_set',
            data_group=self.data_group1,
            data_type=self.data_type1)

        data_set.capped_size = 42
        assert_raises(ImmutableFieldError, data_set.save)

    @mock.patch('stagecraft.apps.datasets.models.data_set.create_dataset')
    def test_capped_size_can_be_set_on_creation(self, mocked):
        data_set = DataSet.objects.create(
            name='data_set',
            data_group=self.data_group1,
            data_type=self.data_type1,
            capped_size=42)

    @mock.patch('stagecraft.apps.datasets.models.data_set.create_dataset')
    def test_cant_delete_data_set(self, mocked):
        data_set = DataSet.objects.create(
            name='data_set',
            data_group=self.data_group1,
            data_type=self.data_type1)

        assert_raises(DeleteNotImplementedError, lambda: data_set.delete())

    @mock.patch('stagecraft.apps.datasets.models.data_set.create_dataset')
    def test_cant_delete_referenced_data_group(self, mocked):
        refed_data_group = DataGroup.objects.create(name='refed_data_group')
        data_set = DataSet.objects.create(
            name='data_set',
            data_group=refed_data_group,
            data_type=self.data_type1)

        assert_raises(ProtectedError, lambda: refed_data_group.delete())

    @mock.patch('stagecraft.apps.datasets.models.data_set.create_dataset')
    def test_cant_delete_referenced_data_type(self, mocked):
        refed_data_type = DataType.objects.create(name='refed_data_type')
        data_set = DataSet.objects.create(
            name='data_set',
            data_group=self.data_group1,
            data_type=refed_data_type)

        assert_raises(ProtectedError, lambda: refed_data_type.delete())

    @mock.patch('stagecraft.apps.datasets.models.data_set.create_dataset')
    def test_bearer_token_defaults_to_blank(self, mocked):
        data_set = DataSet.objects.create(
            name='data_set',
            data_group=self.data_group1,
            data_type=self.data_type1)
        assert_equal('', data_set.bearer_token)

    @mock.patch('stagecraft.apps.datasets.models.data_set.create_dataset')
    def test_that_empty_bearer_token_serializes_to_null(self, mocked):
        data_set = DataSet.objects.create(
            name='data_set',
            data_group=self.data_group1,
            data_type=self.data_type1,
            bearer_token='')
        assert_equal(None, data_set.serialize()['bearer_token'])


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


class BackdropIntegrationTestCase(TransactionTestCase):

    """
    Test that stagecraft.libs.backdrop_client.create_dataset(...)
    is called appropriately on model creation, and that stagecraft responds
    appropriately to the result of that.
    """

    @classmethod
    def setUpClass(cls):
        cls.data_group = DataGroup.objects.create(name='data_group1')
        cls.data_type = DataType.objects.create(name='data_type1')

    @classmethod
    def tearDownClass(cls):
        cls.data_group.delete()
        cls.data_type.delete()

    @mock.patch('stagecraft.apps.datasets.models.data_set.create_dataset')
    def test_stagecraft_calls_backdrop_on_save(self, mock_create_dataset):
        DataSet.objects.create(
            name='test_dataset',
            data_group=self.data_group,
            data_type=self.data_type)

        mock_create_dataset.assert_called_once_with('test_dataset', 0)

    @mock.patch('stagecraft.apps.datasets.models.data_set.create_dataset')
    def test_model_not_saved_on_backdrop_failure(self, mock_create_dataset):
        # Not saved because of being rolled back
        mock_create_dataset.side_effect = BackdropError('Failed')

        assert_raises(
            BackdropError,
            lambda: DataSet.objects.create(
                name='test_dataset',
                data_group=self.data_group,
                data_type=self.data_type)
        )

        assert_raises(
            ObjectDoesNotExist,
            lambda: DataSet.objects.get(name='test_dataset'))

    @mock.patch.object(Manager, 'get_or_create')
    @mock.patch('stagecraft.apps.datasets.models.data_set.create_dataset')
    def test_backdrop_not_called_on_model_save_failure(
            self, mock_get_or_create, mock_create_dataset):

        mock_get_or_create.side_effect = Exception("My first fake db error")

        assert_raises(
            Exception,
            lambda: DataSet.objects.create(
                name='test_dataset',
                data_group=self.data_group,
                data_type=self.data_type)
        )

        mock_create_dataset.assert_not_called('test_dataset', 0)

    @mock.patch('stagecraft.apps.datasets.models.data_set.create_dataset')
    def test_model_saved_on_backdrop_success(self, mock_create_dataset):
        DataSet.objects.create(
            name='test_dataset',
            data_group=self.data_group,
            data_type=self.data_type)

        DataSet.objects.get(name='test_dataset')  # should succeed
