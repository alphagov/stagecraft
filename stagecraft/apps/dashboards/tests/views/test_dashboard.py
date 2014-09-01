import json

from django.test import TestCase
from hamcrest import assert_that, equal_to, is_, none
from mock import patch

from stagecraft.apps.dashboards.tests.factories.factories import(
    DashboardFactory, DepartmentFactory)
from stagecraft.apps.dashboards.models.dashboard import (
    Dashboard)
from stagecraft.apps.dashboards.views.dashboard import(
    recursively_fetch_dashboard)
from stagecraft.libs.authorization.tests.test_http import govuk_signon_mock


class DashboardViewsListTestCase(TestCase):

    @patch(
        'stagecraft.apps.dashboards.models.dashboard.Dashboard.spotlightify')
    def test_get_dashboards_with_slug_query_param_returns_dashboard_json(
            self,
            spotlightify_patch):
        DashboardFactory(slug='my_first_slug')
        spotlightify_response = {
            'this': {
                'response': 'is',
                'nonsense': 1234}
        }
        spotlightify_patch.return_value = spotlightify_response
        resp = self.client.get(
            '/public/dashboards', {'slug': 'my_first_slug/this'})
        assert_that(json.loads(resp.content), equal_to(spotlightify_response))
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
                u'message': u"No dashboard with slug 'my_first_slug' exists"}))
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


class DashboardViewsCreateTestCase(TestCase):
    def setUp(self):
        settings.USE_DEVELOPMENT_USERS = False

    def tearDown(self):
        settings.USE_DEVELOPMENT_USERS = True

    def test_create_a_new_dashboard_with_no_modules(self):
        department = DepartmentFactory()
        data = {
            "slug": "/foo",
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
            "strapline": "This is the strapline",
            "tagline": "This is the tagline",
            "organisation": "{}".format(department.id),
        }
        signon = govuk_signon_mock(permissions=['dashboard'])

        with HTTMock(signon):
            resp = self.client.post(
                '/dashboard', json.dumps(data),
                content_type="application/json",
                HTTP_AUTHORIZATION='Bearer correct-token')

        assert_that(resp.status_code, equal_to(200))
        assert_that(Dashboard.objects.count(), equal_to(1))
