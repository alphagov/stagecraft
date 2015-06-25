import argparse
import os
import sys
from stagecraft.tools import get_credentials_or_die

import requests

import django
django.setup()

from django.db import IntegrityError
from django.db.utils import DataError
from django.core.exceptions import ValidationError

from stagecraft.tools.spreadsheets import SpreadsheetMunger

from stagecraft.apps.dashboards.models import Dashboard
from stagecraft.apps.dashboards.models import Module
from stagecraft.apps.dashboards.models import ModuleType
from stagecraft.apps.datasets.models import DataSet


def import_dashboards(summaries, update=False,
                      dry_run=True, publish=False):
    client_email, private_key = get_credentials_or_die()

    loader = SpreadsheetMunger(positions={
        'names_transaction_name': 11,
        'names_transaction_slug': 12,
        'names_service_name': 9,
        'names_service_slug': 10,
        'names_tx_id': 19,
        'names_other_notes': 17,
        'names_notes': 3,
        'names_description': 8
    })
    records = loader.load(client_email, private_key)
    print('Loaded {} records'.format(len(records)))

    failed_dashboards = []
    for record in records:
        loader.sanitise_record(record)
        try:
            import_dashboard(record, summaries, dry_run, publish, update)
        except (DataError, ValidationError) as e:
            print(e)
            failed_dashboards.append(record['tx_id'])

    if failed_dashboards:
        print('Failed dashboards: {}'.format(failed_dashboards))


def set_dashboard_attributes(dashboard, record, publish):

    dashboard.title = record['name']
    # Only set slug on new dashboards
    if dashboard.pk is None:
        dashboard.slug = record['tx_id']
    if record.get('description'):
        dashboard.description = record['description']
    if record.get('costs'):
        dashboard.costs = record['costs']
    if record.get('other_notes'):
        dashboard.other_notes = record['other_notes']
    if record.get('customer_type'):
        dashboard.customer_type = record['customer_type']
    if record.get('business_model'):
        dashboard.business_model = record['business_model']
    # Set type to high volume to distinguish from manually built dashboards.
    dashboard.dashboard_type = 'high-volume-transaction'
    dashboard.description_extra = ''

    if publish:
        dashboard.published = True
    # Don't modify published status if it exists.
    elif dashboard.published is None:
        dashboard.published = False

    return dashboard


def import_dashboard(record, summaries, dry_run=True, publish=False,
                     update=False):

    dashboard = dashboard_from_record(record)

    if update or not record['high_volume']:
        dashboard = set_dashboard_attributes(dashboard, record, publish)

    if dashboard.pk is None or dashboard.module_set.count() == 0:
        if not dry_run:
            dashboard.save()
        print('Updating modules on {}'.format(dashboard.slug))
        dataset = get_dataset()
        import_modules(dashboard, dataset, record, summaries, dry_run)

    if dry_run:
        dashboard.full_clean()
    else:
        dashboard.save()


def dashboard_from_record(record):
    def set_truncated_slug_to_full_slug(full_slug):
        dashboard.slug = full_slug
        print("Setting truncated slug to {}".format(full_slug))

    if 'tx_truncated' in record and \
            Dashboard.objects.filter(slug=record['tx_truncated']).count():
        dashboard = Dashboard.objects.get(slug=record['tx_truncated'])
        set_truncated_slug_to_full_slug(record['tx_id'])

    elif 'tx_truncated' in record and list(Dashboard.objects.by_tx_id(
            record['tx_truncated'])):
        dashboard = list(
            Dashboard.objects.by_tx_id(record['tx_truncated'])).pop()
        set_truncated_slug_to_full_slug(record['tx_id'])

    elif Dashboard.objects.filter(slug=record['tx_id']).count():
        dashboard = Dashboard.objects.get(slug=record['tx_id'])

    elif list(Dashboard.objects.by_tx_id(record['tx_id'])):
        dashboard = list(Dashboard.objects.by_tx_id(record['tx_id'])).pop()

    else:
        dashboard = Dashboard()
        dashboard.slug = record['tx_id']

    return dashboard


def determine_modules_for_dashboard(summaries, tx_id):
    """
    Inspect the summary data for a given tx_id and determine
    whether modules should be created for the different data types.
    """

    module_types = {
        'transactions_per_year': True,
        'transactions_per_quarter': True
    }
    service_data = [data for data in summaries if data['service_id'] == tx_id]
    quarterly_data = [datum for datum in service_data
                      if datum['type'] == 'quarterly']
    seasonal_data = [datum for datum in service_data
                     if datum['type'] == 'seasonally-adjusted']

    for datum in seasonal_data:
        if datum.get('total_cost') is not None:
            module_types['total_cost'] = True
            break

    for datum in seasonal_data:
        if datum.get('cost_per_transaction') is not None:
            module_types['cost_per_transaction'] = True
            break

    digital_takeup = False
    for datum in seasonal_data:
        if datum.get('digital_takeup'):
            digital_takeup = True
            break
    for datum in quarterly_data:
        if datum.get('digital_takeup'):
            digital_takeup = True
            break
    if digital_takeup:
        module_types['digital_takeup'] = True

    return module_types


