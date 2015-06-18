from __future__ import unicode_literals
import json

from django.test import TestCase
from hamcrest import (
    assert_that, equal_to, is_, has_property,
    contains, has_entry, has_entries, has_key, starts_with, has_length
)
from django_nose.tools import assert_redirects
from mock import patch

from stagecraft.apps.dashboards.tests.factories.factories import(
    DashboardFactory, DepartmentFactory, ModuleTypeFactory, ModuleFactory,
    LinkFactory)
from stagecraft.apps.datasets.tests.factories import DataSetFactory

from stagecraft.apps.dashboards.models.dashboard import (
    Dashboard)
from stagecraft.apps.dashboards.models.module import Module
from stagecraft.apps.dashboards.views.dashboard import fetch_dashboard
from stagecraft.apps.users.models import User
from stagecraft.libs.authorization.tests.test_http import (
    with_govuk_signon)
from stagecraft.libs.views.utils import to_json
from stagecraft.libs.views.utils import JsonEncoder


class DashboardViewsListTestCase(TestCase):

    @classmethod
    def setUpClass(cls):
        cls.user, _ = User.objects.get_or_create(
            email='foobar.lastname@gov.uk')

    @classmethod
    def tearDownClass(cls):
        pass

    def test_list_dashboards_lists_dashboards(self):
        DashboardFactory(
            slug='dashboard',
            title='Dashboard',
            status='published'
        )
        resp = self.client.get(
            '/dashboards',
            HTTP_AUTHORIZATION='Bearer development-oauth-access-token')
        response_object = json.loads(resp.content)

        public_url = ('http://spotlight.development.performance.service'
                      '.gov.uk/performance/dashboard')
        internal_url = ('http://stagecraft.development.performance.service'
                        '.gov.uk/dashboard/')
        base_expectation = {
            'title': 'Dashboard',
            'public-url': public_url,
            'published': True,
        }

        assert_that(response_object[0], has_entries(base_expectation))
        assert_that(response_object[0], has_key('id'))
        assert_that(response_object[0]['url'], starts_with(internal_url))

    def test_list_dashboards_list_alphabetically(self):
        DashboardFactory(slug='dashboard-1', title='Alpha')
        DashboardFactory(slug='dashboard-2', title='Beta')
        resp = self.client.get(
            '/dashboards',
            HTTP_AUTHORIZATION='Bearer development-oauth-access-token')
        response_object = json.loads(resp.content)

        assert_that(response_object[0]['title'], is_('Alpha'))
        assert_that(response_object[1]['title'], is_('Beta'))

    @patch(
        "stagecraft.apps.dashboards.models."
        "dashboard.Dashboard.list_for_spotlight")
    def test_get_dashboards_without_slug_returns_minimal_dashboards_json(
            self,
            patch_list_for_spotlight):
        returned_data = [
            {'i am in a list': 'this is a list'},
            {'more things in a list': 'yes'}]
        patch_list_for_spotlight.return_value = returned_data
        resp = self.client.get(
            '/public/dashboards', {})
        assert_that(resp.status_code, equal_to(200))
        assert_that(
            len(json.loads(resp.content)),
            equal_to(2)
        )
        assert_that(
            json.loads(resp.content)[0],
            has_entries(returned_data[0])
        )
        assert_that(
            json.loads(resp.content)[1],
            has_entries(returned_data[1])
        )

    def test_get_dashboards_with_slug_query_param_returns_dashboard_json(self):
        DashboardFactory(slug='my_first_slug')
        resp = self.client.get(
            '/public/dashboards', {'slug': 'my_first_slug'})
        assert_that(json.loads(resp.content), has_entry('slug',
                                                        'my_first_slug'))
        assert_that(resp['Cache-Control'], equal_to('max-age=300'))

    def test_public_dashboard_endpoint_has_cors_allowed(self):
        DashboardFactory(slug='my-dashboard')

        resp = self.client.get(
            '/public/dashboards', {'slug': 'my-dashboard'})
        assert_that(resp['Access-Control-Allow-Origin'], equal_to('*'))

    def test_get_dashboards_only_caches_when_published(self):
        DashboardFactory(slug='published_dashboard')
        DashboardFactory(slug='unpublished_dashboard', published=False)

        resp = self.client.get(
            '/public/dashboards', {'slug': 'published_dashboard'})
        assert_that(resp['Cache-Control'], equal_to('max-age=300'))

        resp = self.client.get(
            '/public/dashboards', {'slug': 'unpublished_dashboard'})
        assert_that(resp['Cache-Control'], equal_to('no-cache'))

    @patch(
        'stagecraft.apps.dashboards.models.dashboard.Dashboard.spotlightify')
    def test_get_dashboards_with_slug_query_param_returns_404_if_no_dashboard(
            self,
            spotlightify_patch):
        resp = self.client.get(
            '/public/dashboards', {'slug': 'my_first_slug'})
        assert_that(json.loads(resp.content), equal_to(
            {
                u'status': u'error',
                u'message': u"No dashboard with slug 'my_first_slug' exists",
                u'errors': [{
                    u'status': u'404',
                    u'title': u'',
                    u'code': u'',
                    u'detail': u"No dashboard with slug " +
                               u"'my_first_slug' exists",
                    u'id': u''},
                ]
            }))
        assert_that(resp.status_code, equal_to(404))

    def test_fetch_dashboard_with_multiple_slug_fragments(self):
        dashboard = DashboardFactory(slug='my_first_slug')
        dashboard.owners.add(self.user)
        slug = 'my_first_slug/another/thing'
        returned_dashboard = fetch_dashboard(slug)
        assert_that(dashboard.id, equal_to(returned_dashboard.id))

    @patch(
        'stagecraft.apps.dashboards.models.dashboard.Dashboard.spotlightify'
    )
    def test_public_dashboards_with_forward_slash_redirects(
            self,
            spotlightify_patch):
        resp = self.client.get(
            '/public/dashboards/', {'slug': 'my_first_slug'})
        assert_redirects(
            resp,
            'http://testserver/public/dashboards?slug=my_first_slug',
            status_code=301,
            target_status_code=404)

    def test_modules_are_ordered_correctly(self):
        dashboard = DashboardFactory(slug='my-first-slug')
        dashboard.owners.add(self.user)
        module_type = ModuleTypeFactory()
        ModuleFactory(
            type=module_type, dashboard=dashboard,
            order=2, slug='slug2')
        ModuleFactory(
            type=module_type, dashboard=dashboard,
            order=1, slug='slug1')
        ModuleFactory(
            type=module_type, dashboard=dashboard,
            order=3, slug='slug3')

        resp = self.client.get(
            '/public/dashboards', {'slug': 'my-first-slug'})

        data = json.loads(resp.content)
        assert_that(data['modules'],
                    contains(
                        has_entry('slug', 'slug1'),
                        has_entry('slug', 'slug2'),
                        has_entry('slug', 'slug3')))

    def test_dashboard_with_section_slug_returns_module_and_children(self):
        dashboard = DashboardFactory(slug='my-first-slug')
        dashboard.owners.add(self.user)
        module_type = ModuleTypeFactory()
        parent = ModuleFactory(
            type=module_type,
            slug='section-we-want',
            order=1,
            dashboard=dashboard
        )
        ModuleFactory(
            type=module_type,
            slug='module-we-want',
            order=2,
            dashboard=dashboard,
            parent=parent)

        resp = self.client.get(
            '/public/dashboards', {'slug': 'my-first-slug/section-we-want'})
        data = json.loads(resp.content)

        assert_that(data['modules'],
                    contains(has_entry('slug', 'section-we-want')))
        assert_that(len(data['modules']), equal_to(1))
        assert_that(data['modules'][0]['modules'],
                    contains(has_entry('slug', 'module-we-want')))
        assert_that(data, has_entry('page-type', 'module'))

    def test_dashboard_with_module_slug_only_returns_module(self):
        dashboard = DashboardFactory(slug='my-first-slug')
        dashboard.owners.add(self.user)
        module_type = ModuleTypeFactory()
        ModuleFactory(
            type=module_type, dashboard=dashboard,
            slug='module-we-want')
        ModuleFactory(
            type=module_type, dashboard=dashboard,
            slug='module-we-dont-want')
        resp = self.client.get(
            '/public/dashboards', {'slug': 'my-first-slug/module-we-want'})
        data = json.loads(resp.content)
        assert_that(data['modules'],
                    contains(has_entry('slug', 'module-we-want')))
        assert_that(data, has_entry('page-type', 'module'))

    def test_dashboard_with_sectioned_module_slug_only_returns_module(self):
        dashboard = DashboardFactory(slug='my-first-slug')
        dashboard.owners.add(self.user)
        module_type = ModuleTypeFactory()
        parent = ModuleFactory(
            type=module_type, dashboard=dashboard,
            slug='section-we-want')
        ModuleFactory(
            type=module_type, dashboard=dashboard,
            slug='module-we-want',
            parent=parent)
        resp = self.client.get(
            '/public/dashboards',
            {'slug': 'my-first-slug/section-we-want/module-we-want'}
        )
        data = json.loads(resp.content)
        assert_that(data['modules'],
                    contains(has_entry('slug', 'module-we-want')))
        assert_that(data, has_entry('page-type', 'module'))

    def test_dashboard_with_non_existing_module_slug_returns_nothing(self):
        dashboard = DashboardFactory(slug='my-first-slug')
        module_type = ModuleTypeFactory()
        ModuleFactory(
            type=module_type, dashboard=dashboard,
            slug='module-we-want')
        resp = self.client.get(
            '/public/dashboards', {'slug': 'my-first-slug/nonexisting-module'})
        data = json.loads(resp.content)
        assert_that(data, has_entry('status', 'error'))

    def test_dashboard_with_tab_slug_only_returns_tab(self):
        dashboard = DashboardFactory(slug='my-first-slug')
        dashboard.owners.add(self.user)
        module_type = ModuleTypeFactory()
        ModuleFactory(
            type=module_type, dashboard=dashboard,
            slug='module-we-want',
            info=['module-info'],
            title='module-title',
            options={
                'tabs': [
                    {
                        'slug': 'tab-we-want',
                        'title': 'tab-title'
                    },
                    {
                        'slug': 'tab-we-dont-want',
                    }
                ]
            })
        ModuleFactory(
            type=module_type, dashboard=dashboard,
            slug='module-we-dont-want')
        resp = self.client.get(
            '/public/dashboards',
            {'slug': 'my-first-slug/module-we-want/module-we-want-tab-we-want'}
        )
        data = json.loads(resp.content)
        assert_that(data['modules'],
                    contains(
                        has_entries({'slug': 'tab-we-want',
                                     'info': contains('module-info'),
                                     'title': 'module-title - tab-title'
                                     })))
        assert_that(data, has_entry('page-type', 'module'))

    def test_dashboard_with_sectioned_tab_slug_only_returns_tab(self):
        dashboard = DashboardFactory(slug='my-first-slug')
        dashboard.owners.add(self.user)
        module_type = ModuleTypeFactory()
        parent = ModuleFactory(
            type=module_type, dashboard=dashboard,
            slug='section-we-want')
        ModuleFactory(
            type=module_type, dashboard=dashboard,
            slug='module-we-want',
            info=['module-info'],
            title='module-title',
            options={
                'tabs': [
                    {
                        'slug': 'tab-we-want',
                        'title': 'tab-title'
                    },
                    {
                        'slug': 'tab-we-dont-want',
                    }
                ]
            },
            parent=parent
        )
        slug = 'my-first-slug/section-we-want/module-we-want/'
        slug += 'module-we-want-tab-we-want'
        resp = self.client.get(
            '/public/dashboards',
            {'slug': slug}
        )
        data = json.loads(resp.content)
        assert_that(data['modules'],
                    contains(
                        has_entries({'slug': 'tab-we-want',
                                     'info': contains('module-info'),
                                     'title': 'module-title - tab-title'
                                     })))
        assert_that(data, has_entry('page-type', 'module'))

    def test_dashboard_with_nonexistent_tab_slug_returns_nothing(self):
        dashboard = DashboardFactory(slug='my-first-slug')
        dashboard.owners.add(self.user)
        module_type = ModuleTypeFactory()
        ModuleFactory(
            type=module_type, dashboard=dashboard,
            slug='module',
            info=['module-info'],
            title='module-title',
            options={
                'tabs': [
                    {
                        'slug': 'tab-we-want',
                        'title': 'tab-title'
                    },
                    {
                        'slug': 'tab-we-dont-want',
                    }
                ]
            })
        ModuleFactory(
            type=module_type, dashboard=dashboard,
            slug='module-we-dont-want')
        resp = self.client.get(
            '/public/dashboards',
            {'slug': 'my-first-slug/module/module-non-existent-tab'}
        )
        data = json.loads(resp.content)
        assert_that(data, has_entry('status', 'error'))


