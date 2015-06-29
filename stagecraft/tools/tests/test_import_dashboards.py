import json

import random

from mock import Mock
from hamcrest import (
    assert_that, has_properties, has_entries,
    equal_to
)

from stagecraft.apps.dashboards.models import Dashboard, Module
from stagecraft.apps.dashboards.tests.factories.factories import(
    ModuleTypeFactory, DashboardFactory)
from stagecraft.apps.datasets.tests.factories import(
    DataSetFactory)

from ..spreadsheets import SpreadsheetMunger
from ..import_dashboards import (dashboard_from_record,
                                 set_dashboard_attributes,
                                 import_dashboard,
                                 determine_modules_for_dashboard)

with open('stagecraft/tools/fixtures/tx.json') as f:
    tx_worksheet = json.loads(f.read())

with open('stagecraft/tools/fixtures/names.json') as f:
    names_worksheet = json.loads(f.read())


def test_attributes_from_record():

    munger = SpreadsheetMunger({
        'names_transaction_name': 11,
        'names_transaction_slug': 12,
        'names_service_name': 9,
        'names_service_slug': 10,
        'names_tx_id': 19,
        'names_other_notes': 17,
        'names_notes': 3,
        'names_description': 8,
    })

    mock_account = Mock()
    mock_account.open_by_key()\
        .worksheet().get_all_values.return_value = tx_worksheet
    tx = munger.load_tx_worksheet(mock_account)

    mock_account = Mock()
    mock_account.open_by_key()\
        .worksheet().get_all_values.return_value = names_worksheet
    names = munger.load_names_worksheet(mock_account)

    record = munger.merge(tx, names)[0]

    dashboard = Dashboard()
    dashboard = set_dashboard_attributes(dashboard, record, False)

    assert_that(dashboard, has_properties({
        'title': record['name'],
        'description': record['description'],
        'costs': record['costs'],
        'other_notes': record['other_notes'],
        'dashboard_type': 'high-volume-transaction',
        'customer_type': record['customer_type'],
        'business_model': record['business_model'],
        'published': False
    }))


def test_truncated_slug_is_replaced():

    munger = SpreadsheetMunger({
        'names_transaction_name': 11,
        'names_transaction_slug': 12,
        'names_service_name': 9,
        'names_service_slug': 10,
        'names_tx_id': 19,
        'names_other_notes': 17,
        'names_notes': 3,
        'names_description': 8,
    })

    mock_account = Mock()
    mock_account.open_by_key() \
        .worksheet().get_all_values.return_value = tx_worksheet
    tx = munger.load_tx_worksheet(mock_account)

    mock_account = Mock()
    mock_account.open_by_key() \
        .worksheet().get_all_values.return_value = names_worksheet
    names = munger.load_names_worksheet(mock_account)

    record = munger.merge(tx, names)[0]
    truncated_slug = 'truncated-{}'.format(random.randrange(1e7))
    record['tx_truncated'] = truncated_slug

    dashboard = DashboardFactory(slug=truncated_slug)
    dashboard = dashboard_from_record(record)

    assert_that(dashboard, has_properties({
        'slug': record['tx_id']
    }))


def test_truncated_slug_is_replaced_in_modules():
    DataSetFactory(
        data_group__name='transactional-services',
        data_type__name='summaries')
    ModuleTypeFactory(name='kpi')
    ModuleTypeFactory(name='bar_chart_with_number')

    munger = SpreadsheetMunger({
        'names_transaction_name': 11,
        'names_transaction_slug': 12,
        'names_service_name': 9,
        'names_service_slug': 10,
        'names_tx_id': 19,
        'names_other_notes': 17,
        'names_notes': 3,
        'names_description': 8,
    })

    mock_account = Mock()
    mock_account.open_by_key() \
        .worksheet().get_all_values.return_value = tx_worksheet
    tx = munger.load_tx_worksheet(mock_account)

    mock_account = Mock()
    mock_account.open_by_key() \
        .worksheet().get_all_values.return_value = names_worksheet
    names = munger.load_names_worksheet(mock_account)

    record = munger.merge(tx, names)[0]
    truncated_slug = 'truncated-{}'.format(random.randrange(1e7))
    full_tx_id = record['tx_id']
    record['tx_id'] = truncated_slug

    DashboardFactory(slug=truncated_slug)
    summaries = [
        {
            'service_id': record['tx_id'],
            'type': 'quarterly',
            'cost_per_transaction': 0,
            'digital_takeup': 0
        },
        {
            'service_id': record['tx_id'],
            'type': 'seasonally-adjusted',
            'total_cost': 0
        },
        {
            'service_id': full_tx_id,
            'type': 'quarterly',
            'cost_per_transaction': 0,
            'digital_takeup': 0
        },
        {
            'service_id': full_tx_id,
            'type': 'seasonally-adjusted',
            'total_cost': 0
        }
    ]
    import_dashboard(record, summaries, dry_run=False)
    initial_modules = Module.objects.all()
    service_id_filters = set(
        [module.query_parameters['filter_by'][0] for
         module in initial_modules])
    assert_that(len(service_id_filters), equal_to(1))
    assert_that(
        service_id_filters.pop(),
        equal_to('service_id:{}'.format(truncated_slug)))

    record['tx_id'] = full_tx_id
    record['tx_truncated'] = truncated_slug

    import_dashboard(record, summaries, dry_run=False)
    new_modules = Module.objects.all()
    assert_that(len(new_modules), equal_to(len(initial_modules)))

    service_id_filters = set(
        [module.query_parameters['filter_by'][0] for
         module in new_modules])
    assert_that(len(service_id_filters), equal_to(1))
    assert_that(
        service_id_filters.pop(),
        equal_to('service_id:{}'.format(full_tx_id)))


