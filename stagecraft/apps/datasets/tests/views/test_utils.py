from hamcrest import assert_that

from django.test import TestCase

from stagecraft.apps.datasets.tests.support.test_helpers import has_header


class LongCacheTestCase(TestCase):

    def test_list_sets_long_cache_headers(self):
        resp = self.client.get(
            '/data-sets',
            HTTP_AUTHORIZATION='Bearer dev-data-set-query-token')
        assert_that(resp, has_header('Cache-Control', 'max-age=31536000'))

    def test_detail_sets_long_cache_headers(self):
        resp = self.client.get(
            '/data-sets/set1',
            HTTP_AUTHORIZATION='Bearer dev-data-set-query-token')
        assert_that(resp, has_header('Cache-Control', 'max-age=31536000'))
