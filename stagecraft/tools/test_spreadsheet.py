from mock import patch
from hamcrest import (
    assert_that, equal_to
)

from .spreadsheets import SpreadsheetMunger


TX_RECORDS = [
    {
        'agency': {
            'abbr': 'CPS',
            'name': 'Crown Prosecution Service',
            'slug': 'cps'
        },
        'costs': '',
        'department': {
            'abbr': 'AGO',
            'name': "Attorney General's Office",
            'slug': 'ago'
        },
        'description': '',
        'description_extra': '',
        'high_volume': False,
        'name': 'Witness expenses: reimbursements',
        'other_notes': '',
        'tx_id': 'ago-reimbursing-witness-expenses'
    }
]

NAMES_RECORDS = [
    {
        'name': 'Court actions',
        'description': 'description',
        'slug': 'court-actions-',
        'tx_id': 'ago-reimbursing-witness-expenses'
    }
]

def test_merge():
    loader = SpreadsheetMunger({
        'names_description': 8,
        'names_name': 11,
        'names_slug': 12,
        'names_notes': 17,
        'names_other_notes': 18,
        'names_tx_id': 19,
    })
    merged = loader._merge(TX_RECORDS, NAMES_RECORDS)
    assert_that(merged[0]['tx_id'], 'ago-reimbursing-witness-expenses')
    assert_that(merged[0]['name'], 'Court actions')
    assert_that(merged[0]['description'], 'description')

