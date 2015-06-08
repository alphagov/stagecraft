import os
import requests
import sys
import json

from collections import defaultdict

import django
django.setup()

from django.db.utils import DataError, IntegrityError

from stagecraft.apps.organisation.models import Node, NodeType
from stagecraft.apps.dashboards.models import Dashboard

from stagecraft.tools.spreadsheets import SpreadsheetMunger


class WhatHappened:
    happenings = defaultdict(list)

    def this_happened(self, key, value):
        self.happenings[key] = value

    def add_to_what_happened(self, key, value):
        if key in self.happenings:
            self.happenings[key] = self.happenings[key] + value
        else:
            self.this_happened(key, value)

    def get(self, key):
        if key in self.happenings:
            return self.happenings[key]
        else:
            return []


WHAT_HAPPENED = WhatHappened()


def get_govuk_organisations():
    """
    Fetch organisations from the GOV.UK API. This is the canonical source.
    """

    def get_page(page):
        response = requests.get(
            'https://www.gov.uk/api/organisations?page={}'.format(page))
        return response.json()

    first_page = get_page(1)
    results = first_page['results']

    for page_num in range(2, first_page['pages'] + 1):
        page = get_page(page_num)
        results = results + page['results']

    # Remove any organisations that have closed.
    results = \
        [org for org in results if org['details']['closed_at'] is None]
    return results


def load_data(client_email, private_key):
    spreadsheets = SpreadsheetMunger({
        'names_transaction_name': 11,
        'names_transaction_slug': 12,
        'names_service_name': 9,
        'names_service_slug': 10,
        'names_tx_id': 19,
        'names_other_notes': 17,
        'names_notes': 3,
        'names_description': 8
    })
    records = spreadsheets.load(client_email, private_key)
    govuk_response = get_govuk_organisations()
    return records, govuk_response


def load_organisations(client_email, private_key):
    WHAT_HAPPENED.this_happened(
        'dashboards_at_start', list(Dashboard.objects.all()))

    # Remove existing refs to organisations from dashboards.
    remove_dashboard_refs_to_orgs()

    WHAT_HAPPENED.this_happened(
        'total_nodes_before', [node for node in Node.objects.all()])
    records, govuk_response = load_data(client_email, private_key)

    WHAT_HAPPENED.this_happened('organisations', govuk_response)
    WHAT_HAPPENED.this_happened('transactions', records)

    org_dict = create_org_dict(records, govuk_response)
    create_nodes(org_dict)

    succeeded = []
    failed = []
    for record in records:
        if associate_with_dashboard(record):
            succeeded.append(record)
        else:
            failed.append(record)
    WHAT_HAPPENED.this_happened(
        'records_matched_with_dashboards', succeeded)
    WHAT_HAPPENED.this_happened(
        'records_not_matched_with_dashboards', failed)
    WHAT_HAPPENED.this_happened(
        'total_nodes_after', list(Node.objects.all()))
    WHAT_HAPPENED.this_happened(
        'dashboards_at_end', list(Dashboard.objects.all()))
    return WHAT_HAPPENED.happenings


def remove_dashboard_refs_to_orgs():
    for dashboard in Dashboard.objects.all():
        # TODO: re-associate non TxEx dashboards to organisations.
        dashboard.organisation = None
        dashboard.transaction_cache = None
        dashboard.service_cache = None
        dashboard.agency_cache = None
        dashboard.department_cache = None
        dashboard.save()
    Node.objects.all().delete()


def create_org_dict(records, govuk_response):

    # Query GOV.UK for depts and agencies.
    govuk_org_dict = create_govuk_org_dict(govuk_response)
    govuk_org_dict = key_govuk_org_dict_by_abbreviation(govuk_org_dict)

    # Load the spreadsheet records for services/transactions.
    full_org_dict = add_records_to_org_dict(govuk_org_dict, records)
    full_org_dict = add_parents_to_records(full_org_dict, records)
    return full_org_dict


def create_govuk_org_dict(organisations):

    # Build dictionary keyed by org ID from GOV.UK API response.
    govuk_org_dict = {}
    for org in organisations:
        govuk_org_dict[org['id']] = {
            'name': org['title'],
            'slug': org['details']['slug'],
            'abbreviation': org['details']['abbreviation'],
            'typeOf': types_dict[org['format']],
            'parents': []
        }

    # Iterate organisations again, assigning parents.
    for org in organisations:
        for parent in org['parent_organisations']:
            abbr = govuk_org_dict[parent['id']]['abbreviation']
            if abbr:
                parent_abbr = abbr
            elif govuk_org_dict[parent['id']]['name']:
                parent_abbr = govuk_org_dict[parent['id']]['name']

            govuk_org_dict[org['id']]['parents'].append(
                (parent_abbr.lower()))

    return govuk_org_dict


