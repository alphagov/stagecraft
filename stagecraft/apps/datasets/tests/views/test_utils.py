from hamcrest import assert_that, equal_to, none
from httmock import urlmatch, HTTMock

from django.conf import settings
from django.test import TestCase

from stagecraft.apps.datasets.tests.support.test_helpers import has_header
from stagecraft.apps.datasets.views.common.utils import check_permission


def govuk_signon_mock(**kwargs):
    @urlmatch(netloc=r'.*signon.*')
    def func(url, request):
        if request.headers['Authorization'] == 'Bearer correct-token':
            status_code = 200
            user = {
                "user": {
                    "email": kwargs.get("email", "foobar.lastname@gov.uk"),
                    "name": kwargs.get("name", "Foobar"),
                    "organisation_slug": kwargs.get(
                        "organisation_slug", "cabinet-office"),
                    "permissions": kwargs.get("permissions", ["signin"]),
                    "uid": "a-long-uid",
                }
            }

        else:
            status_code = 401
            user = {}

        return {'status_code': status_code, 'content': user}

    return func


class CheckPermissionTestCase(TestCase):

    def setUp(self):
        self.use_development_users = settings.USE_DEVELOPMENT_USERS

    def tearDown(self):
        settings.USE_DEVELOPMENT_USERS = self.use_development_users

    def test_use_development_users_gets_from_dictionary(self):
        (user, has_permission) = check_permission(
            'development-oauth-access-token', 'signin')
        assert_that(user['name'], equal_to('Some User'))
        assert_that(has_permission, equal_to(True))

    def test_user_with_permission_returns_object_and_true(self):
        settings.USE_DEVELOPMENT_USERS = False
        with HTTMock(govuk_signon_mock()):
            (user, has_permission) = check_permission(
                'correct-token', 'signin')
        assert_that(user['name'], equal_to('Foobar'))
        assert_that(has_permission, equal_to(True))

    def test_user_without_permission_returns_none_and_false(self):
        settings.USE_DEVELOPMENT_USERS = False
        with HTTMock(govuk_signon_mock()):
            (user, has_permission) = check_permission('bad-auth', 'signin')
        assert_that(user, none())
        assert_that(has_permission, equal_to(False))


class LongCacheTestCase(TestCase):
    fixtures = ['datasets_testdata.json']

    def test_list_sets_long_cache_headers(self):
        resp = self.client.get(
            '/data-sets',
            HTTP_AUTHORIZATION='Bearer development-oauth-access-token')
        assert_that(resp, has_header('Cache-Control', 'max-age=31536000'))

    def test_detail_sets_long_cache_headers(self):
        resp = self.client.get(
            '/data-sets/set1',
            HTTP_AUTHORIZATION='Bearer development-oauth-access-token')
        assert_that(resp, has_header('Cache-Control', 'max-age=31536000'))
