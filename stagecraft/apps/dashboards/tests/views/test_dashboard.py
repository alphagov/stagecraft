from __future__ import unicode_literals
import json

from django.test import TestCase
from hamcrest import (
    assert_that, equal_to, is_, none, has_property,
    contains, has_entry, has_entries, has_key, starts_with
)
from django_nose.tools import assert_redirects
from mock import patch

from stagecraft.apps.dashboards.tests.factories.factories import(
    DashboardFactory, DepartmentFactory, ModuleTypeFactory, ModuleFactory)
from stagecraft.apps.dashboards.models.dashboard import (
    Dashboard)
from stagecraft.apps.dashboards.views.dashboard import(
    recursively_fetch_dashboard)
from stagecraft.libs.authorization.tests.test_http import (
    with_govuk_signon)
from stagecraft.libs.views.utils import to_json
from stagecraft.libs.views.utils import JsonEncoder


class DashboardViewsListTestCase(TestCase):

    def test_list_dashboards_lists_dashboards(self):
        DashboardFactory(slug='dashboard', title='Dashboard', published=True)
        resp = self.client.get(
            '/dashboards',
            HTTP_AUTHORIZATION='Bearer development-oauth-access-token')
        response_object = json.loads(resp.content)['dashboards']

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

    def test_recursively_fetch_dashboard_recurses_down_the_slug_fragments(
            self):
        dashboard = DashboardFactory(slug='experimental/my_first_slug')
        slug = 'experimental/my_first_slug/another/thing'
        returned_dashboard = recursively_fetch_dashboard(slug)
        assert_that(dashboard.id, equal_to(returned_dashboard.id))

    def test_recursively_fetch_dashboard_returns_none_after_3_levels(
            self):
        DashboardFactory(slug='my_first_slug')
        slug = 'my_first_slug/some_url_fragment/another/another'
        returned_dashboard = recursively_fetch_dashboard(slug)
        assert_that(returned_dashboard, is_(none()))

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

    def test_dashboard_with_module_slug_only_returns_module(self):
        dashboard = DashboardFactory(slug='my-first-slug')
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

    def test_dashboard_with_nonexistent_tab_slug_returns_nothing(self):
        dashboard = DashboardFactory(slug='my-first-slug')
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

    @with_govuk_signon(permissions=['dashboard'])
    def test_get_a_dashboard_with_incorrect_id_or_no_id_returns_404(self):
        resp = self.client.get(
            '/dashboard/', HTTP_AUTHORIZATION='Bearer correct-token'
        )
        second_response = self.client.get(
            '/dashboard/non-existant-m8',
            HTTP_AUTHORIZATION='Bearer correct-token'
        )

        assert_that(resp.status_code, equal_to(404))
        assert_that(second_response.status_code, equal_to(404))

    @with_govuk_signon(permissions=['dashboard'])
    def test_get_an_existing_dashboard_returns_a_dashboard(self):
        dashboard = DashboardFactory()

        resp = self.client.get(
            '/dashboard/{}'.format(dashboard.id),
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
                    "organisation": None,
                    "modules": [],
                    "dashboard_type": "transaction",
                    "slug": "slug1",
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

    @with_govuk_signon(permissions=['dashboard'])
    def test_change_title_of_dashboard_changes_title_of_dashboard(self):
        dashboard = DashboardFactory()
        dashboard_data = dashboard.serialize()

        dashboard_data['title'] = 'foo'

        resp = self.client.put(
            '/dashboard/{}'.format(dashboard.id),
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
            organisation='{}'.format(department.id))

        resp = self.client.post(
            '/dashboard', json.dumps(data),
            content_type="application/json",
            HTTP_AUTHORIZATION='Bearer correct-token')

        assert_that(resp.status_code, equal_to(200))
        assert_that(Dashboard.objects.count(), equal_to(1))

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

        assert_that(resp.status_code, equal_to(400))
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
            }

        data = self._get_dashboard_payload()
        data['modules'] = [
            make_module('foo', 'The Foo', 1),
            make_module('bar', 'The Bar', 3),
            make_module('monkey', 'The the', 2),
        ]

        resp = self.client.post(
            '/dashboard', to_json(data),
            content_type="application/json",
            HTTP_AUTHORIZATION='Bearer correct-token')

        assert_that(resp.status_code, equal_to(200))
        dashboard = Dashboard.objects.first()
        assert_that(dashboard.module_set.count(), equal_to(3))

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
    def test_dashboard_failing_validation_returns_json_error(self):
        data = {
            'slug': 'my-dashboard',
            'title': 'My dashboard',
            'strapline': 'Invalid',
        }

        resp = self.client.post(
            '/dashboard', json.dumps(data),
            content_type='application/json',
            HTTP_AUTHORIZATION='Bearer correct-token')
        response_dictionary = json.loads(resp.content)
        expected_message = "strapline: Value u'Invalid' is not a valid choice."

        assert_that(resp.status_code, equal_to(400))
        assert_that(response_dictionary['status'], equal_to('error'))
        assert_that(response_dictionary['message'],
                    equal_to(expected_message))