class DashboardViewsGetTestCase(TestCase):

    @classmethod
    def setUpClass(cls):
        cls.user, _ = User.objects.get_or_create(
            email='foobar.lastname@gov.uk')

    @classmethod
    def tearDownClass(cls):
        pass

    @with_govuk_signon(permissions=['dashboard'])
    def test_404_when_user_not_in_ownership_array(self):
        dashboard = DashboardFactory()
        user, _ = User.objects.get_or_create(
            email='not_correct_user.lastname@gov.uk')
        dashboard.owners.add(user)

        resp = self.client.get('/dashboard/{}'.format(dashboard.slug),
                               HTTP_AUTHORIZATION='Bearer correct-token')

        assert_that(resp.status_code, equal_to(404))

    @with_govuk_signon(permissions=['dashboard'])
    def test_404_when_user_not_in_ownership_array_for_any_dashboards(self):
        dashboard = DashboardFactory()
        user, _ = User.objects.get_or_create(
            email='not_correct_user.lastname@gov.uk')
        dashboard.owners.add(user)

        resp = self.client.get('/dashboards',
                               HTTP_AUTHORIZATION='Bearer correct-token')

        assert_that(resp.status_code, equal_to(200))
        assert_that(json.loads(resp.content), equal_to([]))

    @with_govuk_signon(permissions=['dashboard'])
    def test_get_a_dashboard_with_incorrect_id_returns_404(self):
        resp = self.client.get(
            '/dashboard/non-existant-m8',
            HTTP_AUTHORIZATION='Bearer correct-token'
        )

        assert_that(resp.status_code, equal_to(404))

    @with_govuk_signon(permissions=['dashboard', 'user'])
    def test_get_an_existing_dashboard_returns_a_dashboard(self):
        dashboard = DashboardFactory(slug='slug1')
        dashboard.owners.add(self.user)

        resp = self.client.get(
            '/dashboard/{}'.format(dashboard.slug),
            HTTP_AUTHORIZATION='Bearer correct-token')

        assert_that(resp.status_code, equal_to(200))
        assert_that(
            json.loads(resp.content),
            has_entries(
                {
                    "description_extra": "",
                    "strapline": "Dashboard",
                    "description": "",
                    "links": [],
                    "title": "title",
                    "tagline": "",
                    "modules": [],
                    "dashboard_type": "transaction",
                    "slug": dashboard.slug,
                    "improve_dashboard_message": True,
                    "customer_type": "",
                    "costs": "",
                    "page_type": "dashboard",
                    "published": True,
                    "business_model": "",
                    "other_notes": ""
                }
            )
        )


