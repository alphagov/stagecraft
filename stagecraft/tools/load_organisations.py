import cPickle as pickle
import os
import requests
import sys
from stagecraft.apps.organisation.models import Node, NodeType

from collections import defaultdict
from spreadsheets import SpreadsheetMunger


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


def add_to_slugs(slugs, things):
    for thing in things:
        slug = thing[0]
        if slug in slugs:
            print '{} exists. offender: {} original: {}'.format(
                slug, thing, slugs[slug])
        else:
            slugs[slug] = thing


def load_data(username, password):
    spreadsheets = SpreadsheetMunger({
        'names_name': 8,
        'names_slug': 9,
        'names_service_name': 6,
        'names_service_slug': 7,
        'names_tx_id_column': 18,
    })
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

    import json
    # with open('thing.json', 'w') as f:
    # f.write(json.dumps([org for org in govuk_organisations if org['web_url'] == 'https://www.gov.uk/government/organisations/crown-prosecution-service']))  # noqa
    # with open('thing2.json', 'w') as f:
    # f.write(json.dumps([org for org in govuk_organisations if org['web_url'] == 'https://www.gov.uk/government/organisations/attorney-generals-office']))  # noqa
    # with open('thing3.json', 'w') as f:
    # f.write(json.dumps(list(set([org['format'] for org in govuk_organisations]))))  # noqa
    return transactions_data, govuk_organisations


def load_organisations(username, password):
    transactions_data, govuk_organisations = load_data(username, password)

    print transactions_data
    print govuk_organisations
    nodes_hash = build_up_node_hash(transactions_data, govuk_organisations)
    create_nodes(nodes_hash)
    # transactions = create_transactions()
    # for transaction in transactions:
    # associate_with_dashboard(transaction, stuff)
    # associate_with_parents_recursively(transaction, stuff)

# a type for all of these or map them? or is there a
# field other than format we should use?
types_hash = {
    "Advisory non-departmental public body": 'department',
    "Tribunal non-departmental public body": 'department',
    "Sub-organisation": 'department',
    "Executive agency": 'department',
    "Devolved administration": 'department',
    "Ministerial department": 'department',
    "Non-ministerial department": 'agency',
    "Executive office": 'department',
    "Civil Service": 'department',
    "Other": 'department',
    "Executive non-departmental public body": 'department',
    "Independent monitoring body": 'department',
    "Public corporation": 'department'
}


def create_nodes(nodes_hash):
    def _get_or_create_node(node_hash, nodes_hash):
        node_type, _ = NodeType.objects.get_or_create(name=node_hash['typeOf'])
        node, _ = Node.objects.get_or_create(
            name=node_hash['name'],
            abbreviation=slugify(node_hash['abbreviation']),
            typeOf=node_type
        )
        for parent in node_hash['parents']:
            node.parents.add(
                _get_or_create_node(
                    nodes_hash[parent],
                    nodes_hash))
        return node
    for key_or_abbr, node_hash in nodes_hash.items():
        _get_or_create_node(node_hash, nodes_hash)


def build_up_org_hash(organisations):
    org_id_hash = {}
    for org in organisations:
        org_id_hash[org['id']] = {
            'name': org['title'],
            'abbreviation': org['details']['abbreviation'],
            'typeOf': types_hash[org['format']],
            'parents': []
        }

    for org in organisations:
        for parent in org['parent_organisations']:
            org_id_hash[org['id']]['parents'].append(
                slugify(org_id_hash[parent['id']]['abbreviation']))

    org_hash = {}
    for org_id, org in org_id_hash.items():
        org_hash[slugify(org['abbreviation'])] = org
    return org_hash


def slugify(string):
    if string:
        return string.lower()
    else:
        return string


