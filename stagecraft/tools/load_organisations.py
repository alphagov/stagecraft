import django
# import cPickle as pickle
import os
import requests
import sys
from stagecraft.apps.organisation.models import Node, NodeType
from stagecraft.apps.dashboards.models import Dashboard

from collections import defaultdict
from spreadsheets import SpreadsheetMunger


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


def load_organisations(username, password):
    WHAT_HAPPENED.this_happened(
        'dashboards_at_start',
        [dashboard for dashboard in Dashboard.objects.all()])
    # we only care about transactions, everything else loses their org
    remove_all_dashboard_references_to_orgs()
    WHAT_HAPPENED.this_happened(
        'total_nodes_before', [node for node in Node.objects.all()])
    transactions_data, govuk_organisations = load_data(username, password)

    # remove any orgs from the list from GOV.UK where they have shut down
    govuk_organisations = \
        [org for org in govuk_organisations if org[
            'details']['closed_at'] is None]

    WHAT_HAPPENED.this_happened('organisations', govuk_organisations)
    WHAT_HAPPENED.this_happened('transactions', transactions_data)

    nodes_dict = build_up_node_dict(transactions_data, govuk_organisations)

    create_nodes(nodes_dict)

    finished = []
    bruk = []
    for transaction in transactions_data:
        if associate_with_dashboard(transaction):
            finished.append(transaction)
        else:
            bruk.append(transaction)
    WHAT_HAPPENED.this_happened(
        'transactions_associated_with_dashboards', finished)
    WHAT_HAPPENED.this_happened(
        'transactions_not_associated_with_dashboards', bruk)
    WHAT_HAPPENED.this_happened(
        'total_nodes_after',
        [node for node in Node.objects.all()])
    WHAT_HAPPENED.this_happened(
        'dashboards_at_end',
        [dashboard for dashboards in Dashboard.objects.all()])
    return WHAT_HAPPENED.happenings


def remove_all_dashboard_references_to_orgs():
    for dashboard in Dashboard.objects.all():
        dashboard.organisation = None
        dashboard.save()
    Node.objects.all().delete()


def load_data(username, password):
    spreadsheets = SpreadsheetMunger({
        'names_name': 9,
        'names_slug': 10,
        'names_service_name': 11,
        'names_service_slug': 12,
        'names_tx_id_column': 19,
    })
    transactions_data = spreadsheets.load(username, password)

    # with open('transactions_data.pickle', 'w') as data_file:
    #     pickle.dump(transactions_data, data_file)

    # with open('transactions_data.pickle', 'r') as data_file:
    #     transactions_data = pickle.load(data_file)

    govuk_organisations = get_govuk_organisations()

    # with open('govuk_organisations.pickle', 'w') as org_file:
    #     pickle.dump(govuk_organisations, org_file)

    # with open('govuk_organisations.pickle', 'r') as org_file:
    #     govuk_organisations = pickle.load(org_file)

    return transactions_data, govuk_organisations


def get_govuk_organisations():
    def get_page(page):
        response = requests.get(
            'https://www.gov.uk/api/organisations?page={}'.format(page))
        return response.json()

    first_page = get_page(1)
    results = first_page['results']

    for page_num in range(2, first_page['pages'] + 1):
        page = get_page(page_num)
        results = results + page['results']

    return results


def build_up_node_dict(transactions, organisations):
    org_dict = {}
    org_dict = add_departments_and_agencies_to_org_dict(
        org_dict, organisations)
    org_dict = add_transactions_and_services_to_org_dict(
        org_dict, transactions)
    org_dict = add_parents_to_organisations_and_correct_types(
        org_dict, transactions)

    return org_dict


def add_departments_and_agencies_to_org_dict(org_dict, organisations):
    org_id_dict = build_department_and_agency_dict_keyed_off_govuk_id(
        organisations)
    org_id_dict = assign_parents_to_departments_and_agencies(
        organisations, org_id_dict)
    org_dict = key_department_and_agency_dict_off_abbreviation_or_name(
        org_dict,
        org_id_dict)
    return org_dict


