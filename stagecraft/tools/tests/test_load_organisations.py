from hamcrest import (
    assert_that, is_not, is_, equal_to
)
from django.test import TestCase
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


class LoadOrganisationsTestCase(TestCase):

    @classmethod
    def setUpClass(cls):
        cls.tx_data_set = DataSetFactory(
            data_group__name='transactional_services',
            data_type__name='summaries'
        )
        cls.kpi_module = ModuleFactory(
            dashboard=DashboardFactory(published=True),
            data_set=cls.tx_data_set,
            query_parameters={
                'filter_by': ['service_id:bis-acas-elearning-registrations'],
            }
        )

    @patch('stagecraft.tools.load_organisations.load_data')
    def test_load_organisations(self, mock_load_data):
        mock_load_data.return_value = tx_fixture, govuk_fixture

        dashboard = self.__class__.kpi_module.dashboard

        load_organisations('foo', 'bar')

        dashboard = Dashboard.objects.get(id=dashboard.id)

        assert_that(dashboard.organisation, is_not(None))

        org_parents = [org for org in dashboard.organisation.get_ancestors(
            include_self=True)]

        assert_that(len(org_parents), is_(5))

        assert_that(
            dashboard.organisation.name,
            equal_to(
                "Registrations to use online training and resources on"
                " workplace relations"))
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

        parents = parent_org.parents.all()
        assert_that(len(parents), equal_to(2))
        parent_org = parents[0]
        assert_that(
            parent_org.name,
            equal_to("Attorney General's Office"))
        assert_that(
            parent_org.typeOf.name,
            equal_to("department"))
        parent_org = parents[1]
        assert_that(
            parent_org.name,
            equal_to("Foo thing"))
        assert_that(
            parent_org.typeOf.name,
            equal_to("department"))

    @patch('stagecraft.tools.load_organisations.load_data')
    def test_load_organisations_same_result_if_run_twice(self, mock_load_data):
        mock_load_data.return_value = tx_fixture, govuk_fixture

        what_happened = load_organisations('foo', 'bar')
        assert_that(len(what_happened['dashboards_at_start']), equal_to(1))
        assert_that(len(what_happened['dashboards_at_end']), equal_to(1))
        assert_that(len(what_happened['total_nodes_before']), equal_to(0))
        assert_that(len(what_happened['total_nodes_after']), equal_to(5))
        assert_that(len(what_happened['organisations']), equal_to(3))
        assert_that(len(what_happened['transactions']), equal_to(1))
        assert_that(len(what_happened['created_nodes']), equal_to(5))
        assert_that(len(what_happened['existing_nodes']), equal_to(0))
        assert_that(
            len(what_happened['unable_to_find_or_create_nodes']), equal_to(0))
        assert_that(
            len(what_happened['unable_existing_nodes_diff_details']),
            equal_to(0))
        assert_that(
            len(what_happened['unable_existing_nodes_diff_details_msgs']),
            equal_to(0))
        assert_that(len(what_happened['unable_data_error_nodes']), equal_to(0))
        assert_that(
            len(what_happened['unable_data_error_nodes_msgs']), equal_to(0))
        assert_that(len(what_happened['duplicate_services']), equal_to(0))
        assert_that(len(what_happened['duplicate_transactions']), equal_to(0))
        assert_that(len(
            what_happened['duplicate_dep_or_agency_abbreviations']),
            equal_to(0))
        assert_that(
            len(what_happened['link_to_parents_not_found']),
            equal_to(0))
        assert_that(len(what_happened['link_to_parents_found']), equal_to(1))
        assert_that(
            len(what_happened['transactions_associated_with_dashboards']),
            equal_to(1))
        assert_that(
            len(what_happened['transactions_not_associated_with_dashboards']),
            equal_to(0))

        what_happened = load_organisations('foo', 'bar')
        assert_that(len(what_happened['dashboards_at_start']), equal_to(1))
        assert_that(len(what_happened['dashboards_at_end']), equal_to(1))
        assert_that(len(what_happened['total_nodes_before']), equal_to(0))
        assert_that(len(what_happened['total_nodes_after']), equal_to(5))
        assert_that(len(what_happened['organisations']), equal_to(3))
        assert_that(len(what_happened['transactions']), equal_to(1))
        assert_that(len(what_happened['created_nodes']), equal_to(5))
        assert_that(len(what_happened['existing_nodes']), equal_to(0))
        assert_that(
            len(what_happened['unable_to_find_or_create_nodes']), equal_to(0))
        assert_that(
            len(what_happened['unable_existing_nodes_diff_details_msgs']),
            equal_to(0))
        assert_that(len(what_happened['unable_data_error_nodes']), equal_to(0))
        assert_that(
            len(what_happened['unable_data_error_nodes_msgs']), equal_to(0))
        assert_that(len(what_happened['unable_data_error_nodes']), equal_to(0))
        assert_that(len(what_happened['duplicate_services']), equal_to(0))
        assert_that(len(what_happened['duplicate_transactions']), equal_to(0))
        assert_that(len(
            what_happened['duplicate_dep_or_agency_abbreviations']),
            equal_to(0))
        assert_that(
            len(what_happened['link_to_parents_not_found']),
            equal_to(0))
        assert_that(len(what_happened['link_to_parents_found']), equal_to(1))
        assert_that(
            len(what_happened['transactions_associated_with_dashboards']),
            equal_to(1))
        assert_that(
            len(what_happened['transactions_not_associated_with_dashboards']),
            equal_to(0))