def import_modules(dashboard, dataset, record, summaries, dry_run):

    module_types = determine_modules_for_dashboard(summaries, record['tx_id'])
    modules = []

    # Order in which modules are appended is significant
    # as it will affect how the dashboard displays.
    if module_types.get('transactions_per_year'):
        modules.append(import_tpy_module(record, dashboard, dataset))
    if module_types.get('total_cost'):
        modules.append(import_tc_module(record, dashboard, dataset))
    if module_types.get('cost_per_transaction'):
        modules.append(import_cpt_module(record, dashboard, dataset))
    if module_types.get('transactions_per_year'):
        modules.append(import_tpq_module(record, dashboard, dataset))
    if module_types.get('digital_takeup'):
        modules.append(import_dtu_module(record, dashboard, dataset))

    for idx, module in enumerate(modules):
        # Order is 1-indexed
        module.order = idx + 1
        if not dry_run:
            try:
                module.save()
            except IntegrityError as e:
                print('Error saving module {}: {}'.format(module.slug, str(e)))


def get_dataset():
    return DataSet.objects.get(
        data_group__name='transactional-services',
        data_type__name='summaries')


def get_or_create_module(dashboard, module_slug):
    try:
        module = Module.objects.get(dashboard=dashboard, slug=module_slug)
    except Module.DoesNotExist:
        module = Module()
    return module


def set_module_attributes(module, dashboard, dataset, attributes):
    module.type = ModuleType.objects.get(name=attributes['module_type'])
    module.title = attributes['title']
    module.slug = attributes['slug']
    module.dashboard = dashboard
    module.query_parameters = attributes['query_params']
    module.options = attributes['options']
    module.data_set = dataset
    return module


def import_tc_module(record, dashboard, dataset):
    attributes = {
        'module_type': 'kpi',
        'title': 'Total cost',
        'slug': 'total-cost',
        'query_params': {
            'filter_by': [
                'service_id:' + record['tx_id'],
                'type:seasonally-adjusted'
            ],
            'sort_by': '_timestamp:descending'
        },
        'options': {
            'value-attribute': 'total_cost',
            'format': {
                'type': 'currency',
                'magnitude': True,
                'sigfigs': 3
            },
            'classes': 'cols3',
        },
    }
    module = get_or_create_module(dashboard, attributes['slug'])
    return set_module_attributes(module, dashboard, dataset, attributes)


def import_cpt_module(record, dashboard, dataset):
    attributes = {
        'module_type': 'kpi',
        'title': 'Cost per transaction',
        'slug': 'cost-per-transaction',
        'query_params': {
            'filter_by': [
                'service_id:' + record['tx_id'],
                'type:seasonally-adjusted'
            ],
            'sort_by': '_timestamp:descending'
        },
        'options': {
            'value-attribute': 'cost_per_transaction',
            'format': {
                'type': 'currency',
                'pence': True
            },
            'classes': 'cols3',
        },
    }
    module = get_or_create_module(dashboard, attributes['slug'])
    return set_module_attributes(module, dashboard, dataset, attributes)


def import_tpy_module(record, dashboard, dataset):
    attributes = {
        'module_type': 'kpi',
        'title': 'Transactions per year',
        'slug': 'transactions-per-year',
        'query_params': {
            'filter_by': [
                'service_id:' + record['tx_id'],
                'type:seasonally-adjusted'
            ],
            'sort_by': '_timestamp:descending'
        },
        'options': {
            'value-attribute': 'number_of_transactions',
            'format': {
                'type': 'number',
                'magnitude': True,
                'sigfigs': 3
            },
            'classes': 'cols3',
        },
    }
    module = get_or_create_module(dashboard, attributes['slug'])
    return set_module_attributes(module, dashboard, dataset, attributes)


def import_tpq_module(record, dashboard, dataset):
    attributes = {
        'module_type': 'bar_chart_with_number',
        'title': 'Transactions per quarter',
        'slug': 'transactions-per-quarter',
        'query_params': {
            'filter_by': [
                'service_id:' + record['tx_id'],
                'type:quarterly'
            ],
            'sort_by': '_timestamp:ascending'
        },
        'options': {
            'value-attribute': 'number_of_transactions',
            'axis-period': 'quarter'
        },
    }
    module = get_or_create_module(dashboard, attributes['slug'])
    return set_module_attributes(module, dashboard, dataset, attributes)


def import_dtu_module(record, dashboard, dataset):
    attributes = {
        'module_type': 'bar_chart_with_number',
        'title': 'Digital take-up',
        'slug': 'digital-take-up-per-quarter',
        'query_params': {
            'filter_by': [
                'service_id:' + record['tx_id'],
                'type:quarterly'
            ],
            'sort_by': '_timestamp:ascending'
        },
        'options': {
            'value-attribute': 'digital_takeup',
            'format': {'type': 'percent'},
            'axis-period': 'quarter',
            'axes': {
                'y': [{'label': 'Percentage digital take-up'}]
            }
        },
    }
    module = get_or_create_module(dashboard, attributes['slug'])
    return set_module_attributes(module, dashboard, dataset, attributes)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("--update",
                        help="update dasbboard attributes",
                        action="store_true")
    parser.add_argument("--commit",
                        help="save changes to database",
                        action="store_true")
    parser.add_argument("--publish",
                        help="publish all dashboards",
                        action="store_true")
    args = parser.parse_args()
    if args.update:
        print("Updating all dashboard attributes")
        update = True
    else:
        update = False
    if args.commit:
        print("Committing changes")
        dry_run = False
    else:
        dry_run = True
    if args.publish:
        print("Publishing all dashboards")
        publish = True
    else:
        publish = False

    if os.getenv('SUMMARIES_URL'):
        summaries = requests.get(os.getenv('SUMMARIES_URL')).json()['data']
    else:
        print("Please set SUMMARIES_URL to the endpoint for transactions data")
        sys.exit(1)

    import_dashboards(summaries, update, dry_run, publish)
    print('Finished')
