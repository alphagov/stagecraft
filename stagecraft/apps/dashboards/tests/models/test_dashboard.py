from django.test import TransactionTestCase
from hamcrest import (
    assert_that, has_entry, has_key, is_not, has_length, equal_to, instance_of,
    has_entries, has_items, has_property, is_, none, calling, raises,
    starts_with, contains, has_item
)

from ...models import Link, Module, ModuleType
from ....organisation.models import Node, NodeType
from stagecraft.apps.dashboards.tests.factories.factories import(
    DashboardFactory,
    LinkFactory,
    ModuleFactory,
    ModuleTypeFactory,
    DepartmentFactory,
    AgencyFactory,
    AgencyWithDepartmentFactory)


class DashboardTestCase(TransactionTestCase):

    def setUp(self):
        self.dashboard = DashboardFactory()

    def test_spotlightify_no_modules(self):
        spotlight_dashboard = self.dashboard.spotlightify()
        assert_that(spotlight_dashboard, has_entry('modules', []))

    def test_spotlightify_with_a_module(self):
        module_type = ModuleType.objects.create(name='graph', schema={})
        module = Module.objects.create(
            type=module_type,
            dashboard=self.dashboard,
            slug='a-module',
            options={},
            order=1,
        )

        module_type.save()
        module.save()

        spotlight_dashboard = self.dashboard.spotlightify()
        assert_that(len(spotlight_dashboard['modules']), equal_to(1))
        assert_that(
            spotlight_dashboard['modules'],
            has_item(has_entry('slug', 'a-module')))

        module.delete()
        module_type.delete()

    def test_transaction_link(self):
        self.dashboard.update_transaction_link('blah', 'http://www.gov.uk')
        self.dashboard.update_transaction_link('blah2', 'http://www.gov.uk')
        self.dashboard.validate_and_save()
        assert_that(self.dashboard.link_set.all(), has_length(1))
        assert_that(self.dashboard.link_set.first().title, equal_to('blah2'))
        assert_that(
            self.dashboard.link_set.first().link_type,
            equal_to('transaction')
        )

    def test_other_link(self):
        self.dashboard.add_other_link('blah', 'http://www.gov.uk')
        self.dashboard.add_other_link('blah2', 'http://www.gov.uk')
        self.dashboard.validate_and_save()
        links = self.dashboard.link_set.all()

        assert_that(links, has_length(2))
        assert_that(
            links,
            has_items(
                has_property('title', 'blah'),
                has_property('title', 'blah2'),
            )
        )
        assert_that(
            self.dashboard.link_set.first().link_type,
            equal_to('other')
        )

    def test_spotlightify_handles_other_and_transaction_links(self):
        self.dashboard.add_other_link('other', 'http://www.gov.uk')
        self.dashboard.add_other_link('other2', 'http://www.gov.uk')
        self.dashboard.update_transaction_link(
            'transaction',
            'http://www.gov.uk'
        )
        self.dashboard.validate_and_save()
        transaction_link = self.dashboard.get_transaction_link()
        assert_that(transaction_link, instance_of(Link))
        assert_that(
            transaction_link.link_type,
            equal_to('transaction')
        )
        assert_that(
            self.dashboard.get_other_links()[0].link_type,
            equal_to('other')
        )
        assert_that(
            self.dashboard.spotlightify(),
            has_entries({
                'title': 'title',
                'page-type': 'dashboard',
                'relatedPages': has_entries({
                    'improve-dashboard-message': True,
                    'transaction_link':
                    has_entries({
                        'url': 'http://www.gov.uk',
                        'title': 'transaction',
                        }),
                    'other_links':
                    has_items(
                        has_entries({
                            'url': 'http://www.gov.uk',
                            'title': 'other',
                        }),
                        has_entries({
                            'url': 'http://www.gov.uk',
                            'title': 'other2',
                        }),
                    )
                })
            })
        )

        assert_that(self.dashboard.spotlightify(), is_not(has_key('id')))
        assert_that(self.dashboard.spotlightify(), is_not(has_key('link')))

    def test_spotlightify_handles_dashboard_without_transaction_link(self):
        assert_that(
            self.dashboard.spotlightify(), has_entries({'title': 'title'}))

    def test_spotlightify_handles_department_and_agency(self):
        agency = AgencyWithDepartmentFactory()
        self.dashboard.organisation = agency
        self.dashboard.validate_and_save()
        assert_that(
            self.dashboard.spotlightify(),
            has_entry(
                'department',
                has_entries({
                    'title': starts_with('department'),
                    'abbr': starts_with('abbreviation')
                })
            )
        )
        assert_that(
            self.dashboard.spotlightify(),
            has_entry(
                'agency',
                has_entries({
                    'title': starts_with('agency'),
                    'abbr': starts_with('abbreviation')
                })
            )
        )

    def test_serialize_contains_dashboard_properties(self):
        data = self.dashboard.serialize()

        assert_that(data['title'], is_('title'))
        assert_that(data['published'], is_(True))

    def test_serialize_serializes_dashboard_links(self):
        link = LinkFactory(dashboard=self.dashboard)
        data = self.dashboard.serialize()

        expected_link = {
            'url': u'https://www.gov.uk/link-1',
            'title': u'Link title'
        }

        assert_that(data['links'], contains(expected_link))

    def test_serialize_contains_modules(self):
        module_type = ModuleTypeFactory()
        ModuleFactory(type=module_type, dashboard=self.dashboard,
                      order=2, slug='slug2')
        ModuleFactory(type=module_type, dashboard=self.dashboard,
                      order=1, slug='slug1')
        data = self.dashboard.serialize()

        assert_that(data['modules'],
                    contains(
                        has_entry('slug', 'slug1'),
                        has_entry('slug', 'slug2')))

    def test_agency_returns_none_when_no_organisation(self):
        assert_that(self.dashboard.agency(), is_(none()))

    def test_agency_returns_none_when_organisation_is_a_department(self):
        self.dashboard.organisation = DepartmentFactory()
        self.dashboard.save()

        assert_that(self.dashboard.agency(), is_(none()))

    def test_agency_returns_organisation_when_organisation_is_an_agency(self):
        agency = AgencyFactory()
        self.dashboard.organisation = agency
        assert_that(self.dashboard.agency(), equal_to(agency))

    def test_department_returns_organisation_when_organisation_is_a_department(self):  # noqa
        self.dashboard.organisation = DepartmentFactory()
        assert_that(
            self.dashboard.department(), equal_to(self.dashboard.organisation))

    def test_department_returns_agency_department_when_organisation_is_an_agency(self):  # noqa
        agency = AgencyWithDepartmentFactory()
        self.dashboard.organisation = agency
        assert_that(self.dashboard.department(), equal_to(agency.parent))

    def test_department_throws_exception_when_agency_has_no_department(self):
        self.dashboard.organisation = AgencyFactory()
        assert_that(calling(self.dashboard.department), raises(ValueError))

    def test_department_returns_none_when_organisation_is_none(self):
        assert_that(self.dashboard.department(), is_(none()))

    def create_department(self):
        department_type = NodeType.objects.create(
            name='department'
        )
        department = Node.objects.create(
            name='department-node',
            typeOf=department_type
        )
        department.save()
        return department

    def create_agency(self):
        agency_type = NodeType.objects.create(
            name='agency'
        )
        agency = Node.objects.create(
            name='agency-node',
            typeOf=agency_type
        )
        agency.save()
        return agency
