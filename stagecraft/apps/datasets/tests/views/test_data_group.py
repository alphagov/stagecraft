from django.test import TestCase
import json
from nose.tools import assert_equal
from stagecraft.apps.datasets.models import DataGroup
from stagecraft.apps.datasets.tests.factories import DataGroupFactory


class DataGroupsViewsTestCase(TestCase):

    def test_post(self):
        data_group = {
            'name': 'carers-allowance'
        }
        resp = self.client.post(
            '/data-groups',
            data=json.dumps(data_group),
            HTTP_AUTHORIZATION='Bearer development-oauth-access-token',
            content_type='application/json')
        assert_equal(resp.status_code, 200)

        resp = self.client.post(
            '/data-groups',
            data=json.dumps(data_group),
            HTTP_AUTHORIZATION='Bearer development-oauth-access-token',
            content_type='application/json')
        assert_equal(resp.status_code, 400)

        assert_equal(DataGroup.objects.get(name=data_group["name"]).name,
                     'carers-allowance')

    def test_post_from_unauthorised_client_fails(self):
        data_group = {
            'name': 'carers-allowance'
        }
        resp = self.client.post(
            '/data-groups',
            data=json.dumps(data_group),
            content_type='application/json')

        assert_equal(resp.status_code, 403)

    def test_get(self):
        data_group = DataGroupFactory()
        resp = self.client.get(
            '/data-groups?name={}'.format(data_group.name),
            HTTP_AUTHORIZATION='Bearer development-oauth-access-token')

        assert_equal(resp.status_code, 200)

    def test_get_from_unauthorised_client_fails(self):
        data_group = DataGroupFactory()
        resp = self.client.get(
            '/data-groups?name={}'.format(data_group.name))

        assert_equal(resp.status_code, 403)

    def test_get_correct_datagroup(self):
        data_group_1 = DataGroupFactory()
        data_group_2 = DataGroupFactory()

        resp = self.client.get(
            '/data-groups?name={}'.format(data_group_2.name),
            HTTP_AUTHORIZATION='Bearer development-oauth-access-token'
        )

        resp_json = json.loads(resp.content)

        expected_response = {
            "name": data_group_2.name
        }

        assert_equal(resp_json[0], expected_response)

    def test_get_nonexistant_datagroup(self):
        resp = self.client.get(
            '/data-groups?data-group=nonexistant-group',
            HTTP_AUTHORIZATION='Bearer development-oauth-access-token')
        assert_equal(resp.status_code, 200)
        expected = []
        assert_equal(json.loads(resp.content.decode('utf-8')), expected)
