from hamcrest import *
from stagecraft.libs.validation.validation import extract_bearer_token
from django.test import TestCase


class BearerTokenIsValid(TestCase):
    def test_extract_bearer_token_returns_blank_string_if_invalid(self):
        received_token = "token"

        assert_that(extract_bearer_token(received_token), is_(''))

    def test_extract_bearer_token_returns_the_token_if_valid(self):
        token = "token"
        received_token = "Bearer {}".format(token)

        assert_that(extract_bearer_token(received_token), is_(token))