def key_govuk_org_dict_by_abbreviation(govuk_org_dict):
    """
    Create dictionary keyed on dept/agency abbreviation for matching
    against abbreviations in the transactions explorer spreadsheet.
    """

    org_dict = {}
    duplicates = defaultdict(list)
    for org_id, org in govuk_org_dict.items():
        # If the abbreviation is already in the dict, record the
        # organisation as a duplicate.
        if org['abbreviation'].lower() in org_dict:
            if not duplicates.get([org['abbreviation'].lower()]):
                duplicates[org['abbreviation'].lower()].append(
                    org_dict[org['abbreviation'].lower()])
            duplicates[org['abbreviation'].lower()].append(org)
            org_dict[org['name'].lower()] = org
        else:
            # If organisation does not have an abbreviation, use the name
            # as the key.
            if org['abbreviation'].lower():
                org_dict[org['abbreviation'].lower()] = org
            else:
                org_dict[org['name'].lower()] = org

    WHAT_HAPPENED.this_happened(
        'duplicate_dept_or_agency_abbreviations',
        [(abbr, tx) for abbr, tx in duplicates.items()])
    return org_dict


def add_records_to_org_dict(org_dict, records):
    """
    Iterate records and create organisation entries for the service
    and/or transaction.
    """

    duplicate_transactions = []
    duplicate_services = []
    for record in records:
        if transaction_name(record) in org_dict:
            duplicate_transactions.append(transaction_name(record))
        if service_name(record) is not None and\
                service_name(record) in org_dict:
            duplicate_services.append(service_name(record))

        if service_name(record) is not None:
            org_dict[service_name(record)] = {
                'name': service_name(record),
                'slug': service_slug(record),
                'abbreviation': None,
                'typeOf': 'service',
                'parents': []
            }
            org_dict[transaction_name(record)] = {
                'name': transaction_name(record),
                'slug': transaction_slug(record),
                'abbreviation': None,
                'typeOf': 'transaction',
                'parents': [service_name(record)]
            }
        else:
            org_dict[transaction_name(record)] = {
                'name': transaction_name(record),
                'slug': transaction_slug(record),
                'abbreviation': None,
                'typeOf': 'service',
                'parents': []
            }

    WHAT_HAPPENED.this_happened('duplicate_services', duplicate_services)
    WHAT_HAPPENED.this_happened('duplicate_transactions',
                                duplicate_transactions)
    return org_dict


def add_parents_to_records(org_dict, records):
    """
    Add parent organisation(s) to the spreadsheet records.
    """

    successfully_linked = []
    failed_to_link = []

    for record in records:
        # Assumes departments are always parents of agencies.
        success = False
        if record.get('agency'):
            success, link = associate_record_parents(
                record, org_dict, 'agency')
        elif record.get('department'):
            success, link = associate_record_parents(
                record, org_dict, 'department')
        else:
            print(
                "Failed on record with no department or agency: {}"
                .format(record['name']))
        if success:
            successfully_linked.append(link)
        else:
            failed_to_link.append(link)

    WHAT_HAPPENED.this_happened('link_to_parents_found', successfully_linked)
    WHAT_HAPPENED.this_happened('link_to_parents_not_found', failed_to_link)
    return org_dict


def associate_record_parents(record, org_dict, typeOf):
    """
    Associate parent dept/agencies to a record using the org_dict. typeOf
    is 'department' or 'agency'.
    """

    parent_by_abbr = org_dict.get(record[typeOf]['abbr'].lower())
    parent_by_name = org_dict.get(record[typeOf]['name'].lower())

    if record[typeOf].get('abbr') and parent_by_abbr:
        parent = parent_by_abbr
        parent['typeOf'] = typeOf
        parent['slug'] = record[typeOf]['slug']
        parent_identifier = parent['abbreviation'].lower()
    elif record[typeOf].get('name') and parent_by_name:
        parent = parent_by_name
        parent['typeOf'] = typeOf
        parent['slug'] = record[typeOf]['slug']
        parent_identifier = parent['name'].lower()
    else:
        return False, (record[typeOf], None)

    # Add the dept/agency as the parent of the record (service or transaction).
    if service_name(record) is not None:
        org_dict[service_name(record)]['parents'].append(
            parent_identifier)
    else:
        org_dict[transaction_name(record)]['parents'].append(
            parent_identifier)
    return True, (record[typeOf], parent)


