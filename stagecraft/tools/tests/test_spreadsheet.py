from mock import patch
from ..spreadsheets import SpreadsheetMunger
import json
from hamcrest import (
    assert_that, equal_to
)

with open('stagecraft/tools/fixtures/tx.json') as f:
    tx_worksheet = json.loads(f.read())

with open('stagecraft/tools/fixtures/names.json') as f:
    names_worksheet = json.loads(f.read())


@patch('gspread.login')
def test_load(mock_login):
    def get_appropriate_spreadsheet():
        return [tx_worksheet, names_worksheet]

    mock_login().open_by_key().worksheet().get_all_values.side_effect = get_appropriate_spreadsheet()  # noqa
    munger = SpreadsheetMunger(positions={
        'names_name': 6,
        'names_slug': 7,
        'names_service_name': 4,
        'names_service_slug': 5,
        'names_tx_id_column': 16
    })
    result = munger.load('beep', 'boop')
    with open('stagecraft/tools/fixtures/result.json', 'r') as f:
        assert_that(json.loads(f.read()), equal_to(result))