class DashboardViewsUpdateTestCase(TestCase):

    @classmethod
    def setUpClass(cls):
        cls.user, _ = User.objects.get_or_create(
            email='foobar.lastname@gov.uk')

    @classmethod
    def tearDownClass(cls):
        pass

    @with_govuk_signon(permissions=['dashboard'])
    def test_change_title_of_dashboard_changes_title_of_dashboard(self):
        dashboard = DashboardFactory()
        dashboard.owners.add(self.user)
        dashboard_data = dashboard.serialize()

        dashboard_data['title'] = 'foo'

        resp = self.client.put(
            '/dashboard/{}'.format(dashboard.slug),
            json.dumps(dashboard_data, cls=JsonEncoder),
            content_type="application/json",
            HTTP_AUTHORIZATION='Bearer correct-token')

        assert_that(resp.status_code, equal_to(200))
        assert_that(
            Dashboard.objects.get(id=dashboard.id).title, equal_to('foo')
        )

    @with_govuk_signon(permissions=['dashboard'])
    def test_putting_to_nonexistant_dashboard_returns_404(self):
        dashboard = DashboardFactory()
        dashboard_data = dashboard.serialize()

        resp = self.client.put(
            '/dashboard/nonsense',
            json.dumps(dashboard_data, cls=JsonEncoder),
            content_type="application/json",
            HTTP_AUTHORIZATION='Bearer correct-token')

        assert_that(resp.status_code, equal_to(404))

    @with_govuk_signon(permissions=['dashboard'])
    def test_updating_module_attributes(self):
        dashboard = DashboardFactory(title='test dashboard')
        dashboard.owners.add(self.user)
        module = ModuleFactory(
            dashboard=dashboard,
            title='module-title',
            data_set=DataSetFactory()
        )
        new_data_set = DataSetFactory(
            data_group__name='new-group-title',
            data_type__name='new-type-title'
        )
        dashboard_data = dashboard.serialize()
        dashboard_data['modules'][0]['title'] = 'new module title'
        dashboard_data['modules'][0]['data_group'] = 'new-group-title'
        dashboard_data['modules'][0]['data_type'] = 'new-type-title'
        dashboard_data['modules'][0]['order'] = 1
        dashboard_data['modules'][0]['type_id'] = module.type_id
        dashboard_data['modules'][0]['query_parameters'] = {
            'sort_by': 'thing:desc',
        }
        dashboard_data['modules'][0]['modules'] = []

        resp = self.client.put(
            '/dashboard/{}'.format(dashboard.id),
            json.dumps(dashboard_data, cls=JsonEncoder),
            content_type="application/json",
            HTTP_AUTHORIZATION='Bearer correct-token')

        module_from_db = Module.objects.get(id=module.id)
        assert_that(resp.status_code, equal_to(200))
        assert_that(
            module_from_db.title,
            equal_to('new module title')
        )
        assert_that(
            module_from_db.data_set_id,
            equal_to(new_data_set.id)
        )

    @with_govuk_signon(permissions=['dashboard'])
    def test_updating_nested_module_attributes(self):
        dashboard = DashboardFactory(title='test dashboard')
        dashboard.owners.add(self.user)
        module = ModuleFactory(
            dashboard=dashboard,
            title='module-title',
            data_set=DataSetFactory()
        )
        nested_module = ModuleFactory(
            parent=module,
            dashboard=dashboard,
            title='module-title',
            data_set=DataSetFactory()
        )
        new_data_set = DataSetFactory(
            data_group__name='new-group-title',
            data_type__name='new-type-title'
        )
        dashboard_data = dashboard.serialize()
        dashboard_data['modules'][0]['order'] = 1
        dashboard_data['modules'][0]['type_id'] = module.type_id
        dashboard_data['modules'][0]['query_parameters'] = {
            'sort_by': 'thing:desc', }
        nested_data = dashboard_data['modules'][0]['modules'][0]
        nested_data['title'] = 'new module title'
        nested_data['data_group'] = 'new-group-title'
        nested_data['data_type'] = 'new-type-title'
        nested_data['order'] = 2
        nested_data['type_id'] = module.type_id
        nested_data['query_parameters'] = {'sort_by': 'thing:desc', }
        nested_data['modules'] = []

        resp = self.client.put(
            '/dashboard/{}'.format(dashboard.id),
            json.dumps(dashboard_data, cls=JsonEncoder),
            content_type="application/json",
            HTTP_AUTHORIZATION='Bearer correct-token')

        module_from_db = Module.objects.get(id=nested_module.id)
        assert_that(resp.status_code, equal_to(200))
        assert_that(
            module_from_db.title,
            equal_to('new module title')
        )
        assert_that(
            module_from_db.data_set_id,
            equal_to(new_data_set.id)
        )

    @with_govuk_signon(permissions=['dashboard'])
    def test_updating_module_with_nonexistent_dataset(self):
        dashboard = DashboardFactory(title='test dashboard')
        dashboard.owners.add(self.user)
        module = ModuleFactory(
            dashboard=dashboard,
            title='module-title',
        )
        dashboard_data = dashboard.serialize()
        dashboard_data['modules'][0]['title'] = 'new module title'
        dashboard_data['modules'][0]['data_group'] = 'non-existent-group'
        dashboard_data['modules'][0]['data_type'] = 'non-existent-type'
        dashboard_data['modules'][0]['order'] = 1
        dashboard_data['modules'][0]['type_id'] = module.type_id
        dashboard_data['modules'][0]['query_parameters'] = {
            'sort_by': 'thing:desc',
        }

        resp = self.client.put(
            '/dashboard/{}'.format(dashboard.id),
            json.dumps(dashboard_data, cls=JsonEncoder),
            content_type="application/json",
            HTTP_AUTHORIZATION='Bearer correct-token')

        assert_that(resp.status_code, equal_to(400))

    @with_govuk_signon(permissions=['dashboard'])
    def test_update_non_existent_module_doesnt_work(self):
        dashboard = DashboardFactory(title='test dashboard')
        dashboard.owners.add(self.user)
        dashboard_data = dashboard.serialize()
        dashboard_data['modules'] = [
            {
                'id': '623b6e9c-507f-4c5c-8937-7ea81a349cfa',
                'title': 'non-existent-title'
            }
        ]

        resp = self.client.put(
            '/dashboard/{}'.format(dashboard.id),
            json.dumps(dashboard_data, cls=JsonEncoder),
            content_type="application/json",
            HTTP_AUTHORIZATION='Bearer correct-token')

        assert_that(resp.status_code, equal_to(400))

    @with_govuk_signon(permissions=['dashboard'])
    def test_removing_module(self):
        dashboard = DashboardFactory(title='test dashboard')
        dashboard.owners.add(self.user)
        module = ModuleFactory(
            title='module to remove', dashboard=dashboard)
        dashboard_data = dashboard.serialize()
        dashboard_data['modules'] = [
        ]

        resp = self.client.put(
            '/dashboard/{}'.format(dashboard.id),
            json.dumps(dashboard_data, cls=JsonEncoder),
            content_type="application/json",
            HTTP_AUTHORIZATION='Bearer correct-token')

        assert_that(resp.status_code, equal_to(200))
        assert_that(json.loads(
            resp.content), has_entry('modules', has_length(0)))
        assert_that(Module.objects.filter(id=module.id), has_length(0))

    @with_govuk_signon(permissions=['dashboard'])
    def test_removing_nested_module(self):
        dashboard = DashboardFactory(title='test dashboard')
        dashboard.owners.add(self.user)
        parent = ModuleFactory(dashboard=dashboard, title='parent')
        child = ModuleFactory(
            parent=parent, dashboard=dashboard, title='module to remove')
        child_of_child = ModuleFactory(
            title='child of child', parent=child, dashboard=dashboard)
        dashboard_data = dashboard.serialize()
        dashboard_data['modules'][0]['order'] = 1
        dashboard_data['modules'][0]['type_id'] = parent.type_id
        child_data = dashboard_data['modules'][0]['modules'][0]
        child_of_child_data = child_data['modules'][0]
        child_of_child_data['order'] = 2
        child_of_child_data['type_id'] = child_of_child.type_id
        dashboard_data['modules'][0]['modules'] = [child_of_child_data]

        resp = self.client.put(
            '/dashboard/{}'.format(dashboard.id),
            json.dumps(dashboard_data, cls=JsonEncoder),
            content_type="application/json",
            HTTP_AUTHORIZATION='Bearer correct-token')

        assert_that(resp.status_code, equal_to(200))
        parent_json = json.loads(resp.content)['modules'][0]
        child_json = parent_json['modules'][0]
        assert_that(parent_json['title'], equal_to('parent'))
        assert_that(child_json['title'], equal_to('child of child'))
        assert_that(child_json['modules'], has_length(0))
        assert_that(Module.objects.filter(id=child.id), has_length(0))
        assert_that(Module.objects.get(id=child_of_child.id).parent,
                    equal_to(parent))

    @with_govuk_signon(permissions=['dashboard'])
    def test_update_existing_link(self):
        dashboard = DashboardFactory(title='test dashboard')
        dashboard.owners.add(self.user)
        link = LinkFactory(dashboard=dashboard)
        dashboard_data = dashboard.serialize()
        dashboard_data['links'][0]['url'] = 'https://gov.uk/new-link'
        dashboard_data['links'][0]['title'] = 'new link title'

        self.client.put(
            '/dashboard/{}'.format(dashboard.id),
            json.dumps(dashboard_data, cls=JsonEncoder),
            content_type="application/json",
            HTTP_AUTHORIZATION='Bearer correct-token')

        transaction_links = dashboard.link_set.filter(link_type='transaction')
        assert_that(transaction_links, has_length(1))
        link = transaction_links[0]
        assert_that(link.title, equal_to('new link title'))
        assert_that(link.url, equal_to('https://gov.uk/new-link'))


