from hamcrest import (
    assert_that, is_not, is_, equal_to
)
from mock import patch
import json
from stagecraft.apps.organisation.models import Node, NodeType

from stagecraft.apps.dashboards.tests.factories.factories import(
    ModuleFactory)
from stagecraft.apps.datasets.tests.factories import DataSetFactory

from ..load_organisations import(
    load_organisations,
    build_up_org_hash,
    build_up_node_hash,
    create_nodes)


with open('stagecraft/tools/fixtures/result.json', 'r') as f:
    tx_fixture = json.loads(f.read())

with open('stagecraft/tools/fixtures/organisations.json', 'r') as f:
    govuk_fixture = json.loads(f.read())


@patch('stagecraft.tools.load_organisations.load_data')
def test_load_organisations(mock_load_data):
    mock_load_data.return_value = tx_fixture, govuk_fixture

    tx_data_set = DataSetFactory(
        name='transactional_services_summaries',
    )
    kpi_module = ModuleFactory(
        data_set=tx_data_set,
        query_parameters={
            'filter_by': ['service_id:daa-reports-filing'],
        }
    )
    dashboard = kpi_module.dashboard

    load_organisations('foo', 'bar')

    assert_that(dashboard.organisation, is_not(None))

    org_parents = dashboard.organisation.get_ancestors(include_self=True)

    assert_that(len(org_parents), is_(4))
    assert_that(org_parents[0].name, is_('Report filing'))
    assert_that(org_parents[0].typeOf.name, is_('transaction'))
    assert_that(org_parents[1].name, is_('Filing cabinet service'))
    assert_that(org_parents[1].typeOf.name, is_('service'))
    assert_that(org_parents[2].name, is_('Paper love agency'))
    assert_that(org_parents[2].typeOf.name, is_('agency'))
    assert_that(org_parents[3].name, is_(
        'Department of Administrative Affairs'))
    assert_that(org_parents[3].typeOf.name, is_('department'))

# this is the intermediate data format built up from external data
# it is then used to actually create and update things in the database.
expected_result = {
    'Training and resources on workplace relations: registrations': {
        'name': "Training and resources on"
                " workplace relations: registrations",
        'abbreviation': None,
        'typeOf': 'transaction',
        'parents': ['Training and resources on workplace relations']
    },
    'Training and resources on workplace relations': {
        'name': 'Training and resources on workplace relations',
        'abbreviation': None,
        'typeOf': 'service',
        'parents': [u'cps']
    },
    u'cps': {
        'name': u'Crown Prosecution Service',
        'abbreviation': u'CPS',
        'typeOf': 'agency',
        'parents': [u'ago']
    },
    u'ago': {
        'name': "Attorney General's Office",
        'abbreviation': u'AGO',
        'typeOf': 'department',
        'parents': []
    }
}


def test_create_nodes():
    create_nodes(expected_result)

    assert_that(len(Node.objects.all()), is_(4))

    transaction = Node.objects.get(
        name="Training and resources on"
             " workplace relations: registrations")
    tx_ancestors = [
        ancestor.name for ancestor in transaction.get_ancestors()]
    assert_that(tx_ancestors, equal_to(
        ["Attorney General's Office",
         "Crown Prosecution Service",
         "Training and resources on workplace relations",
         "Training and resources on workplace relations: registrations"]))

    service = Node.objects.get(
        name="Training and resources on"
             " workplace relations")
    service_ancestors = [
        ancestor.name for ancestor in service.get_ancestors()]
    assert_that(service_ancestors, equal_to(
        ["Attorney General's Office",
         "Crown Prosecution Service",
         "Training and resources on workplace relations"]))

    agency = Node.objects.get(
        name="Crown Prosecution Service")
    agency_ancestors = [
        ancestor.name for ancestor in agency.get_ancestors()]
    assert_that(agency_ancestors, equal_to(
        ["Attorney General's Office",
         "Crown Prosecution Service"]))

    department = Node.objects.get(
        name="Attorney General's Office")
    department_ancestors = [
        ancestor.name for ancestor in department.get_ancestors()]
    assert_that(department_ancestors, equal_to(
        ["Attorney General's Office"]))


def test_build_up_node_hash():
    result = build_up_node_hash(tx_fixture, govuk_fixture)
    assert_that(result, equal_to(expected_result))


def test_build_up_org_hash():
    expected_result = {
        'cps': {
            'name': 'Crown Prosecution Service',
            'abbreviation': 'CPS',
            'typeOf': 'agency',
            'parents': ['ago']
        },
        'ago': {
            'name': "Attorney General's Office",
            'abbreviation': 'AGO',
            'typeOf': 'department',
            'parents': []
        }
    }
    result = build_up_org_hash(govuk_fixture)
    assert_that(result, equal_to(expected_result))
