import json
from django.test import TestCase
from mock import patch
from hamcrest import assert_that, equal_to
from stagecraft.apps.dashboards.tests.factories.factories import(
    DashboardFactory)


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

    # test gets the correct dashboard or sub module...

    # services list is dashboards with no slugs

    # test for redirect from /