def add_transactions_and_services_to_org_dict(org_dict, transactions):
    """
    go through each transaction and build dict with names as keys
    """
    more_than_one_tx = []
    more_than_one_service = []
    for tx in transactions:
        if transaction_name(tx) in org_dict:
            more_than_one_tx.append(transaction_name(tx))
        if service_name(tx) in org_dict:
            more_than_one_service.append(service_name(tx))

        org_dict[transaction_name(tx)] = {
            'name': transaction_name(tx),
            'slug': transaction_slug(tx),
            'abbreviation': None,
            'typeOf': 'transaction',
            'parents': [service_name(tx)]
        }
        org_dict[service_name(tx)] = {
            'name': service_name(tx),
            'slug': service_slug(tx),
            'abbreviation': None,
            'typeOf': 'service',
            'parents': []
        }
    WHAT_HAPPENED.this_happened('duplicate_services', more_than_one_service)
    WHAT_HAPPENED.this_happened('duplicate_transactions', more_than_one_tx)
    return org_dict


def add_parents_to_organisations_and_correct_types(org_dict, transactions):
    """
    go through again
    """
    successfully_linked = []
    failed_to_link = []
    for tx in transactions:
        """
        ***THIS IS ASSUMING AGENCIES ARE ALWAYS JUNIOR TO DEPARTMENTS****
        """
        # if there is an agency then get the thing by abbreviation
        if tx["agency"] and (tx['agency']['abbr'] or tx['agency']['name']):
            success, link = associate_parents(
                tx, org_dict, 'agency')
        # if there is a department and no agency
        elif tx['department']:
            # if there is a thing for abbreviation then add it's abbreviation to parents  # noqa
            success, link = associate_parents(
                tx, org_dict, 'department')
        else:
            raise Exception("transaction with no department or agency!")
        if success:
            successfully_linked.append(link)
        else:
            failed_to_link.append(link)
    WHAT_HAPPENED.this_happened('link_to_parents_found', successfully_linked)
    WHAT_HAPPENED.this_happened('link_to_parents_not_found', failed_to_link)
    return org_dict


def build_department_and_agency_dict_keyed_off_govuk_id(organisations):
    org_id_dict = {}
    # note, typeOf will be overwritten with more certain information
    # based on iterating through all tx rows in build_up_node_dict.
    # We do this here though to to get the full org graph even when orgs are
    # not associated with a transaction in txex

    # name will be overwritten with the renamed value if found
    # slug will be overwritten with the renamed value if found
    for org in organisations:
        org_id_dict[org['id']] = {
            'name': org['title'],
            'slug': org['details']['slug'],
            'abbreviation': org['details']['abbreviation'],
            'typeOf': types_dict[org['format']],
            'parents': []
        }
    return org_id_dict


def assign_parents_to_departments_and_agencies(organisations, org_id_dict):
    # assign parents, all at least have name
    for org in organisations:
        for parent in org['parent_organisations']:
            abbr = org_id_dict[parent['id']]['abbreviation']
            if abbr:
                parent_abbreviation = abbr
            elif org_id_dict[parent['id']]['name']:
                parent_abbreviation = org_id_dict[parent['id']]['name']

            org_id_dict[org['id']]['parents'].append(
                slugify(parent_abbreviation))

    return org_id_dict


