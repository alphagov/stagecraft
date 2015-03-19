from django.conf import settings
from django.test import TestCase, Client

from hamcrest import assert_that, is_, is_not, equal_to
from httmock import HTTMock

from stagecraft.apps.datasets.models.oauth_user import OAuthUser
from stagecraft.libs.authorization.tests.test_http import govuk_signon_mock
from ..support.test_helpers import is_unauthorized, is_forbidden


class OAuthInvalidateTestCase(TestCase):

    def setUp(self):
        self.client = Client(enforce_csrf_checks=True)
        settings.USE_DEVELOPMENT_USERS = False

    def tearDown(self):
        settings.USE_DEVELOPMENT_USERS = True

    def _create_oauth_user(self):
        OAuthUser.objects.cache_user(
            'the-token',
            {"uid": "the-uid",
             "email": "foo@foo.com",
             "permissions": ['signin', 'admin']})

    def _mock_signon(self, permissions):
        return HTTMock(
            govuk_signon_mock(
                permissions=permissions))

    def test_reauth_with_permission(self):
        self._create_oauth_user()
        with self._mock_signon(['signin', 'user_update_permission']):
            resp = self.client.post(
                '/auth/gds/api/users/the-uid/reauth',
                HTTP_AUTHORIZATION='Bearer correct-token')
            assert_that(resp.status_code, equal_to(204))
            assert_that(
                OAuthUser.objects.get_by_access_token('the-token'),
                is_(None))

    def test_update_with_permission(self):
        self._create_oauth_user()
        with self._mock_signon(['signin', 'user_update_permission']):
            resp = self.client.put(
                '/auth/gds/api/users/the-uid',
                HTTP_AUTHORIZATION='Bearer correct-token')
            assert_that(resp.status_code, equal_to(204))
            assert_that(
                OAuthUser.objects.get_by_access_token('the-token'),
                is_(None))

    def test_invalidate_without_permission(self):
        self._create_oauth_user()
        with self._mock_signon(['signin']):
            resp = self.client.post(
                '/auth/gds/api/users/the-uid/reauth',
                HTTP_AUTHORIZATION='Bearer correct-token')
            assert_that(resp, is_forbidden())
            assert_that(
                OAuthUser.objects.get_by_access_token('the-token'),
                is_not(None))

    def test_invalidate_returns_200_if_user_is_not_found(self):
        with self._mock_signon(['signin', 'user_update_permission']):
            resp = self.client.post(
                '/auth/gds/api/users/the-uid/reauth',
                HTTP_AUTHORIZATION='Bearer correct-token')
            assert_that(resp.status_code, equal_to(204))

    def test_subsequent_requests_are_unauthorized(self):
        self._create_oauth_user()
        resp = self.client.get(
            '/data-sets',
            HTTP_AUTHORIZATION='Bearer the-token')
        assert_that(resp.status_code, equal_to(200))

        with self._mock_signon(['signin', 'user_update_permission']):
            self.client.post(
                '/auth/gds/api/users/the-uid/reauth',
                HTTP_AUTHORIZATION='Bearer correct-token')
            resp = self.client.get(
                '/data-sets',
                HTTP_AUTHORIZATION='Bearer the-token')
            assert_that(resp, is_unauthorized())

    def test_fails_with_get(self):
        with self._mock_signon(['signin', 'user_update_permission']):
            resp = self.client.get(
                '/auth/gds/api/users/the-uid/reauth',
                HTTP_AUTHORIZATION='Bearer correct-token')
            assert_that(resp.status_code, equal_to(405))
