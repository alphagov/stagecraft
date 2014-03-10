from __future__ import unicode_literals

from hamcrest import assert_that, is_

from django.http import HttpRequest
from django.test import TestCase

from stagecraft.libs.validation.validation import extract_bearer_token


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
