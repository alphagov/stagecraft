import os
import json
from ..redirects import generate, write
from hamcrest import (
    assert_that, equal_to
)
import unittest

from mock import patch, Mock, call

result_path = 'stagecraft/tools/fixtures/spreadsheet_munging_result.json'
with open(result_path, 'r') as f:
    spreadsheets_data = json.loads(f.read())

result_path = 'stagecraft/tools/fixtures/long_spreadsheet_munging_result.json'
with open(result_path, 'r') as f:
    long_spreadsheets_data = json.loads(f.read())

tx_path = ("/performance/transactions-explorer"
           "/service-details/"
           "ago-bona-vacantia-referrals-of-estates-company-assets")
tx_full_url = "https://gov.uk{}".format(tx_path)

spotlight_path = ("/performance/trusts-estates/"
                  "referrals-estates-company-assets-bona-vacantia")
spotlight_full_url = "https://gov.uk{}".format(spotlight_path)

alphabetized_new_style = [
    [
        "Source",
        "Destination"
    ],
    [
        "/performance/transactions-explorer/service-details/"
        "ago-bona-vacantia-referrals-of-estates-company-assets",
        "/performance/trusts-estates/"
        "referrals-estates-company-assets-bona-vacantia"
    ],
    [
        "/performance/transactions-explorer/service-details/"
        "bis-acas-elearning-registrations",
        "/performance/training-resources-on-workplace-relations/"
        "registrations"
    ],
    [
        "/performance/transactions-explorer/service-details/"
        "zebrazebrazebra",
        "/performance/zebrazebrazebra/zebrazebrazebra"
    ]
]

alphabetized_old_style = [
    [
        "Source",
        "Destination"
    ],
    [
        "/performance/transactions-explorer/service-details/"
        "ago-bona-vacantia-referrals-of-estates-company-assets",
        "/performance/"
        "ago-bona-vacantia-referrals-of-estates-company-assets"
    ],
    [
        "/performance/transactions-explorer/service-details/"
        "bis-acas-elearning-registrations",
        "/performance/bis-acas-elearning-registrations"
    ],
    [
        "/performance/transactions-explorer/service-details/"
        "zebrazebrazebra",
        "/performance/zebrazebrazebra"
    ]
]


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
        redirects = generate(spreadsheets_data, True)
        assert_that(redirects, equal_to([
            ['Source', 'Destination'],
            [tx_path, spotlight_path]
        ]))
        mock_get.assert_has_calls(
            [call(tx_full_url), call(spotlight_full_url)])

    @patch('requests.get')
    def test_redirects_produced_when_source_pages_exist_and_old_slugs(
            self, mock_get):
        mock_get().status_code = 200
        # to prevent the above being counted as a call
        mock_get.reset_mock()
        redirects = generate(spreadsheets_data, False)
        old_slug_path = ("/performance/ago-bona-vacantia-"
                         "referrals-of-estates-company-assets")
        spotlight_full_url = "https://gov.uk{}".format(old_slug_path)
        assert_that(redirects, equal_to([
            ['Source', 'Destination'],
            [tx_path, old_slug_path]
        ]))
        mock_get.assert_has_calls(
            [call(tx_full_url), call(spotlight_full_url)])

    @patch('requests.get')
    def test_no_redirect_if_no_existing_source_page(self, mock_get):
        mock_get().status_code = 404
        # to prevent the above being counted as a call
        mock_get.reset_mock()
        redirects = generate(spreadsheets_data, True)
        assert_that(redirects, equal_to([
            ['Source', 'Destination'],
        ]))
        mock_get.assert_called_once_with(tx_full_url)

    @patch('requests.get')
    def test_no_redirect_if_source_already_redirected(self, mock_get):
        mock_get().status_code = 301
        # to prevent the above being counted as a call
        mock_get.reset_mock()
        redirects = generate(spreadsheets_data, True)
        assert_that(redirects, equal_to([
            ['Source', 'Destination'],
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
            generate(spreadsheets_data, True)

    @patch('requests.get')
    def test_redirects_produced_when_target_pages_exist(self, mock_get):
        mock_get.side_effect = ordered_responses(200)

        redirects = generate(spreadsheets_data, True)
        assert_that(redirects, equal_to([
            ['Source', 'Destination'],
            [tx_path, spotlight_path]
        ]))

    @patch('requests.get')
    def test_no_redirect_if_no_existing_target_page(self, mock_get):
        mock_get.side_effect = ordered_responses(404)

        redirects = generate(spreadsheets_data, True)
        assert_that(redirects, equal_to([
            ['Source', 'Destination'],
        ]))

    @patch('requests.get')
    def test_no_redirect_if_target_already_redirected(self, mock_get):
        mock_get.side_effect = ordered_responses(301)

        redirects = generate(spreadsheets_data, True)
        assert_that(redirects, equal_to([
            ['Source', 'Destination'],
        ]))

    @patch('requests.get')
    def test_raises_exception_if_target_returns_unexpected_status_code(
            self, mock_get):
        mock_get.side_effect = ordered_responses(501)
        expected_exception_message = ("UNEXPECTED STATUS"
                                      " CODE 501 FOR {}".format(
                                          spotlight_full_url))
        with self.assertRaisesRegexp(Exception, expected_exception_message):
            generate(spreadsheets_data, True)

    def test_redirect_csv_can_be_written(self):
        try:
            write([['bif', 'bof', 'foo'], ['1', 2], ['va lue', 'another']])
            with open('redirects.csv', 'r') as f:
                assert_that(f.read(), equal_to(
                    'bif,bof,foo\r\n1,2\r\nva lue,another\r\n'))
        finally:
            os.remove('redirects.csv')

    @patch('requests.get')
    def test_ordered_alphabetically_when_new_style(self, mock_get):
        mock_get().status_code = 200
        # to prevent the above being counted as a call
        mock_get.reset_mock()
        redirects = generate(long_spreadsheets_data, True)
        assert_that(redirects, equal_to(alphabetized_new_style))
        mock_get.assert_has_calls(
            [call(tx_full_url), call(spotlight_full_url)])

    @patch('requests.get')
    def test_ordered_alphabetically_when_old_style(
            self, mock_get):
        mock_get().status_code = 200
        # to prevent the above being counted as a call
        mock_get.reset_mock()
        redirects = generate(long_spreadsheets_data, False)
        old_slug_path = ("/performance/ago-bona-vacantia-"
                         "referrals-of-estates-company-assets")
        spotlight_full_url = "https://gov.uk{}".format(old_slug_path)
        assert_that(redirects, equal_to(alphabetized_old_style))
        mock_get.assert_has_calls(
            [call(tx_full_url), call(spotlight_full_url)])