class DashboardViewsCreateTestCase(TestCase):

    def _get_dashboard_payload(self, **kwargs):
        data = {
            "slug": "foo",
            "dashboard-type": "transaction",
            "page-type": "dashboard",
            "published": True,
            "title": "Foo dashboard",
            "description": "This is a foo",
            "description-extra": "This is some extra",
            "costs": "eh?",
            "other-notes": "some other notes",
            "customer-type": "Business",
            "business-model": "Department budget",
            "improve-dashboard-message": True,
            "strapline": "Dashboard",
            "tagline": "This is the tagline",
            "organisation": None,
            "links": [
                {
                    "title": "External link",
                    "url": "https://www.gov.uk/",
                    "type": "transaction",
                }
            ],
        }
        for k, v in kwargs.iteritems():
            data[k.replace('_', '-')] = v

        return data

    @with_govuk_signon(permissions=['dashboard'])
    def test_create_dashboard_with_organisation(self):
        department = DepartmentFactory()
        data = self._get_dashboard_payload(
            organisation=str(department.id))

        resp = self.client.post(
            '/dashboard', json.dumps(data),
            content_type="application/json",
            HTTP_AUTHORIZATION='Bearer correct-token')

        assert_that(resp.status_code, equal_to(200))
        assert_that(Dashboard.objects.count(), equal_to(1))

    @with_govuk_signon(permissions=['dashboard'])
    def test_create_dashboard_adds_owner(self):
        department = DepartmentFactory()
        data = self._get_dashboard_payload(
            organisation=str(department.id))

        resp = self.client.post(
            '/dashboard', json.dumps(data),
            content_type="application/json",
            HTTP_AUTHORIZATION='Bearer correct-token')

        assert_that(resp.status_code, equal_to(200))
        dashboard = Dashboard.objects.get(
            slug=self._get_dashboard_payload()['slug'])
        assert_that(len(dashboard.owners.all()), equal_to(1))
        assert_that(
            dashboard.owners.first().email,
            equal_to('foobar.lastname@gov.uk'))

    @with_govuk_signon(permissions=['dashboard'])
    def test_create_dashboard_fails_with_invalid_organisation_uuid(self):
        data = self._get_dashboard_payload(organisation='invalid')

        resp = self.client.post(
            '/dashboard', json.dumps(data),
            content_type="application/json",
            HTTP_AUTHORIZATION='Bearer correct-token')

        assert_that(resp.status_code, equal_to(400))
        assert_that(Dashboard.objects.count(), equal_to(0))

    @with_govuk_signon(permissions=['dashboard'])
    def test_create_dashboard_fails_with_non_existent_organisation(self):
        data = self._get_dashboard_payload(
            organisation='7969dcd9-7e9e-4cab-a352-424d57724523')

        resp = self.client.post(
            '/dashboard', json.dumps(data),
            content_type="application/json",
            HTTP_AUTHORIZATION='Bearer correct-token')

        assert_that(resp.status_code, equal_to(404))
        assert_that(Dashboard.objects.count(), equal_to(0))

    @with_govuk_signon(permissions=['dashboard'])
    def test_create_dashboard_ok_with_no_organisation(self):
        data = self._get_dashboard_payload(
            organisation=None)

        resp = self.client.post(
            '/dashboard', json.dumps(data),
            content_type="application/json",
            HTTP_AUTHORIZATION='Bearer correct-token')

        assert_that(resp.status_code, equal_to(200))
        assert_that(Dashboard.objects.count(), equal_to(1))

    @with_govuk_signon(permissions=['dashboard'])
    def test_create_dashboard_ok_with_links(self):
        data = self._get_dashboard_payload()

        resp = self.client.post(
            '/dashboard', json.dumps(data),
            content_type="application/json",
            HTTP_AUTHORIZATION='Bearer correct-token')

        dashboard = Dashboard.objects.first()

        assert_that(resp.status_code, equal_to(200))
        assert_that(dashboard.link_set.count(), equal_to(1))
        assert_that(dashboard.link_set.all(),
                    contains(has_property('title',
                                          equal_to('External link'))))

    @with_govuk_signon(permissions=['dashboard'])
    def test_create_dashboard_ok_with_modules(self):
        module_type = ModuleTypeFactory()

        def make_module(slug, title, order):
            return {
                'slug': slug,
                'title': title,
                'type_id': module_type.id,
                'description': 'a description',
                'info': [],
                'options': {},
                'order': order,
                'modules': [],
            }

        data = self._get_dashboard_payload()
        data['modules'] = [
            make_module('foo', 'The Foo', 1),
            make_module('bar', 'The Bar', 4),
            make_module('monkey', 'The the', 2),
        ]
        data['modules'][2]['modules'] = [make_module('chimp', 'Ooh', 3)]

        resp = self.client.post(
            '/dashboard', to_json(data),
            content_type="application/json",
            HTTP_AUTHORIZATION='Bearer correct-token')

        assert_that(resp.status_code, equal_to(200))
        dashboard = Dashboard.objects.first()
        assert_that(dashboard.module_set.count(), equal_to(4))
        nested_module = Module.objects.get(slug='chimp')
        assert_that(nested_module.parent.slug, equal_to('monkey'))

    @with_govuk_signon(permissions=['dashboard'])
    def test_create_dashboard_fails_with_invalid_module(self):
        module_type = ModuleTypeFactory()
        module = {
            'slug': 'bad slug',
            'title': 'bad slug',
            'type_id': module_type.id,
            'description': '',
            'info': [],
            'options': {},
            'order': 1,
        }
        data = self._get_dashboard_payload()
        data['modules'] = [module]

        resp = self.client.post(
            '/dashboard', to_json(data),
            content_type="application/json",
            HTTP_AUTHORIZATION='Bearer correct-token')

        assert_that(resp.status_code, equal_to(400))

    @with_govuk_signon(permissions=['dashboard'])
    def test_create_dashboard_failure_rolls_back_transaction(self):
        module_type = ModuleTypeFactory()
        module = {
            'slug': 'bad slug',
            'title': 'bad slug',
            'type_id': module_type.id,
            'description': '',
            'info': [],
            'options': {},
            'order': 1,
        }
        data = self._get_dashboard_payload()
        data['modules'] = [module]

        resp = self.client.post(
            '/dashboard', to_json(data),
            content_type="application/json",
            HTTP_AUTHORIZATION='Bearer correct-token')

        assert_that(resp.status_code, equal_to(400))
        assert_that(Dashboard.objects.count(), equal_to(0))

    @with_govuk_signon(permissions=['dashboard'])
    def test_create_dashboard_with_reused_slug_is_bad_request(self):
        data = self._get_dashboard_payload()

        resp = self.client.post(
            '/dashboard', json.dumps(data),
            content_type="application/json",
            HTTP_AUTHORIZATION='Bearer correct-token')

        second_resp = self.client.post(
            '/dashboard', json.dumps(data),
            content_type="application/json",
            HTTP_AUTHORIZATION='Bearer correct-token')

        assert_that(resp.status_code, equal_to(200))
        assert_that(second_resp.status_code, equal_to(400))
        assert_that(Dashboard.objects.count(), equal_to(1))

    @with_govuk_signon(permissions=['dashboard'])
    def test_dashboard_failing_validation_returns_error(self):
        data = {
            'slug': 'my-dashboard',
            'title': 'My dashboard',
            'strapline': 'Invalid',
        }

        resp = self.client.post(
            '/dashboard', json.dumps(data),
            content_type='application/json',
            HTTP_AUTHORIZATION='Bearer correct-token')
        expected_message = "validation errors:\n" \
                           "strapline: Value u'Invalid' is not a valid choice."

        response_dict = json.loads(resp.content)
        assert_that(resp.status_code, equal_to(400))
        assert_that(response_dict['message'], equal_to(expected_message))
