from hamcrest import assert_that, is_, equal_to

from django.test import TestCase

from stagecraft.apps.datasets.models import OAuthUser


class OAuthUserTest(TestCase):

    def test_get_by_access_token_returns_none_if_not_found(self):
        assert_that(
            OAuthUser.objects.get_by_access_token('not-there'),
            is_(None))

    def test_get_by_access_token_after_cache(self):
        OAuthUser.objects.cache_user(
            'access-token',
            {'uid': 'uid', 'email': 'foo@bar', 'permissions': ['one']})

        oauth_user = OAuthUser.objects.get_by_access_token('access-token')

        assert_that(oauth_user.access_token, equal_to('access-token'))
        assert_that(oauth_user.email, equal_to('foo@bar'))
        assert_that(oauth_user.permissions, equal_to(['one']))

    def test_cache_user_does_not_fail_if_user_already_exists(self):
        OAuthUser.objects.cache_user(
            'access-token',
            {'uid': 'uid', 'email': 'foo@bar', 'permissions': ['one']})
        OAuthUser.objects.cache_user(
            'access-token',
            {'uid': 'uid', 'email': 'foo@bar', 'permissions': ['one']})

    def test_get_by_access_token_returns_none_after_purge(self):
        OAuthUser.objects.cache_user(
            'access-token',
            {'uid': 'uid', 'email': 'foo@bar', 'permissions': ['one']})

        OAuthUser.objects.purge_user('uid')

        assert_that(
            OAuthUser.objects.get_by_access_token('access-token'),
            is_(None))
