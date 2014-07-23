from __future__ import unicode_literals

import json
from nose.tools import assert_equal
from hamcrest import assert_that

from django.test import TestCase

from stagecraft.apps.datasets.tests.support.test_helpers import (
    is_unauthorized, is_error_response, has_header)


class LongCacheTestCase(TestCase):
    def test_detail_sets_long_cache_headers(self):
        resp = self.client.get(
            '/data-sets/set1',
            HTTP_AUTHORIZATION='Bearer development-oauth-access-token')
        assert_that(resp, has_header('Cache-Control', 'max-age=31536000'))
        assert_that(resp, has_header('Vary', 'Authorization'))


class BackdropUserViewsTestCase(TestCase):
    fixtures = ['backdrop_users_testdata.json']

    def test_authorization_header_needed_for_detail(self):
        resp = self.client.get('/users/tea%40yourmumshouse.com')
        assert_that(resp, is_unauthorized())
        assert_that(resp, is_error_response())

    def test_correct_format_authorization_header_needed_for_detail(self):
        resp = self.client.get(
            '/users/tea%40yourmumshouse.com',
            HTTP_AUTHORIZATION='Nearer development-oauth-access-token')
        assert_that(resp, is_unauthorized())
        assert_that(resp, is_error_response())

    def test_correct_authorization_header_needed_for_detail(self):
        resp = self.client.get(
            '/users/tea%40yourmumshouse.com',
            HTTP_AUTHORIZATION='Bearer I AM WRONG')
        assert_that(resp, is_unauthorized())
        assert_that(resp, is_error_response())

    def test_detail(self):
        resp = self.client.get(
            '/users/foo%40bar.com',
            HTTP_AUTHORIZATION='Bearer development-oauth-access-token')
        assert_equal(resp.status_code, 200)
        expected = {'data_sets': ['set1', 'set2'], 'email': 'foo@bar.com'}
        assert_equal(json.loads(resp.content.decode('utf-8')), expected)

    def test_detail_nonexistant_user(self):
        resp = self.client.get(
            '/users/nonexistant@user.com',
            HTTP_AUTHORIZATION='Bearer development-oauth-access-token')
        assert_equal(resp.status_code, 404)
        assert_that(resp, is_error_response(
            "No user with email address 'nonexistant@user.com' exists"))
