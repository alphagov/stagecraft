from django.test import TransactionTestCase
from hamcrest import (
    assert_that, has_entry, has_key, is_not, has_length, equal_to, instance_of,
    has_entries, has_items, has_property, is_, none, calling, raises,
    starts_with, contains, has_item
)

from ...models import Link, Dashboard
from stagecraft.apps.dashboards.tests.factories.factories import(
    AgencyFactory,
    AgencyWithDepartmentFactory,
    DashboardFactory,
    DepartmentFactory,
    LinkFactory,
    ModuleFactory,
    ModuleTypeFactory)


class DashboardTestCase(TransactionTestCase):

    def setUp(self):
        self.dashboard = DashboardFactory()

    def test_class_level_list_for_spotlight_returns_minimal_json_array(self):
        dashboard_two = DashboardFactory()
        dashboard_two.organisation = AgencyWithDepartmentFactory()
        dashboard_two.validate_and_save()
        DashboardFactory(published=False)
        list_for_spotlight = Dashboard.list_for_spotlight()
        assert_that(list_for_spotlight['page-type'], equal_to('browse'))
        assert_that(len(list_for_spotlight['items']), equal_to(2))
        assert_that(list_for_spotlight['items'][1],
                    has_entries({
                        'slug': starts_with('slug'),
                        'title': 'title',
                        'dashboard-type': 'transaction',
                        'department': has_entries({
                            'title': starts_with('department'),
                            'abbr': starts_with('abbreviation')
                        }),
                        'agency': has_entries({
                            'title': starts_with('agency'),
                            'abbr': starts_with('abbreviation')
                        })
                    }))
        assert_that(list_for_spotlight['items'][0],
                    has_entries({
                        'slug': starts_with('slug'),
                        'title': 'title',
                        'dashboard-type': 'transaction'
                    }))

    def test_spotlightify_no_modules(self):
        spotlight_dashboard = self.dashboard.spotlightify()
        assert_that(spotlight_dashboard, has_entry('modules', []))

    def test_spotlightify_with_a_module(self):
        module_type = ModuleTypeFactory(name='graph', schema={})
        ModuleFactory(
            type=module_type,
            dashboard=self.dashboard,
            slug='a-module',
            options={},
            order=1,
        )

        spotlight_dashboard = self.dashboard.spotlightify()
        assert_that(len(spotlight_dashboard['modules']), equal_to(1))
        assert_that(
            spotlight_dashboard['modules'],
            has_item(has_entry('slug', 'a-module')))

    def test_spotlightify_with_a_nested_module(self):
        section_type = ModuleTypeFactory(name='section')
        graph_type = ModuleTypeFactory(name='graph')
        parent = ModuleFactory(
            type=section_type,
            slug='a-module',
            order=1,
            dashboard=self.dashboard
        )
        ModuleFactory(
            type=graph_type,
            slug='b-module',
            order=2,
            dashboard=self.dashboard,
            parent=parent)

        spotlightify = self.dashboard.spotlightify()

        assert_that(
            spotlightify,
            has_entry('modules', contains(parent.spotlightify()))
        )
        assert_that(len(spotlightify['modules']), equal_to(1))

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
                    'transaction':
                    has_entries({
                        'url': 'http://www.gov.uk',
                        'title': 'transaction',
                    }),
                    'other':
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
        LinkFactory(dashboard=self.dashboard, url='https://www.gov.uk/url')
        data = self.dashboard.serialize()

        expected_link = {
            'url': u'https://www.gov.uk/url',
            'type': u'transaction',
            'title': u'Link title'
        }

        assert_that(data['links'], contains(expected_link))

    def test_serialize_contains_nested_modules(self):
        module_type = ModuleTypeFactory()
        ModuleFactory(type=module_type, dashboard=self.dashboard,
                      order=3, slug='slug3')
        parent = ModuleFactory(type=module_type, dashboard=self.dashboard,
                               order=1, slug='slug1')
        ModuleFactory(parent=parent, type=module_type, order=2, slug='slug2')
        data = self.dashboard.serialize()

        assert_that(data['modules'],
                    contains(
                        has_entry('slug', 'slug1'),
                        has_entry('slug', 'slug3')))

        assert_that(data['modules'][0]['modules'][0],
                    has_entry('slug', 'slug2'))

        assert_that(data['modules'],
                    is_not(has_entry('slug', 'slug2')))

    def test_agency_returns_none_when_no_organisation(self):
        assert_that(self.dashboard.agency(), is_(none()))

    def test_agency_returns_none_when_organisation_is_a_department(self):
        self.dashboard.organisation = DepartmentFactory()

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
        assert_that(
            self.dashboard.department(), equal_to(agency.parents.first()))

    def test_department_throws_exception_when_agency_has_no_department(self):
        self.dashboard.organisation = AgencyFactory()
        assert_that(calling(self.dashboard.department), raises(ValueError))

    def test_department_returns_none_when_organisation_is_none(self):
        assert_that(self.dashboard.department(), is_(none()))