def test_published_unmodified():
    """
    Unless publish is True, dashboard.published should
    not be modified if already set.
    """

    record = {
        'name': 'Test dashboard',
        'tx_id': 'test-dashboard',
        'department': {
            'abbr': 'DEPT',
            'name': 'Dept',
            'slug': 'dept'
        },
        'high_volume': False
    }
    dashboard = Dashboard()
    dashboard.published = True
    dashboard = set_dashboard_attributes(dashboard, record, False)

    assert_that(dashboard, has_properties({
        'title': record['name'],
        'published': True
    }))


def test_unset_published_modified():
    """
    If published is not set, it should be set to False unless
    the 'publish' param is True.
    """

    record = {
        'name': 'Test dashboard',
        'tx_id': 'test-dashboard',
        'department': {
            'abbr': 'DEPT',
            'name': 'Dept',
            'slug': 'dept'
        },
        'high_volume': False
    }
    dashboard = Dashboard()
    dashboard = set_dashboard_attributes(dashboard, record, False)

    assert_that(dashboard, has_properties({
        'title': record['name'],
        'published': False
    }))


def test_update_published():
    """
    If published is set, it should be set to True if
    the 'publish' param is True.
    """

    record = {
        'name': 'Test dashboard',
        'tx_id': 'test-dashboard',
        'department': {
            'abbr': 'DEPT',
            'name': 'Dept',
            'slug': 'dept'
        },
        'high_volume': False
    }
    dashboard = Dashboard()
    dashboard = set_dashboard_attributes(dashboard, record, True)

    assert_that(dashboard, has_properties({
        'title': record['name'],
        'published': True
    }))


def test_compulsory_modules():
    """
    These modules should always be present, regardless of the data available.
    """

    summaries = []
    module_types = determine_modules_for_dashboard(summaries, 'tx_id')

    assert_that(module_types, has_entries({
        'transactions_per_year': True,
        'transactions_per_quarter': True,
    }))


def test_digital_takeup_present_seasonal():
    summaries = [
        {
            'service_id': 'tx_id',
            'type': 'seasonally-adjusted',
            'digital_takeup': 240542,
        }
    ]
    module_types = determine_modules_for_dashboard(summaries, 'tx_id')

    assert_that(module_types, has_entries({
        'transactions_per_year': True,
        'transactions_per_quarter': True,
        'digital_takeup': True,
    }))


def test_digital_takeup_present_quarterly():
    summaries = [
        {
            'service_id': 'tx_id',
            'type': 'quarterly',
            'digital_takeup': 240542,
        }
    ]
    module_types = determine_modules_for_dashboard(summaries, 'tx_id')

    assert_that(module_types, has_entries({
        'transactions_per_year': True,
        'transactions_per_quarter': True,
        'digital_takeup': True,
    }))


def test_total_cost_present():
    summaries = [
        {
            'service_id': 'tx_id',
            'type': 'seasonally-adjusted',
            'total_cost': 240542,
        }
    ]
    module_types = determine_modules_for_dashboard(summaries, 'tx_id')

    assert_that(module_types, has_entries({
        'transactions_per_year': True,
        'transactions_per_quarter': True,
        'total_cost': True,
    }))


def test_cost_per_transaction_present():
    summaries = [
        {
            'service_id': 'tx_id',
            'type': 'seasonally-adjusted',
            'cost_per_transaction': 240542,
        }
    ]
    module_types = determine_modules_for_dashboard(summaries, 'tx_id')

    assert_that(module_types, has_entries({
        'transactions_per_year': True,
        'transactions_per_quarter': True,
        'cost_per_transaction': True,
    }))
