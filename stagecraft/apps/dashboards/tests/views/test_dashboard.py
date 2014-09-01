import json
from django.test import TestCase
from mock import patch
from hamcrest import assert_that, equal_to, is_, none
from stagecraft.apps.dashboards.tests.factories.factories import(
    DashboardFactory)
from stagecraft.apps.dashboards.views.dashboard import(
    recursively_fetch_dashboard)


class DashboardViewsTestCase(TestCase):

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
            '/public/dashboards', {'slug': 'my_first_slug'})
        assert_that(json.loads(resp.content), equal_to(spotlightify_response))
        assert_that(resp['Cache-Control'], equal_to('max-age=300'))

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
        slug = 'experimental/my_first_slug/another'
        returned_dashboard = recursively_fetch_dashboard(slug)
        assert_that(dashboard.id, equal_to(returned_dashboard.id))

    def test_recursively_fetch_dashboard_ignore_level_1_and_returns_none_after_2_levels(  # noqa
            self):
        DashboardFactory(slug='my_first_slug')
        slug = 'my_first_slug/some_url_fragment/another/another'
        returned_dashboard = recursively_fetch_dashboard(slug)
        assert_that(returned_dashboard, is_(none()))