def create_nodes(org_dict):
    created_nodes = []
    key_to_uuid = {}
    for key, node_dict in org_dict.items():
        node = get_or_create_node(node_dict)
        if node:
            if node.abbreviation:
                key_to_uuid[node.abbreviation] = node.id
            if node.name:
                key_to_uuid[node.name] = node.id
            created_nodes.append((node, node_dict['parents']))
    save_parent_associations(created_nodes, key_to_uuid)


def get_or_create_node(node_dict):
    node_type, _ = NodeType.objects.get_or_create(name=node_dict['typeOf'])
    try:
        defaults = {
            'typeOf': node_type
        }
        if node_dict.get('abbreviation'):
            defaults['abbreviation'] = node_dict['abbreviation'].lower()
        node, created = Node.objects.get_or_create(
            name=node_dict['name'],
            slug=node_dict['slug'],
            defaults=defaults
        )

        if created:
            WHAT_HAPPENED.add_to_what_happened(
                'created_nodes', [node_dict])
        elif(node_dict not in WHAT_HAPPENED.get('created_nodes')
             and node_dict not in WHAT_HAPPENED.get('existing_nodes')):
            WHAT_HAPPENED.add_to_what_happened('existing_nodes', [node_dict])

    except DataError as e:
        WHAT_HAPPENED.add_to_what_happened(
            'unable_data_error_nodes', [e])
        WHAT_HAPPENED.add_to_what_happened(
            'unable_data_error_nodes_msgs', [e.message])
        WHAT_HAPPENED.add_to_what_happened(
            'unable_to_find_or_create_nodes', [node_dict])
        return False
    except IntegrityError as e:
        WHAT_HAPPENED.add_to_what_happened(
            'unable_existing_nodes_diff_details', [e])
        WHAT_HAPPENED.add_to_what_happened(
            'unable_existing_nodes_diff_details_msgs', [e.message])
        WHAT_HAPPENED.add_to_what_happened(
            'unable_to_find_or_create_nodes', [node_dict])
        return False
    return node


def save_parent_associations(created_nodes, key_to_uuid):
    total_parents = []
    total_parents_found = []
    for node, parents in created_nodes:
        parent_uuids = []
        for parent in parents:
            if parent in key_to_uuid:
                # Prevent a node being its own parent.
                if node.id == key_to_uuid[parent]:
                    print("A node tried to be its own parent: {}".format(node))
                else:
                    parent_uuids.append(key_to_uuid[parent])
        total_parents += parents
        total_parents_found += parent_uuids
        if parent_uuids:
            node.parents.add(*parent_uuids)

    WHAT_HAPPENED.this_happened('total_parents_found', total_parents_found)
    WHAT_HAPPENED.this_happened('total_parents', total_parents)


def associate_with_dashboard(record):
    try:
        transaction = Node.objects.get(name=record['name'])
    except DataError as e:
        print("Couldn't get org with name {}, error was {}. ",
              "Trying again with {}".
              format(transaction_name(record).encode('utf-8'),
                     e.message, transaction_name_latin1(record)))
        transaction = Node.objects.get(name=record['name']).first()

    dashboards = []
    if transaction is not None:
        dashboards = Dashboard.objects.by_tx_id(record['tx_id'])
        for dashboard in dashboards:
            existing_org = dashboard.organisation
            dashboard.organisation = transaction
            # Denormalise so we can query easily later.
            for node in transaction.get_ancestors():
                if node.typeOf.name == 'department':
                    dashboard.department_cache = node
                elif node.typeOf.name == 'agency':
                    dashboard.agency_cache = node
                elif node.typeOf.name == 'service':
                    dashboard.service_cache = node
                elif node.typeOf.name == 'transaction':
                    dashboard.transaction_cache = node
            dashboard.save()

            # Log if the new parents do not contain the dashboard's old
            # organisation.
            if existing_org and existing_org not in \
               list(dashboard.organisation.get_ancestors()):
                print("Existing org {} for dashboard {}"
                      "not in new ancestors {}".format(
                          existing_org.name, dashboard.title,
                          [org.name for org
                           in dashboard.organisation.get_ancestors()]))
    return dashboards


