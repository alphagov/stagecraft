from __future__ import unicode_literals

from hamcrest import assert_that, is_, equal_to

from django.http import HttpRequest
from django.test import TestCase

from stagecraft.libs.validation.validation import (
    extract_bearer_token, is_uuid)


def mock_request(auth_header):
    """
    >>> a = mock_request('Bearer some-token')
    >>> a.META['HTTP_AUTHORIZATION']
    'Bearer some-token'
    """
    request = HttpRequest()
    request.META['HTTP_AUTHORIZATION'] = auth_header
    return request


class BearerTokenIsValid(TestCase):

    def test_extract_bearer_token_returns_the_token_if_valid(self):
        token = "token"
        auth_header = "Bearer {}".format(token)

        assert_that(
            extract_bearer_token(mock_request(auth_header)),
            is_(token))

    def test_extract_bearer_token_returns_None_if_invalid(self):
        auth_header = "token"

        assert_that(
            extract_bearer_token(mock_request(auth_header)),
            is_(None))

    def test_extract_bearer_token_returns_None_if_wrong_prefix(self):
        token = "token"
        auth_header = "Nearer {}".format(token)

        assert_that(
            extract_bearer_token(mock_request(auth_header)),
            is_(None))


class IsUUIDTestCase(TestCase):

    def test_is_uuid(self):
        assert_that(is_uuid('blah'), equal_to(False))
        assert_that(
            is_uuid('edc9aa07-f45f-4d93-9f9c-d9d760f08019'),
            equal_to(True)
        )
        assert_that(
            is_uuid('edc9aa07f45f4d939f9cd9d760f08019'),
            equal_to(True)
        )
