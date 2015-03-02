import django
import cPickle as pickle
import os
import requests
import sys
from stagecraft.apps.organisation.models import Node, NodeType
from stagecraft.apps.dashboards.models import Dashboard

from collections import defaultdict
# from spreadsheets import SpreadsheetMunger


class WhatHappened:
    happenings = {
        'dashboards_at_start': [],
        'dashboards_at_end': [],
        'total_nodes_before': [],
        'total_nodes_after': [],
        'organisations': [],
        'transactions': [],
        'created_nodes': [],
        'existing_nodes': [],
        'unable_to_find_or_create_nodes': [],
        'unable_existing_nodes_diff_details': [],
        'unable_existing_nodes_diff_details_msgs': [],
        'unable_data_error_nodes': [],
        'unable_data_error_nodes_msgs': [],
        'duplicate_services': [],
        'duplicate_transactions': [],
        'duplicate_dep_or_agency_abbreviations': [],
        'link_to_parents_not_found': [],
        'link_to_parents_found': [],
        'transactions_associated_with_dashboards': [],
        'transactions_not_associated_with_dashboards': []
    }

    def this_happened(self, key, value):
        self.happenings[key] = value

WHAT_HAPPENED = WhatHappened()


def remove_all_dashboard_references_to_orgs():
    for dashboard in Dashboard.objects.all():
        dashboard.organisation = None
        dashboard.save()
    Node.objects.all().delete()


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

    nodes_hash = build_up_node_hash(transactions_data, govuk_organisations)
    # as this is recursive internally
    # we could filter to start with the transactions only
    # and then return these created and keyed off the name at the end
    # however I don't fully understand the graph yet and there may be
    # orphans building up in this way.
    # instead ensure we create everything and then load transactions that
    # have been created and associate based on the standard way of building
    # up a transaction name
    create_nodes(nodes_hash)

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


def load_data(username, password):
    # spreadsheets = SpreadsheetMunger({
        # 'names_name': 8,
        # 'names_slug': 9,
        # 'names_service_name': 6,
        # 'names_service_slug': 7,
        # 'names_tx_id_column': 18,
    # })
    # transactions_data = spreadsheets.load(username, password)

    # with open('transactions_data.pickle', 'w') as data_file:
    # pickle.dump(transactions_data, data_file)

    with open('transactions_data.pickle', 'r') as data_file:
        transactions_data = pickle.load(data_file)

    # govuk_organisations = get_govuk_organisations()

    # with open('govuk_organisations.pickle', 'w') as org_file:
        # pickle.dump(govuk_organisations, org_file)

    with open('govuk_organisations.pickle', 'r') as org_file:
        govuk_organisations = pickle.load(org_file)

    # import json
    # with open('thing.json', 'w') as f:
    # f.write(json.dumps([org for org in govuk_organisations if org['web_url'] == 'https://www.gov.uk/government/organisations/crown-prosecution-service']))  # noqa
    # with open('thing2.json', 'w') as f:
    # f.write(json.dumps([org for org in govuk_organisations if org['web_url'] == 'https://www.gov.uk/government/organisations/attorney-generals-office']))  # noqa
    # with open('thing3.json', 'w') as f:
    # f.write(json.dumps(list(set([org['format'] for org in govuk_organisations]))))  # noqa
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

###


def build_up_node_hash(transactions, organisations):
    org_hash = build_up_org_hash(organisations)
    more_than_one_tx = []
    more_than_one_service = []
    """
    go through each transaction and build hash with names as keys
    """
    for tx in transactions:
        if transaction_name(tx) in org_hash:
            more_than_one_tx.append(transaction_name(tx))
            # raise Exception('More than one transaction with name {}'.format(
            # transaction_name(tx)))
        if service_name(tx) in org_hash:
            more_than_one_service.append(service_name(tx))
            # raise Exception('More than one service with name {}'.format(
            # service_name(tx)))

        org_hash[transaction_name(tx)] = {
            'name': transaction_name(tx),
            'abbreviation': None,
            'typeOf': 'transaction',
            'parents': [service_name(tx)]
        }
        org_hash[service_name(tx)] = {
            'name': service_name(tx),
            'abbreviation': None,
            'typeOf': 'service',
            'parents': []
        }
    WHAT_HAPPENED.this_happened('duplicate_services', more_than_one_service)
    WHAT_HAPPENED.this_happened('duplicate_transactions', more_than_one_tx)
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
                tx, org_hash, 'agency')
        # if there is a department and no agency
        elif tx['department']:
            # if there is a thing for abbreviation then add it's abbreviation to parents  # noqa
            success, link = associate_parents(
                tx, org_hash, 'department')
        else:
            raise Exception("transaction with no department or agency!")
        if success:
            successfully_linked.append(link)
        else:
            failed_to_link.append(link)
    WHAT_HAPPENED.this_happened('link_to_parents_found', successfully_linked)
    WHAT_HAPPENED.this_happened('link_to_parents_not_found', failed_to_link)
    return org_hash


