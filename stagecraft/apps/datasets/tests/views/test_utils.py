from django.test import TestCase
from hamcrest import assert_that

from stagecraft.apps.datasets.tests.support.test_helpers import has_header


class LongCacheTestCase(TestCase):
    fixtures = ['datasets_testdata.json']

    def test_list_sets_cache_headers(self):
        resp = self.client.get(
            '/data-sets',
            HTTP_AUTHORIZATION='Bearer development-oauth-access-token')
        assert_that(resp, has_header('Cache-Control', 'no-cache, no-store, must-revalidate, max-age=0'))

    def test_detail_sets_cache_headers(self):
        resp = self.client.get(
            '/data-sets/set1',
            HTTP_AUTHORIZATION='Bearer development-oauth-access-token')
        assert_that(resp, has_header('Cache-Control', 'no-cache, no-store, must-revalidate, max-age=0'))