def build_up_node_hash(transactions, organisations):
    def service_name(tx):
        return "{}".format(tx['service']['name'])

    def transaction_name(tx):
        return "{}: {}".format(tx['service']['name'], tx['slug'])

    no_agency_found = []
    no_dep_found = []
    org_hash = build_up_org_hash(organisations)
    """
    go through each transaction and build hash with names as keys
    """
    for tx in transactions:
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
    """
    go through again
    """
    for tx in transactions:
        """
        ***THIS IS ASSUMING AGENCIES ARE ALWAYS JUNIOR TO DEPARTMENTS****
        """
        # if there is an agency then get the thing by abbreviation
        if tx["agency"]:
            # if there is a thing for abbreviation then add it's abbreviation to parents  # noqa
            if slugify(tx['agency']['abbr']) in org_hash:
                agency_parent = org_hash[slugify(tx['agency']['abbr'])]
                org_hash[service_name(tx)]['parents'].append(
                    slugify(agency_parent['abbreviation']))
            # if there is no thing for abbreviation then add to not found
            else:
                no_agency_found.append(tx)
        # if there is a department and no agency
        elif tx['department']:
            # if there is a thing for abbreviation then add it's abbreviation to parents  # noqa
            if slugify(tx['department']['abbr']) in org_hash:
                department_parent = org_hash[slugify(tx['department']['abbr'])]
                org_hash[service_name(tx)]['parents'].append(
                    slugify(department_parent['abbreviation']))
            # if there is no thing for abbreviation then add to not found
            else:
                no_dep_found.append(tx)
        else:
            raise "transaction with no deparment or agency!"
    return org_hash


def main():
    try:
        username = os.environ['GOOGLE_USERNAME']
        password = os.environ['GOOGLE_PASSWORD']
    except KeyError:
        print "Please supply as environment variables:"
        print "username (GOOGLE_USERNAME)"
        print "password (GOOGLE_PASSWORD)"
        sys.exit(1)

    load_organisations(username, password)

    sys.exit(0)

    # remove any orgs from the list from GOV.UK where they have shut down
    govuk_organisations = \
        [org for org in govuk_organisations if org[
            'details']['closed_at'] is None]

    abbrs = defaultdict(list)
    types = defaultdict(list)

    for org in govuk_organisations:
        types[org['format']].append(org)
        abbr = org['details']['abbreviation']
        if abbr:
            abbrs[abbr.lower()].append(org)
        # else:
            # print '{} doesnt have an
            # abbr'.format(unicode(org['title']).encode('ascii','ignore'))

    # abbrs = dict(abbrs)
    # abbrs_twice = \
        # {abbr: abbrs[abbr] for abbr, orgs in abbrs.items() if len(orgs) > 1}

    list_abbrs = abbrs.keys()
    list_abbrs.sort()

    print list_abbrs

    # pprint.pprint(dict(abbrs_twice), width=-1)
    # pprint.pprint(dict(types), width=-1)

    not_found_depts = set()
    not_found_agencies = set()

    for transaction in transactions_data:
        dept_abbr = transaction['department']['abbr']
        if transaction['agency'] is not None:
            agency_abbr = transaction['agency']['abbr']
        else:
            agency_abbr = None

        dept = abbrs.get(dept_abbr.lower(), None)
        if dept is None:
            not_found_depts.add(dept_abbr)
        elif len(dept) > 1:
            print 'More than one department for abbreviation {}'.format(
                dept_abbr)

        if agency_abbr:
            if agency_abbr == 'INSS':
                agency = abbrs['the insolvency service']
            else:
                agency = abbrs.get(agency_abbr.lower(), None)
                if agency is None:
                    agency_abbr = transaction['agency']['name'].lower()
                    agency = abbrs.get(
                        agency_abbr, None)
                    if agency is None:
                        not_found_agencies.add(
                            (agency_abbr, transaction['agency']['name']))
                if len(agency) > 1:
                    print 'More than one agency for abbreviation {}'.format(
                        agency_abbr)

    print not_found_depts
    print not_found_agencies

    # STUFF FOR EXAMINING SPREADSHEET STUFF

    # transactions = set()
    # services = set()
    # agencies = set()
    # departments = set()

    # for transaction in transactions_data:
    # transactions.add((transaction['slug'], transaction['name']))
    # services.add(
    # (transaction['service']['slug'], transaction['service']['name']))
    # if transaction['agency'] is not None:
    # agencies.add((transaction['agency']['slug'], transaction[
    # 'agency']['name'], transaction['agency']['abbr']))
    # departments.add((
    # transaction['department']['slug'],
    # transaction['department']['name'],
    # transaction['department']['abbr']))

    # slugs = dict()
    # add_to_slugs(slugs, transactions)
    # add_to_slugs(slugs, services)
    # add_to_slugs(slugs, agencies)
    # add_to_slugs(slugs, departments)

    # print len(transactions)
    # print len(services)
    # print len(agencies)
    # print len(departments)

    # print len(transactions) + len(services) + len(agencies) + len(
    #     departments)
    # print len(slugs)

    # print transactions
    # print services
    # print agencies
    # print departments


if __name__ == '__main__':
    main()
