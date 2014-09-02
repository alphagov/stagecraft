from unittest import TestCase
from ..lib.spotlight_config_migration import spotlight_json, Dashboard
import os
from hamcrest import has_item, assert_that, has_entry
import requests
from mock import patch

FIXTURES_PATH = os.path.join(os.path.dirname(__file__), '../fixtures/')

class SpotlightJsonTestCase(TestCase):

    def test_empty_single_file(self):
        assert_that(
            self.load_spotlight_json('spotlight_json_empty'),
            has_item({})
        )

    def test_recursive(self):
        assert_that(
            self.load_spotlight_json('spotlight_json_recursive'),
            has_item(has_entry('test', 'blah'))
        )

    def load_spotlight_json(self, directory):
        return spotlight_json(
            os.path.join(
                FIXTURES_PATH,
                directory
            )
        )

class DashboardFromJsonTestCase(TestCase):

    def setUp(self):
        self.test_url = 'http://example.com'
        self.dashboard = Dashboard(self.test_url)

    @patch('requests.post')
    def test_dashboard_creates_sucessfully(
        self, post_mock
    ):
        dashboard_data = {"slug": "slug", "page-type": "dashboard"}
        self.dashboard.set_data(dashboard_data)
        self.dashboard.send()
        post_mock.assert_called_with(
            # @todo replace this endpoint!
            self.test_url + '/dashboard/',
            dashboard_data
        )

    @patch('requests.get')
    @patch('requests.post')
    def test_organisation_when_exists_creates_successfully(
        self, post_mock, get_mock
    ):
        dashboard_data = {
            "slug": "slug", "page-type": "dashboard", "organisation": "uid"
        }
        self.dashboard.set_data(dashboard_data)
        get_mock.return_value.status_code = 200
        self.dashboard.send()
        get_mock.assert_called_with(
            self.test_url + '/organisation/uid'
        )
        post_mock.assert_called_with(
            # @todo replace this endpoint!
            self.test_url + '/dashboard/',
            dashboard_data
        )