def build_up_org_hash(organisations):
    org_id_hash = {}
    # note, typeOf will be overwritten with more certain information
    # based on iterating through all tx rows in build_up_node_hash.
    # We do this here though to to get the full org graph even when orgs are
    # not associated with a transaction in txex
    for org in organisations:
        org_id_hash[org['id']] = {
            'name': org['title'],
            'abbreviation': org['details']['abbreviation'],
            'typeOf': types_hash[org['format']],
            'parents': []
        }

    # assign parents
    for org in organisations:
        for parent in org['parent_organisations']:
            abbr = org_id_hash[parent['id']]['abbreviation']
            if abbr:
                parent_abbreviation = abbr
            elif org_id_hash[parent['id']]['name']:
                parent_abbreviation = org_id_hash[parent['id']]['name']

            org_id_hash[org['id']]['parents'].append(
                slugify(parent_abbreviation))

    # now the structure of the gov.uk org graph is replicated,
    # create a new hash keyed off the abbreviation for use in linking
    # to the tx data.
    org_hash = {}
    abbrs_twice = defaultdict(list)
    for org_id, org in org_id_hash.items():
        if slugify(org['abbreviation']) in org_hash:
            # this could be the place for case statements to
            # decide on a better names but for now just record any problems
            if not abbrs_twice[slugify(org['abbreviation'])]:
                abbrs_twice[slugify(org['abbreviation'])].append(
                    org_hash[slugify(org['abbreviation'])])
            abbrs_twice[slugify(org['abbreviation'])].append(
                org)
            print 'Using name as key for second with abbr:'
            print org
            org_hash[slugify(org['name'])] = org
        else:
            # if there is an abbreviation use it
            # otherwise use the name
            if slugify(org['abbreviation']):
                org_hash[slugify(org['abbreviation'])] = org
            else:
                org_hash[slugify(org['name'])] = org

    WHAT_HAPPENED.this_happened(
        'duplicate_dep_or_agency_abbreviations',
        [(abbr, tx) for abbr, tx in abbrs_twice.items()])
    return org_hash


def associate_parents(tx, org_hash, typeOf):
    # if there is a thing for abbreviation then add it's abbreviation to parents  # noqa
    if slugify(tx[typeOf]['abbr']) in org_hash:
        parent = org_hash[slugify(tx[typeOf]['abbr'])]
        parent = add_type_to_parent(parent, typeOf)
        # prevent null or blank string parents
        if slugify(parent['abbreviation']):
            org_hash[service_name(tx)]['parents'].append(
                slugify(parent['abbreviation']))
            return (True, (tx[typeOf], parent))
        else:
            # the parent has no name or abbrevation
            # how did it get his way?
            return (False, ('blank or null abbr', tx[typeOf], parent))
    # try the name if no luck with the abbreviation
    elif slugify(tx[typeOf]['name']) in org_hash:
        parent = org_hash[slugify(tx[typeOf]['name'])]
        parent = add_type_to_parent(parent, typeOf)
        # prevent null or blank string parents
        if slugify(parent['name']):
            org_hash[service_name(tx)]['parents'].append(
                slugify(parent['name']))
            return (True, (tx[typeOf], parent))
        else:
            # the parent has no name or abbrevation
            # how did it get his way?
            return (False, ('blank or null name', tx[typeOf], parent))
    # if there is nothing for name
    # or abbreviation then add to not found
    else:
        return (False, (tx[typeOf], None))

###