def service_name(tx):
    if tx.get('service'):
        return tx['service']['name'].encode('utf-8').decode('utf-8')
    return None


def service_slug(tx):
    if tx.get('service'):
        return tx['service']['slug']
    return None


def transaction_name(tx):
    return tx['name'].encode('utf-8').decode('utf-8')


def transaction_name_latin1(tx):
    return tx['name'].encode('latin1', 'ignore').decode('latin1')


def transaction_slug(tx):
    return tx['slug']


def add_type_to_parent(parent, typeOf):
    parent['typeOf'] = typeOf
    return parent


# These may not be 100% accurate however the derived
# typeOf will be overwritten with more certain information
# based on iterating through all tx rows in build_up_node_dict.
# We use this to to get the full org graph with types even when orgs are
# not associated with a transaction in txex. This is the best guess mapping.
types_dict = {
    "Advisory non-departmental public body": 'agency',
    "Tribunal non-departmental public body": 'agency',
    "Sub-organisation": 'agency',
    "Executive agency": 'agency',
    "Devolved administration": 'agency',
    "Ministerial department": 'department',
    "Non-ministerial department": 'department',
    "Executive office": 'agency',
    "Civil Service": 'agency',
    "Other": 'agency',
    "Executive non-departmental public body": 'agency',
    "Independent monitoring body": 'agency',
    "Public corporation": 'agency'
}


def report_what_happened(happened):
    expected_happenings = {
        'link_to_parents_not_found': 90,
        'duplicate_services': 551,
        'unable_data_error_nodes': 3,
        'total_parents': 1925,
        'total_nodes_after': 1877,
        'transactions': 790,
        'duplicate_dep_or_agency_abbreviations': 3,
        'transactions_not_associated_with_dashboards': 697,
        'organisations': 894,
        'total_nodes_before': 0,
        'link_to_parents_found': 700,
        'transactions_associated_with_dashboards': 93,
        'duplicate_transactions': 32,
        'dashboards_at_start': 874,
        'existing_nodes': 7,
        'unable_to_find_or_create_nodes': 6,
        'total_parents_found': 1882,
        'created_nodes': 1877,
        'dashboards_at_end': 874,
        'unable_existing_nodes_diff_details': 3}
    for key, things in happened.items():
        print(key)
        print(len(things))
    print('unable_existing_nodes_diff_details_msgs')
    print(len(set(happened['unable_existing_nodes_diff_details_msgs'])))
    print('unable_data_error_nodes_msgs')
    print(len(set(happened['unable_data_error_nodes_msgs'])))

    new_happened_counts = {}
    expected = True
    for key, things in happened.items():
        if key in expected_happenings:
            new_happened_counts[key] = len(things)
            if not expected_happenings[key] == len(things):
                expected = False
                print("{} should have been {} but was {}".format(
                    key, expected_happenings[key], len(things)))
        else:
            print("something happened we aren't tracking:")
            print(key)
    if not expected:
        raise Exception("should have been {} but was {}".format(
            expected_happenings, new_happened_counts))

    if not len(set(happened['unable_existing_nodes_diff_details_msgs'])) == 3:
        raise Exception("{} should have been {} but was {}".format(
            'unable_existing_nodes_diff_details_msgs',
            3,
            len(set(happened['unable_existing_nodes_diff_details_msgs']))))
    if not len(set(happened['unable_data_error_nodes_msgs'])) == 1:
        raise Exception("{} should have been {} but was {}".format(
            'unable_data_error_nodes_msgs',
            1,
            len(set(happened['unable_data_error_nodes_msgs']))))


if __name__ == '__main__':
    try:
        # This should be the json generated by clicking Create new Client ID
        # and selecting Service account in the google developer console.
        client_json = os.environ['GOOGLE_JSON']
        credentials = json.loads(client_json)
        client_email = credentials['client_email']
        private_key = credentials['private_key']
    except KeyError:
        print("Please supply as an environment variable:")
        print("GOOGLE_JSON")
        print("This should be the json generated by clicking "
              "Create new Client ID and selecting Service "
              "account in the google developer console.")
        sys.exit(1)
    happened = load_organisations(client_email, private_key)
    report_what_happened(happened)
