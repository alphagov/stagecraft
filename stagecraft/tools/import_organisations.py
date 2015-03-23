import cPickle as pickle
import os
import requests
import sys

from collections import defaultdict
from django.db import connection
from pprint import pprint

from stagecraft.apps.organisation.models import Node, NodeType
from stagecraft.apps.dashboards.models import Dashboard

from .spreadsheets import SpreadsheetMunger

# These may not be 100% accurate however the derived
# typeOf will be overwritten with more certain information
# based on iterating through all tx rows in build_up_node_dict.
# We use this to to get the full org graph with types even when orgs are
# not associated with a transaction in txex. This is the best guess mapping.
govuk_to_pp_type = {
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


def get_govuk_organisations():
    """
    Fetch organisations from the GOV.UK API. This is the canonical source.
    """

    try:
        with open('govuk_orgs.pickle', 'rb') as pickled:
            results = pickle.load(pickled)
    except IOError:
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

        with open('govuk_orgs.pickle', 'wb') as pickled:
            pickle.dump(results, pickled, pickle.HIGHEST_PROTOCOL)

    return results


def load_data(username, password):
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
    records = spreadsheets.load(username, password)
    govuk_response = get_govuk_organisations()
    return records, govuk_response


def make_node(id, title, slug, abbr, type):
    if abbr is not None:
        abbr = abbr.encode('utf-8').strip()
        if abbr == '':
            abbr = None

    return (
        id,
        title.encode('utf-8').strip(),
        slug,
        abbr,
        type,
    )


def govuk_graph(entries):
    nodes = set()
    edges = set()

    for entry in entries:
        node_slug = entry['details']['slug']
        node_id = 'govuk-{}'.format(node_slug).lower()
        nodes.add(make_node(
            node_id,
            entry['title'],
            node_slug,
            entry['details']['abbreviation'],
            govuk_to_pp_type[entry['format']],
        ))

        for child in entry['child_organisations']:
            child_id = 'govuk-{}'.format(child['id'].split('/')[-1]).lower()
            edges.add((
                node_id,
                child_id,
            ))

    return nodes, edges


def index_nodes(nodes, field_index):
    indexed = {}

    for node in nodes:
        value = node[field_index]

        if value in indexed:
            print 'Overwriting node in index. [node[{}]: {}]'\
                .format(field_index, value)

        if value is not None and value != '':
            indexed[value.lower()] = node

    return indexed


def govuk_node_for_record(record, by_title, by_abbr):
    parent_org = record[
        'agency'] if 'agency' in record else record['department']
    abbr = parent_org['abbr'].lower()
    title = parent_org['name'].lower()

    node = by_abbr.get(abbr, by_title.get(title, None))
    if node is None and abbr == 'inss':
        node = by_title['the insolvency service']

    return node


def transactions_graph(records, by_title, by_abbr):
    nodes = set()
    edges = set()
    node_to_transactions = defaultdict(list)

    for record in records:
        parent_node = govuk_node_for_record(record, by_title, by_abbr)

        if 'service' not in record:
            print "'{}' doesn't have a service attached".format(record['name'])
        else:
            service = record['service']
            service_slug = service['slug']
            service_id = 'service-{}'.format(service_slug).lower()

            nodes.add(make_node(
                service_id,
                service['name'],
                service_slug,
                None,
                'service',
            ))
            edges.add((parent_node[0], service_id))

            if 'transaction' in record:
                transaction = record['transaction']
                transaction_id = 'transaction-{}-{}'.format(
                    service_slug, transaction['slug']).lower()

                nodes.add(make_node(
                    transaction_id,
                    transaction['name'],
                    transaction['slug'],
                    None,
                    'transaction',
                ))
                edges.add((service_id, transaction_id))
                node_to_transactions[transaction_id].append(record['tx_id'])
            else:
                node_to_transactions[service_id].append(record['tx_id'])

    return nodes, edges, node_to_transactions


def load_organisations(username, password):
    records, govuk_response = load_data(username, password)

    govuk_nodes, govuk_edges = govuk_graph(govuk_response)
    by_title = index_nodes(govuk_nodes, 1)
    by_abbr = index_nodes(govuk_nodes, 3)

    tx_nodes, tx_edges, node_to_transactions = transactions_graph(
        records, by_title, by_abbr)

    nodes = govuk_nodes | tx_nodes
    edges = govuk_edges | tx_edges

    print 'Duplicated nodes'
    print govuk_nodes & tx_nodes

    print 'Duplicated edges'
    print govuk_edges & tx_edges

    print 'Nodes with multiple tx dashboards'
    pprint([(node_id, transactions) for node_id,
            transactions in node_to_transactions.items()
            if len(transactions) > 1], width=1)

    return nodes, edges, node_to_transactions


def clear_organisation_relations():
    past_relations = {}
    for dashboard in Dashboard.objects.all():
        if dashboard.organisation is not None:
            past_relations[dashboard.id] = {
                'id': dashboard.organisation.id,
                'name': dashboard.organisation.name,
                'slug': dashboard.organisation.slug,
                'abbr': dashboard.organisation.abbreviation,
            }

        dashboard.organisation = None
        dashboard.transaction_cache = None
        dashboard.service_cache = None
        dashboard.agency_cache = None
        dashboard.department_cache = None
        dashboard.save()

    Node.objects.all().delete()

    return past_relations


def node_types():
    return {
        'department': NodeType.objects.get_or_create(name='department')[0],
        'agency': NodeType.objects.get_or_create(name='agency')[0],
        'service': NodeType.objects.get_or_create(name='service')[0],
        'transaction': NodeType.objects.get_or_create(name='transaction')[0],
    }


def create_edge(parent_id, child_id):
    cursor = connection.cursor()
    cursor.execute(
        'INSERT INTO organisation_node_parents(from_node_id, to_node_id) VALUES(%s,%s);',  # noqa
        [child_id, parent_id]
    )


def create_nodes(nodes, edges, type_to_NodeType):
    nodes_to_db = {}
    for node in nodes:
        slug = node[2]
        if len(slug) > 150:
            print 'slug too long "{}"'.format(slug)
            slug = slug[:150]
        db_node = Node(
            name=node[1].decode(
                'utf-8').encode('latin1', 'ignore').decode('latin1'),
            slug=slug.decode(
                'utf-8').encode('latin1', 'ignore').decode('latin1'),
            abbreviation=node[3],
            typeOf=type_to_NodeType[node[4]],
        )
        db_node.save()
        nodes_to_db[node[0]] = db_node

    for edge in edges:
        parent_node = nodes_to_db.get(edge[0], None)
        child_node = nodes_to_db.get(edge[1], None)

        if parent_node and child_node:
            if parent_node.id == child_node.id:
                print "Skipping self-referencing edge: {}"\
                    .format(parent_node.slug)
            else:
                create_edge(parent_node.id, child_node.id)

    return nodes_to_db


def link_transactions(nodes_to_transactions, nodes_to_db):
    dashboards_linked = set()

    for node, transactions in nodes_to_transactions.items():
        db_node = nodes_to_db[node]
        for transaction in transactions:
            # duplicate the trimming that is done during import
            if len(transaction) > 90:
                transaction = transaction[:90]
            try:
                dashboard = Dashboard.objects.get(slug=transaction)
                dashboard.organisation = db_node
                dashboard.save()
                dashboards_linked.add(dashboard.id)
            except Dashboard.DoesNotExist:
                dashboards = list(Dashboard.objects.by_tx_id(transaction))
                if len(dashboards) == 0:
                    print 'Ahh no dashboards for {}'.format(transaction)
                else:
                    for dashboard in dashboards:
                        dashboard.organisation = db_node
                        dashboard.save()
                        dashboards_linked.add(dashboard.id)

    return dashboards_linked


def link_remaining(past_relations, dashboards_linked, nodes_to_db, by_abbr):
    for id, node in past_relations.items():
        try:
            dashboard = Dashboard.objects.get(id=id)
        except Dashboard.DoesNotExist:
            print 'Lost a dashboard: {}'.format(id)
        if id not in dashboards_linked:
            if 'abbr' not in node or node['abbr'] is None:
                print 'could not find an org for {}'.format(dashboard.slug)
                print node
            else:
                new_node = by_abbr.get(node['abbr'].lower(), None)
                if new_node:
                    db_node = nodes_to_db[new_node[0]]
                    dashboard.organisation = db_node
                    dashboard.save()
                else:
                    print 'could not find an org for {}'.format(dashboard.slug)
                    print node


if __name__ == '__main__':
    try:
        username = os.environ['GOOGLE_USERNAME']
        password = os.environ['GOOGLE_PASSWORD']
    except KeyError:
        print("Please supply as environment variables:")
        print("GOOGLE_USERNAME")
        print("GOOGLE_PASSWORD")
        sys.exit(1)

    print 'Loading organisations'
    nodes, edges, nodes_to_transactions = load_organisations(
        username, password)
    print 'Clearing organisations'
    past_relations = clear_organisation_relations()
    print 'Creating nodes'
    nodes_to_db = create_nodes(nodes, edges, node_types())
    print 'Linking transactions'
    dashboards_linked = link_transactions(nodes_to_transactions, nodes_to_db)
    print 'Linking outstanding dashboards'
    link_remaining(
        past_relations, dashboards_linked, nodes_to_db, index_nodes(nodes, 3))