def create_nodes(nodes_hash):
    failed_to_create = []
    created = []
    existing = []
    errors = defaultdict(list)

    def _get_or_create_node(node_hash, nodes_hash):
        node_type, _ = NodeType.objects.get_or_create(name=node_hash['typeOf'])
        try:
            defaults = {
                'typeOf': node_type
            }
            if slugify(node_hash['abbreviation']):
                defaults['abbreviation'] = slugify(node_hash['abbreviation'])
            node, _ = Node.objects.get_or_create(
                name=node_hash['name'],
                defaults=defaults
            )

            found_or_created = {
                'name': node_hash['name'],
                'abbreviation': slugify(node_hash['abbreviation']),
                'typeOf': node_type
            }
            if _:
                created.append(found_or_created)
            elif(found_or_created not in created
                 and found_or_created not in existing):
                existing.append({
                    'name': node_hash['name'],
                    'abbreviation': slugify(node_hash['abbreviation']),
                    'typeOf': node_type
                })
        # integrity error are existing with slightly different stuff.
        # data errors are too long field
        except(django.db.utils.DataError, django.db.utils.IntegrityError) as e:

            errors[e.__class__].append(e)
            failed_to_create.append({
                'name': node_hash['name'],
                'abbreviation': slugify(node_hash['abbreviation']),
                'typeOf': node_type
            })
            return False
        return node

    created_nodes = []
    abbr_or_name_to_uuid = {}
    total_parents = []
    total_parents_found = []
    for key_or_abbr, node_hash in nodes_hash.items():
        node = _get_or_create_node(node_hash, nodes_hash)
        if node:
            if node.abbreviation:
                abbr_or_name_to_uuid[node.abbreviation] = node.id
            if node.name:
                abbr_or_name_to_uuid[node.name] = node.id
            created_nodes.append((node, node_hash['parents']))
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
    WHAT_HAPPENED.this_happened('created_nodes', created)
    WHAT_HAPPENED.this_happened('existing_nodes', existing)
    WHAT_HAPPENED.this_happened(
        'unable_to_find_or_create_nodes', failed_to_create)
    for error_type, error_instances in errors.items():
        if error_type == django.db.utils.IntegrityError:
            WHAT_HAPPENED.this_happened(
                'unable_existing_nodes_diff_details', error_instances)
            msgs = set([error.message for error in error_instances])
            WHAT_HAPPENED.this_happened(
                'unable_existing_nodes_diff_details_msgs', msgs)
        elif error_type == django.db.utils.DataError:
            WHAT_HAPPENED.this_happened(
                'unable_data_error_nodes', error_instances)
            msgs = set([error.message for error in error_instances])
            WHAT_HAPPENED.this_happened(
                'unable_data_error_nodes_msgs', msgs)


def associate_with_dashboard(transaction_hash):
    transaction = Node.objects.filter(
        name=transaction_name(transaction_hash)).first()
    dashboards = []
    if transaction:
        # switch to get if not published
        dashboards = Dashboard.objects.by_tx_id(transaction_hash['tx_id'])
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


def transaction_name(tx):
    return tx['name'].encode('utf-8')


def add_type_to_parent(parent, typeOf):
    parent['typeOf'] = typeOf
    return parent


# These may not be 100% accurate however the derived
# typeOf will be overwritten with more certain information
# based on iterating through all tx rows in build_up_node_hash.
# We use this to to get the full org graph with types even when orgs are
# not associated with a transaction in txex. This is the best guess mapping.
types_hash = {
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
        'dashboards_at_start': 872,
        'dashboards_at_end': 872,
        'total_nodes_before': 0,
        'total_nodes_after':  1467,
        'organisations': 894,
        'transactions': 785,
        'created_nodes': 1467,
        'existing_nodes': 7,
        'unable_to_find_or_create_nodes': 96,
        'unable_existing_nodes_diff_details': 3,
        'unable_existing_nodes_diff_details_msgs': 3,
        'unable_data_error_nodes': 93,
        'unable_data_error_nodes_msgs': 5,
        'duplicate_services': 347,
        'duplicate_transactions': 547,
        'duplicate_dep_or_agency_abbreviations': 3,
        'link_to_parents_not_found': 175,
        'link_to_parents_found': 610,
        'transactions_associated_with_dashboards': 93,
        'transactions_not_associated_with_dashboards': 692,
        'total_parents_found': 1110,
        'total_parents': 1245
    }
    for key, things in happened.items():
        print key
        print len(things)
        print '^'

    for key, things in happened.items():
        if not expected_happenings[key] == len(things):
            raise Exception("{} should have been {} but was {}".format(
                key, expected_happenings[key], len(things)))


if __name__ == '__main__':
    main()
