import argparse
import logging
import os
import sys

import requests

from django.db import IntegrityError
from django.core.exceptions import ValidationError

from .spreadsheets import SpreadsheetMunger

from stagecraft.apps.dashboards.models import Dashboard
from stagecraft.apps.dashboards.models import Module
from stagecraft.apps.dashboards.models import ModuleType
from stagecraft.apps.organisation.models import Node
from stagecraft.apps.datasets.models import DataSet


log = logging.getLogger(__name__)
log.setLevel(logging.DEBUG)
handler = logging.StreamHandler()
handler.setLevel(logging.DEBUG)
log.addHandler(handler)


def import_dashboards(summaries, update_all=False,
                      dry_run=True, publish=False):
    try:
        username = os.environ['GOOGLE_USERNAME']
        password = os.environ['GOOGLE_PASSWORD']
    except KeyError:
        log.fatal("Please supply username (GOOGLE_USERNAME)\
                and password (GOOGLE_PASSWORD) as environment variables")
        sys.exit(1)

    loader = SpreadsheetMunger(positions={
        'names_description': 8,
        'names_service_name': 9,
        'names_service_slug': 10,
        'names_transaction_name': 11,
        'names_transaction_slug': 12,
        'names_notes': 17,
        'names_other_notes': 18,
        'names_tx_id': 19,
    })
    records = loader.load(username, password)
    log.debug('Loaded {} records'.format(len(records)))

    failed_dashboards = []
    for record in records:
        if update_all or not record['high_volume']:
            loader.sanitise_record(record)
            try:
                import_dashboard(record, summaries, dry_run, publish)
            except ValidationError:
                failed_dashboards.append(record)

    log.error('Failed dashboards: {}'.format(failed_dashboards))


def set_dashboard_attributes(dashboard, record, dry_run, publish):

    dashboard.title = record['name']
    # Only set slug on new dashboards
    if dashboard.pk is None:
        dashboard.slug = record['tx_id']
    if record.get('description'):
        dashboard.description = record['description']
    if record.get('description_extra'):
        dashboard.description_extra = record['description_extra']
    if record.get('costs'):
        dashboard.costs = record['costs']
    if record.get('other_notes'):
        dashboard.other_notes = record['other_notes']
    if record.get('customer_type'):
        dashboard.customer_type = record['customer_type']
    if record.get('business_model'):
        dashboard.business_model = record['business_model']

    if dashboard.organisation is None:
        if record.get('agency'):
            key = 'agency'
        else:
            key = 'department'
        try:
            org = Node.objects.get(abbreviation=record[key]['abbr'])
            dashboard.organisation = org
        except Node.DoesNotExist:
            if not dry_run:
                log.warn('Organisation not found for record : {}' \
                    .format(record['tx_id']))

    if record['high_volume']:
        dashboard.dashboard_type = 'high-volume-transaction'
    else:
        dashboard.dashboard_type = 'transaction'

    if publish:
        dashboard.published = True
    # Don't modify published status if it exists.
    elif dashboard.published is None:
        dashboard.published = False

    return dashboard


def import_dashboard(record, summaries, dry_run=True, publish=False):

    log.debug(record)
    try:
        dashboard = Dashboard.objects.get(slug=record['tx_id'])
        log.debug('Retrieved dashboard: {}'.format(record['tx_id']))
    except Dashboard.DoesNotExist:
        dashboard = Dashboard()
        log.debug('Creating dashboard: {}'.format(record['tx_id']))

    dashboard = set_dashboard_attributes(dashboard, record, dry_run, publish)
    if dry_run:
        dashboard.full_clean()
    else:
        dashboard.save()

    dataset = get_dataset()
    import_modules(dashboard, dataset, record, summaries)


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


def import_modules(dashboard, dataset, record, summaries):

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
                log.debug('Added module: {}'.format(module.slug))
            except IntegrityError as e:
                log.error(
                    'Error saving module {}: {}'.format(module.slug, str(e)))


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
                'type:seasonally-adjusted'
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
                'type:seasonally-adjusted'
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
    parser.add_argument("--all",
                        help="update all (not just low volume) dashboards",
                        action="store_true")
    parser.add_argument("--commit",
                        help="save changes to database",
                        action="store_true")
    parser.add_argument("--publish",
                        help="publish all dashboards",
                        action="store_true")
    args = parser.parse_args()
    if args.all:
        log.info("Updating all dashboards")
        update_all = True
    else:
        update_all = False
    if args.commit:
        log.info("Committing changes")
        dry_run = False
    else:
        dry_run = True
    if args.publish:
        log.info("Publishing all dashboards")
        publish = True
    else:
        publish = False

    if os.getenv('SUMMARIES_URL'):
        summaries = requests.get(os.getenv('SUMMARIES_URL')).json()['data']
    else:
        log.fatal(
            "Please set SUMMARIES_URL to the endpoint for transactions data")
        sys.exit(1)

    import_dashboards(summaries, update_all, dry_run, publish)
