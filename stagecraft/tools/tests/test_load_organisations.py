from hamcrest import (
    assert_that, is_not, is_, equal_to
)
from mock import patch
import json
from stagecraft.apps.organisation.models import Node
from stagecraft.apps.dashboards.models import Dashboard

from stagecraft.apps.dashboards.tests.factories.factories import(
    ModuleFactory,
    DashboardFactory)
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
        data_group__name='transactional_services',
        data_type__name='summaries'
    )
    kpi_module = ModuleFactory(
        dashboard=DashboardFactory(published=True),
        data_set=tx_data_set,
        query_parameters={
            'filter_by': ['service_id:bis-acas-elearning-registrations'],
        }
    )
    dashboard = kpi_module.dashboard

    load_organisations('foo', 'bar')

    dashboard = Dashboard.objects.get(id=dashboard.id)

    assert_that(dashboard.organisation, is_not(None))

    org_parents = [org for org in dashboard.organisation.get_ancestors(
        include_self=True)]

    assert_that(len(org_parents), is_(4))

    assert_that(
        dashboard.organisation.name,
        equal_to(
            "Training and resources on workplace relations: registrations"))
    assert_that(
        dashboard.organisation.typeOf.name,
        equal_to("transaction"))

    parent_org = dashboard.organisation.parents.first()
    assert_that(
        parent_org.name,
        equal_to("Training and resources on workplace relations"))
    assert_that(
        parent_org.typeOf.name,
        equal_to("service"))

    parent_org = parent_org.parents.first()
    assert_that(
        parent_org.name,
        equal_to("Crown Prosecution Service"))
    assert_that(
        parent_org.typeOf.name,
        equal_to("agency"))

    parent_org = parent_org.parents.first()
    assert_that(
        parent_org.name,
        equal_to("Attorney General's Office"))
    assert_that(
        parent_org.typeOf.name,
        equal_to("department"))

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