def key_department_and_agency_dict_off_abbreviation_or_name(
        org_dict, org_id_dict):
    # now the structure of the gov.uk org graph is replicated,
    # create a new dict keyed off the abbreviation for use in linking
    # to the tx data.
    abbrs_twice = defaultdict(list)
    for org_id, org in org_id_dict.items():
        if slugify(org['abbreviation']) in org_dict:
            # this could be the place for case statements to
            # decide on a better names but for now just record any problems
            if not abbrs_twice[slugify(org['abbreviation'])]:
                abbrs_twice[slugify(org['abbreviation'])].append(
                    org_dict[slugify(org['abbreviation'])])
            abbrs_twice[slugify(org['abbreviation'])].append(
                org)
            print 'Using name as key for second with abbr:'
            print org
            org_dict[slugify(org['name'])] = org
        else:
            # if there is an abbreviation use it
            # otherwise use the name
            if slugify(org['abbreviation']):
                org_dict[slugify(org['abbreviation'])] = org
            else:
                org_dict[slugify(org['name'])] = org

    WHAT_HAPPENED.this_happened(
        'duplicate_dep_or_agency_abbreviations',
        [(abbr, tx) for abbr, tx in abbrs_twice.items()])
    return org_dict


def associate_parents(tx, org_dict, typeOf):
    def matching_org(org_dict, key):
        if key in org_dict:
            return org_dict[key]

    def has_attr_for_type(tx, typeOf, attr_key):
        return tx[typeOf][attr_key]

    def has_name_for_type(tx, typeOf):
        return has_attr_for_type(tx, typeOf, 'name')

    def has_abbreviation_for_type(tx, typeOf):
        return has_attr_for_type(tx, typeOf, 'abbr')
    parent_by_name = matching_org(org_dict, slugify(tx[typeOf]['name']))
    parent_by_abbreviation = matching_org(
        org_dict, slugify(tx[typeOf]['abbr']))
    if has_abbreviation_for_type(tx, typeOf) and parent_by_abbreviation:
        parent = parent_by_abbreviation
        parent = add_type_to_parent(parent, typeOf)
        parent['name'] = tx[typeOf]['name']
        parent['slug'] = tx[typeOf]['slug']
        parent_identifier = slugify(parent['abbreviation'])
    elif has_name_for_type(tx, typeOf) and parent_by_name:
        parent = parent_by_name
        parent = add_type_to_parent(parent, typeOf)
        parent['name'] = tx[typeOf]['name']
        parent['slug'] = tx[typeOf]['slug']
        parent_identifier = slugify(parent['name'])
    else:
        return (False, (tx[typeOf], None))

    org_dict[service_name(tx)]['parents'].append(
        parent_identifier)
    return (True, (tx[typeOf], parent))


def create_nodes(nodes_dict):
    created_nodes = []
    abbr_or_name_to_uuid = {}
    total_parents = []
    total_parents_found = []
    for key_or_abbr, node_dict in nodes_dict.items():
        node = get_or_create_node(node_dict)
        if node:
            if node.abbreviation:
                abbr_or_name_to_uuid[node.abbreviation] = node.id
            if node.name:
                abbr_or_name_to_uuid[node.name] = node.id
            created_nodes.append((node, node_dict['parents']))
    for node, parents in created_nodes:
        parent_uuids = []
        for parent in parents:
            if parent in abbr_or_name_to_uuid:
                parent_uuids.append(abbr_or_name_to_uuid[parent])
        total_parents += parents
        total_parents_found += parent_uuids
        if parent_uuids:
            node.parents.add(*parent_uuids)

    WHAT_HAPPENED.this_happened('total_parents_found', total_parents_found)
    WHAT_HAPPENED.this_happened('total_parents', total_parents)


