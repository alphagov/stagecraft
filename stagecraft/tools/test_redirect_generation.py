import os
import json
from .redirects import generate, write
from hamcrest import (
    assert_that, equal_to
)

from mock import patch

result_path = 'stagecraft/tools/fixtures/spreadsheet_munging_result.json'
with open(result_path, 'r') as f:
    spreadsheets_data = json.loads(f.read())


@patch('requests.get')
def test_redirects_produced_when_pages_exist(mock_get):
    mock_get().status_code = 200
    # to prevent the above being counted as a call
    mock_get.reset_mock()
    redirects = generate(spreadsheets_data)
    assert_that(redirects, equal_to([
        ['source', 'destination'],
        ['/performance/transactions-explorer/service-details/bis-acas-elearning-registrations', '/performance/training-resources-on-workplace-relations/registrations']  # noqa
    ]))
    mock_get.assert_called_once_with('https://gov.uk/performance/transactions-explorer/service-details/bis-acas-elearning-registrations')  # noqa


@patch('requests.get')
def test_no_redirect_if_no_existing_page(mock_get):
    mock_get().status_code = 404
    # to prevent the above being counted as a call
    mock_get.reset_mock()
    redirects = generate(spreadsheets_data)
    assert_that(redirects, equal_to([
        ['source', 'destination'],
    ]))
    mock_get.assert_called_once_with('https://gov.uk/performance/transactions-explorer/service-details/bis-acas-elearning-registrations')  # noqa


def test_no_redirect_csv_written():
    try:
        write([['bif', 'bof', 'foo'], ['1', 2], ['va lue', 'another']])
        with open('redirects.csv', 'r') as f:
            assert_that(f.read(), equal_to(
                'bif,bof,foo\r\n1,2\r\nva lue,another\r\n'))
    finally:
        os.remove('redirects.csv')
