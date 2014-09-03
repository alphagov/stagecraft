from unittest import TestCase
from ..lib.spotlight_config_migration import spotlight_json, Dashboard
import os
from hamcrest import has_item, assert_that, has_entry, is_not, has_key
import requests
from mock import patch, Mock

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
        self.dashboard.set_data(**dashboard_data)
        self.dashboard.send()
        post_mock.assert_called_with(
            # @todo replace this endpoint!
            self.test_url + '/dashboard/',
            dashboard_data
        )

    @patch('requests.get')
    @patch('requests.post')
    def test_department_when_exists_creates_successfully(
        self, post_mock, get_mock
    ):
        dashboard_data = {
            "slug": "slug",
            "page-type": "dashboard",
            "department": {"title": "test-department", "abbr": "TDD"}
        }
        self.dashboard.set_data(**dashboard_data)
        get_mock.return_value.status_code = 200
        self.dashboard.send()
        get_mock.assert_called_with(
            self.test_url + '/organisation/node',
            params={
                "name": dashboard_data['department']['title'],
                "abbreviation": dashboard_data['department']['abbr']
            }
        )
        dashboard_data.pop('department')
        post_mock.assert_called_with(
            # @todo replace this endpoint!
            self.test_url + '/dashboard/',
            dashboard_data
        )

    @patch('requests.get')
    @patch('requests.post')
    def test_department_when_not_exists_creates_successfully(
        self, post_mock, get_mock
    ):
        dashboard_data = {
            "slug": "slug",
            "page-type": "dashboard",
            "department": {"title": "test-department", "abbr": "TDD"}
        }
        self.dashboard.set_data(**dashboard_data)
        get_mock.return_value.status_code = 404
        get_mock.return_value.json.return_value = {"type_id": "type_uid"}
        post_mock.return_value.status_code = 200
        self.dashboard.send()
        post_mock.assert_any_call(
            # @todo replace this endpoint!
            self.test_url + '/organisation/node',
            {"name": "test-department", "abbreviation": "TDD",
             "type_id": "type_uid"}
        )
        dashboard_data.pop('department')
        post_mock.assert_any_call(
            # @todo replace this endpoint!
            self.test_url + '/dashboard/',
            dashboard_data
        )

    @patch('requests.get')
    @patch('requests.post')
    def test_agency_when_not_exists_but_department_exists_creates_successfully(
        self, post_mock, get_mock
    ):
        dashboard_data = {
            "slug": "slug",
            "page-type": "dashboard",
            "department": {"title": "test-department", "abbr": "TDD"},
            "agency": {"title": "test-agency", "abbr": "TAD"}
        }
        self.dashboard.set_data(**dashboard_data)

        def get_side_effect(url, params=None):
            mock = Mock()
            if params["name"] == 'test-department':
                mock.status_code = 200
                mock.json.return_value = {"type_id": "department-type-id"}
            else:
                mock.status_code = 404
                mock.json.return_value = {"type_id": "agency-type-id"}
            return mock

        get_mock.side_effect = get_side_effect
        post_mock.return_value.status_code = 200
        self.dashboard.send()
        post_mock.assert_any_call(
            # @todo replace this endpoint!
            self.test_url + '/organisation/node',
            {"name": "test-agency", "abbreviation": "TAD",
             "type_id": "agency-type-id"}
        )
        dashboard_data.pop('department')
        dashboard_data.pop('agency')
        post_mock.assert_any_call(
            # @todo replace this endpoint!
            self.test_url + '/dashboard/',
            dashboard_data
        )
        assert_that(
            post_mock.call_args_list,
            is_not(has_item(has_key('department'))))
        # assert_that(post_mock.call_args_list, not(