# this is the intermediate data format built up from external data
# it is then used to actually create and update things in the database.
expected_result = {
    "Registrations to use online training and resources"
    " on workplace relations": {
        'name': "Registrations to use online training and resources"
                " on workplace relations",
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
        'parents': [u'ago', u'foo']
    },
    u'ago': {
        'name': "Attorney General's Office",
        'abbreviation': u'AGO',
        'typeOf': 'department',
        'parents': []
    },
    u'foo': {
        'name': u'Foo thing',
        'abbreviation': u'foo',
        'typeOf': 'department',
        'parents': []
    }
}


def test_create_nodes():
    create_nodes(expected_result)

    assert_that(len(Node.objects.all()), is_(5))

    transaction = Node.objects.get(
        name="Registrations to use online training and resources on"
             " workplace relations")
    tx_ancestors = [
        ancestor.name for ancestor in transaction.get_ancestors()]
    assert_that(tx_ancestors, equal_to(
        ["Attorney General's Office",
         "Foo thing",
         "Crown Prosecution Service",
         "Training and resources on workplace relations",
         "Registrations to use online training and resources on"
         " workplace relations"]))

    service = Node.objects.get(
        name="Training and resources on"
             " workplace relations")
    service_ancestors = [
        ancestor.name for ancestor in service.get_ancestors()]
    assert_that(service_ancestors, equal_to(
        ["Attorney General's Office",
         "Foo thing",
         "Crown Prosecution Service",
         "Training and resources on workplace relations"]))

    agency = Node.objects.get(
        name="Crown Prosecution Service")
    agency_ancestors = [
        ancestor.name for ancestor in agency.get_ancestors()]
    assert_that(agency_ancestors, equal_to(
        ["Attorney General's Office",
         "Foo thing",
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
            'typeOf': 'department',
            'parents': ['ago', 'foo']
        },
        'ago': {
            'name': "Attorney General's Office",
            'abbreviation': 'AGO',
            'typeOf': 'department',
            'parents': []
        },
        'foo': {
            'name': "Foo thing",
            'abbreviation': 'foo',
            'typeOf': 'department',
            'parents': []
        }
    }
    result = build_up_org_hash(govuk_fixture)
    assert_that(result, equal_to(expected_result))
