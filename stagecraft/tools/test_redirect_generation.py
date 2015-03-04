import os
import json
from .redirects import generate, write
from hamcrest import (
    assert_that, equal_to
)
import unittest

from mock import patch, Mock, call

MERGED_RECORDS = [
    {
        "name":"Registrations to use online \
        training and resources on workplace relations",
        "service":{
            "name":"Training and resources on workplace relations",
            "slug":"training-resources-on-workplace-relations"
        },
        "agency":{
            "abbr":"CPS",
            "name":"Crown Prosecution Service",
            "slug":"cps"
        },
        "tx_id":"bis-acas-elearning-registrations",
        "department":{
            "abbr":"AGO",
            "name":"Attorney General's Office",
            "slug":"ago"
        },
        "slug":"registrations"
    }
]

tx_path = ("/performance/transactions-explorer"
           "/service-details/"
           "bis-acas-elearning-registrations")
tx_full_url = "https://gov.uk{}".format(tx_path)

spotlight_path = ("/performance/training-resources"
                  "-on-workplace-relations/registrations")
spotlight_full_url = "https://gov.uk{}".format(spotlight_path)


def ordered_responses(spotlight_code):
    okay = Mock()
    okay.status_code = 200
    spotlight_response = Mock()
    spotlight_response.status_code = spotlight_code
    return [okay, spotlight_response]


class RedirectWriterTests(unittest.TestCase):
    @patch('requests.get')
    def test_redirects_produced_when_source_pages_exist(self, mock_get):
        mock_get().status_code = 200
        # to prevent the above being counted as a call
        mock_get.reset_mock()
        redirects = generate(MERGED_RECORDS)
        assert_that(redirects, equal_to([
            ['source', 'destination'],
            [tx_path, spotlight_path]
        ]))
        mock_get.assert_has_calls(
            [call(tx_full_url), call(spotlight_full_url)])

    @patch('requests.get')
    def test_no_redirect_if_no_existing_source_page(self, mock_get):
        mock_get().status_code = 404
        # to prevent the above being counted as a call
        mock_get.reset_mock()
        redirects = generate(MERGED_RECORDS)
        assert_that(redirects, equal_to([
            ['source', 'destination'],
        ]))
        mock_get.assert_called_once_with(tx_full_url)

    @patch('requests.get')
    def test_no_redirect_if_source_already_redirected(self, mock_get):
        mock_get().status_code = 301
        # to prevent the above being counted as a call
        mock_get.reset_mock()
        redirects = generate(MERGED_RECORDS)
        assert_that(redirects, equal_to([
            ['source', 'destination'],
        ]))
        mock_get.assert_called_once_with(tx_full_url)

    @patch('requests.get')
    def test_raises_exception_if_source_returns_unexpected_status_code(
            self, mock_get):
        mock_get().status_code = 501
        expected_exception_message = ("UNEXPECTED STATUS"
                                      " CODE 501 FOR {}".format(
                                          tx_full_url))
        with self.assertRaisesRegexp(Exception, expected_exception_message):
            generate(MERGED_RECORDS)

    @patch('requests.get')
    def test_redirects_produced_when_target_pages_exist(self, mock_get):
        mock_get.side_effect = ordered_responses(200)

        redirects = generate(MERGED_RECORDS)
        assert_that(redirects, equal_to([
            ['source', 'destination'],
            [tx_path, spotlight_path]
        ]))

    @patch('requests.get')
    def test_no_redirect_if_no_existing_target_page(self, mock_get):
        mock_get.side_effect = ordered_responses(404)

        redirects = generate(MERGED_RECORDS)
        assert_that(redirects, equal_to([
            ['source', 'destination'],
        ]))

    @patch('requests.get')
    def test_no_redirect_if_target_already_redirected(self, mock_get):
        mock_get.side_effect = ordered_responses(301)

        redirects = generate(MERGED_RECORDS)
        assert_that(redirects, equal_to([
            ['source', 'destination'],
        ]))

    @patch('requests.get')
    def test_raises_exception_if_target_returns_unexpected_status_code(
            self, mock_get):
        mock_get.side_effect = ordered_responses(501)
        expected_exception_message = ("UNEXPECTED STATUS"
                                      " CODE 501 FOR {}".format(
                                          spotlight_full_url))
        with self.assertRaisesRegexp(Exception, expected_exception_message):
            generate(MERGED_RECORDS)

    def test_redirect_csv_can_be_written(self):
        try:
            write([['bif', 'bof', 'foo'], ['1', 2], ['va lue', 'another']])
            with open('redirects.csv', 'r') as f:
                assert_that(f.read(), equal_to(
                    'bif,bof,foo\r\n1,2\r\nva lue,another\r\n'))
        finally:
            os.remove('redirects.csv')