def get_or_create_node(node_dict):
    node_type, _ = NodeType.objects.get_or_create(name=node_dict['typeOf'])
    try:
        defaults = {
            'typeOf': node_type
        }
        if slugify(node_dict['abbreviation']):
            defaults['abbreviation'] = slugify(node_dict['abbreviation'])
        node, created = Node.objects.get_or_create(
            name=node_dict['name'],
            defaults=defaults
        )

        if created:
            WHAT_HAPPENED.add_to_what_happened(
                'created_nodes', [node_dict])
        elif(node_dict not in WHAT_HAPPENED.get('created_nodes')
             and node_dict not in WHAT_HAPPENED.get('existing_nodes')):
            WHAT_HAPPENED.add_to_what_happened(
                'existing_nodes', [node_dict])
    # integrity error are existing with slightly different stuff.
    # data errors are too long field
    except(django.db.utils.DataError, django.db.utils.IntegrityError) as e:
        if e.__class__ == django.db.utils.IntegrityError:
            WHAT_HAPPENED.add_to_what_happened(
                'unable_existing_nodes_diff_details', [e])
            WHAT_HAPPENED.add_to_what_happened(
                'unable_existing_nodes_diff_details_msgs', [e.message])
        elif e.__class__ == django.db.utils.DataError:
            WHAT_HAPPENED.add_to_what_happened(
                'unable_data_error_nodes', [e])
            WHAT_HAPPENED.add_to_what_happened(
                'unable_data_error_nodes_msgs', [e.message])
        WHAT_HAPPENED.add_to_what_happened(
            'unable_to_find_or_create_nodes', [node_dict])
        return False
    return node


def associate_with_dashboard(transaction_dict):
    transaction = Node.objects.filter(
        name=transaction_name(transaction_dict)).first()
    dashboards = []
    if transaction:
        # switch to get if not published
        dashboards = Dashboard.objects.by_tx_id(transaction_dict['tx_id'])
        for dashboard in dashboards:
            # do this even if there is an existing dashboard
            existing_org = dashboard.organisation
            dashboard.organisation = transaction
            dashboard.save()
            # but say if the ancestors do not contain the old one.
            if(existing_org and existing_org not in
               [org for org in dashboard.organisation.get_ancestors()]):
                print("existing org {} for dashboard {}"
                      "not in new ancestors {}".format(
                          existing_org.name,
                          dashboard.title,
                          [org.name for org
                           in dashboard.organisation.get_ancestors()]))
    return [dashboard for dashboard in dashboards]


def slugify(string):
    if string:
        return string.lower()
    else:
        return string


def service_name(tx):
    return tx['service']['name'].encode('utf-8')


def service_slug(tx):
    return tx['service']['slug']


def transaction_name(tx):
    return tx['name'].encode('utf-8')


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


def main():
    try:
        username = os.environ['GOOGLE_USERNAME']
        password = os.environ['GOOGLE_PASSWORD']
    except KeyError:
        print "Please supply as environment variables:"
        print "username (GOOGLE_USERNAME)"
        print "password (GOOGLE_PASSWORD)"
        sys.exit(1)

    happened = load_organisations(username, password)
    expected_happenings = {
        'link_to_parents_not_found': 90,
        'duplicate_services': 32,
        'unable_data_error_nodes': 3,
        'total_parents': 1406,
        'total_nodes_after': 1876,
        'transactions': 790,
        'duplicate_dep_or_agency_abbreviations': 3,
        'transactions_not_associated_with_dashboards': 697,
        'organisations': 893,
        'total_nodes_before': 0,
        'link_to_parents_found': 700,
        'transactions_associated_with_dashboards': 93,
        'duplicate_transactions': 551,
        'dashboards_at_start': 874,
        'existing_nodes': 7,
        'unable_to_find_or_create_nodes': 6,
        'total_parents_found': 1373,
        'created_nodes': 1876,
        'dashboards_at_end': 874,
        'unable_existing_nodes_diff_details': 3}
    for key, things in happened.items():
        print key
        print len(things)
        print '^'
    print 'unable_existing_nodes_diff_details_msgs'
    print len(set(happened['unable_existing_nodes_diff_details_msgs']))
    print '^'
    print 'unable_data_error_nodes_msgs'
    print len(set(happened['unable_data_error_nodes_msgs']))
    print '^'

    new_happened_counts = {}
    expected = True
    for key, things in happened.items():
        if key in expected_happenings:
            new_happened_counts[key] = len(things)
            print "tracking"
            print key
            print "^"
            if not expected_happenings[key] == len(things):
                expected = False
                # raise Exception("{} should have been {} but was {}".format(
                #     key, expected_happenings[key], len(things)))
        else:
            print "something happened we aren't tracking:"
            print key
            print "^"
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
    main()
