import logging
import os
import sys

import requests

from django.db import IntegrityError

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


def import_dashboards(summaries, dry_run=False):
    try:
        username = os.environ['GOOGLE_USERNAME']
        password = os.environ['GOOGLE_PASSWORD']
    except KeyError:
        log.fatal("Please supply username (GOOGLE_USERNAME)\
                and password (GOOGLE_PASSWORD) as environment variables")
        sys.exit(1)

    loader = SpreadsheetMunger(positions={
        'names_name': 9,
        'names_slug': 10,
        'names_service_name': 11,
        'names_service_slug': 12,
        'names_tx_id_column': 19
    })
    records = loader.load_tx_worksheet(username, password)
    log.debug('Loaded {} records'.format(len(records)))

    for record in records:
        if not record['high_volume']:
            import_dashboard(summaries, record, dry_run)


def import_dashboard(summaries, record, dry_run=False):
    log.debug(record)
    try:
        dashboard = Dashboard.objects.get(slug=record['slug'])
        log.debug('Retrieved dashboard: {}'.format(record['slug']))
    except Dashboard.DoesNotExist:
        dashboard = create_dashboard(record, dry_run)
        log.debug('Creating dashboard: {}'.format(record['slug']))
    dataset = get_dataset()
    modules = []

    service_data = [
        data for data in summaries if data['service_id'] == record['slug']]
    quarterly_data = [
        datum for datum in service_data if datum['type'] == 'quarterly']
    seasonal_data = [
        datum for datum in service_data
        if datum['type'] == 'seasonally-adjusted']

    # Order in which modules are appended is significant
    # as it will affect how the dashboard displays.
    modules.append(make_tpy_module(record, dashboard, dataset, dry_run))

    for datum in seasonal_data:
        if datum.get('total_cost') is not None:
            modules.append(make_tc_module(record, dashboard, dataset, dry_run))
            break

    for datum in seasonal_data:
        if datum.get('cost_per_transaction') is not None:
            modules.append(
                make_cpt_module(record, dashboard, dataset, dry_run))
            break

    modules.append(make_tpq_module(record, dashboard, dataset, dry_run))

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
        modules.append(make_dtu_module(record, dashboard, dataset, dry_run))

    for idx, module in enumerate(modules):
        # Order is 1-indexed
        module.order = idx + 1
        if dry_run:
            # Use any old dashboard for its UUID.
            module.dashboard = Dashboard.objects.first()
            module.full_clean()
        else:
            try:
                module.save()
                log.debug('Added module: {}'.format(module.slug))
            except IntegrityError:
                log.debug('Module already exists: {}'.format(module.slug))


def get_dataset():
    return DataSet.objects.get(
        data_group__name='transactional-services',
        data_type__name='summaries')


def create_dashboard(record, dry_run=False):
    """
    Retrieve or create dashboard config for the record.
    """

    dashboard = Dashboard()
    dashboard.title = record['name']
    dashboard.slug = record['slug']
    dashboard.description = record['description']
    dashboard.description_extra = record['description_extra']
    dashboard.costs = record['costs']
    dashboard.other_notes = record['other_notes']

    if record.get('agency'):
        key = 'agency'
    else:
        key = 'department'
    try:
        organisation = Node.objects.get(abbreviation=record[key]['abbr'])
    except Node.DoesNotExist:
        if not dry_run:
            log.warn(
                'Organisation not found for record : {}'
                .format(record['slug']))
    if record['high_volume']:
        dashboard.dashboard_type = 'high-volume-transaction'
    else:
        dashboard.dashboard_type = 'transaction'
    dashboard.published = False
    if dry_run:
        dashboard.full_clean()
    else:
        dashboard.save()
    return dashboard


def make_module(dashboard, dataset, attributes, dry_run=False):
    module = Module()
    module.type = ModuleType.objects.get(name=attributes['module_type'])
    module.title = attributes['title']
    module.slug = attributes['slug']
    module.dashboard = dashboard
    module.query_params = attributes['query_params']
    module.options = attributes['options']
    module.data_set = dataset
    return module


def make_tc_module(record, dashboard, dataset, dry_run=False):
    attributes = {
        'module_type': 'kpi',
        'title': 'Total cost',
        'slug': 'total-cost',
        'query_params': {
            'filter_by': [
                'service_id:' + record['slug'],
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
    return make_module(dashboard, dataset, attributes, dry_run)


def make_cpt_module(record, dashboard, dataset, dry_run=False):
    attributes = {
        'module_type': 'kpi',
        'title': 'Cost per transaction',
        'slug': 'cost-per-transaction',
        'query_params': {
            'filter_by': [
                'service_id:' + record['slug'],
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
    return make_module(dashboard, dataset, attributes, dry_run)


def make_cpt_module(record, dashboard, dataset, dry_run=False):
    attributes = {
        'module_type': 'kpi',
        'title': 'Cost per transaction',
        'slug': 'cost-per-transaction',
        'query_params': {
            'filter_by': [
                'service_id:' + record['slug'],
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
    return make_module(dashboard, dataset, attributes, dry_run)


def make_tpy_module(record, dashboard, dataset, dry_run=False):
    attributes = {
        'module_type': 'kpi',
        'title': 'Transactions per year',
        'slug': 'transactions-per-year',
        'query_params': {
            'filter_by': [
                'service_id:' + record['slug'],
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
    return make_module(dashboard, dataset, attributes, dry_run)


def make_tpq_module(record, dashboard, dataset, dry_run=False):
    attributes = {
        'module_type': 'bar_chart_with_number',
        'title': 'Transactions per quarter',
        'slug': 'transactions-per-quarter',
        'query_params': {
            'filter_by': [
                'service_id:' + record['slug'],
                'type:seasonally-adjusted'
            ],
            'sort_by': '_timestamp:ascending'
        },
        'options': {
            'value-attribute': 'number_of_transactions',
            'axis-period': 'quarter'
        },
    }
    return make_module(dashboard, dataset, attributes, dry_run)


def make_dtu_module(record, dashboard, dataset, dry_run=False):
    attributes = {
        'module_type': 'bar_chart_with_number',
        'title': 'Digital take-up',
        'slug': 'digital-take-up-per-quarter',
        'query_params': {
            'filter_by': [
                'service_id:' + record['slug'],
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
    return make_module(dashboard, dataset, attributes, dry_run)


if __name__ == '__main__':
    dry_run = True
    if len(sys.argv) == 2:
        if sys.argv[1] == '--commit':
            dry_run = False
        else:
            log.fatal('Please specify --commit to create dashboards')
            sys.exit(1)
    try:
        summaries = requests.get(os.getenv('SUMMARIES_URL')).json()['data']
    except KeyError:
        log.fatal(
            "Please set SUMMARIES_URL to the endpoint for transactions data")
        sys.exit(1)

    import_dashboards(summaries, dry_run)
