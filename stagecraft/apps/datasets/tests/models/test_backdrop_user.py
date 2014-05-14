# encoding: utf-8
# See https://docs.djangoproject.com/en/1.6/topics/testing/tools/

from __future__ import unicode_literals

from django.test import TestCase, TransactionTestCase

from django.core.exceptions import ValidationError

from nose.tools import assert_raises, assert_equal

from stagecraft.apps.datasets.models import(
    BackdropUser, DataSet)

import mock


class BackdropUserTestCase(TestCase):
    fixtures = ['test_import_users_datasets.json']

    def test_user_email_must_be_unique(self):
        a = BackdropUser.objects.create(email='email@email.com')
        a.validate_unique()

        b = BackdropUser(email='email@email.com')
        assert_raises(ValidationError, lambda: b.validate_unique())

    def test_serialize_returns_serialized_user(self):
        a = BackdropUser.objects.create(email='email@blah.net')
        a.data_sets.add(DataSet.objects.get(name="evl_customer_satisfaction"))
        a.data_sets.add(DataSet.objects.get(name="lpa_volumes"))
        expected_response = {
            'email': 'email@blah.net',
            'data_sets': ['evl_customer_satisfaction', 'lpa_volumes']
        }

        assert_equal(a.serialize(), expected_response)


class VarnishCacheIntegrationTestCase(TransactionTestCase):

    """
    Test that Varnish's caches are being purged at the appropriate times.
    """

    @mock.patch('stagecraft.apps.datasets.models.backdrop_user.purge')
    @mock.patch('stagecraft.apps.datasets.models.backdrop_user.'
                'get_backdrop_user_path_queries')
    def test_user_purges_cache_on_create(
            self,
            mock_get_path_queries,
            mock_purge):

        mock_get_path_queries.return_value = ['/some_url']

        BackdropUser.objects.create(email='email@blah.net')

        mock_purge.assert_called_once_with(['/some_url'])

    @mock.patch('stagecraft.apps.datasets.models.backdrop_user.purge')
    @mock.patch('stagecraft.apps.datasets.models.backdrop_user.'
                'get_backdrop_user_path_queries')
    def test_user_purges_cache_on_save(
            self,
            mock_get_path_queries,
            mock_purge):

        user = BackdropUser.objects.create(email='email@blah.net')

        mock_get_path_queries.reset_mock()
        mock_purge.reset_mock()

        mock_get_path_queries.return_value = ['/some_url']

        user.save()

        mock_purge.assert_called_once_with(['/some_url'])

    @mock.patch('stagecraft.apps.datasets.models.backdrop_user.purge')
    @mock.patch('stagecraft.apps.datasets.models.backdrop_user.'
                'get_backdrop_user_path_queries')
    def test_user_purges_cache_on_delete(
            self,
            mock_get_path_queries,
            mock_purge):

        user = BackdropUser.objects.create(email='email@blah.net')

        mock_get_path_queries.reset_mock()
        mock_purge.reset_mock()

        mock_get_path_queries.return_value = ['/some_url']

        user.delete()

        mock_purge.assert_called_once_with(['/some_url'])

    @mock.patch('django.db.models.Model.save')
    @mock.patch('stagecraft.apps.datasets.models.backdrop_user.purge')
    def test_purge_not_called_on_model_save_failure(
            self,
            mock_purge,
            mock_save):

        mock_save.side_effect = Exception("My first fake db error")

        assert_raises(
            Exception,
            lambda: BackdropUser.objects.create(email='email@blah.net')
        )

        assert_equal(mock_purge.called, False)
