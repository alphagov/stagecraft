from mock import patch
from .spreadsheets import load
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
    result = load('beep', 'boop')
    result_path = 'stagecraft/tools/fixtures/spreadsheet_munging_result.json'
    with open(result_path, 'r') as f:
        assert_that(json.loads(f.read()), equal_to(result))
