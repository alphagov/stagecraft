
import json

from django.test import TestCase
from hamcrest import (
    assert_that, equal_to, is_, none,
    has_entry, has_item, has_key, is_not
)

from ...models import ModuleType


class ModuleTypeViewsTestCase(TestCase):

    def test_root_type_only_get_post(self):
        delete_resp = self.client.delete(
            '/module-type',
            HTTP_AUTHORIZATION='Bearer development-oauth-access-token')
        put_resp = self.client.put(
            '/module-type',
            HTTP_AUTHORIZATION='Bearer development-oauth-access-token')

        assert_that(delete_resp.status_code, equal_to(405))
        assert_that(put_resp.status_code, equal_to(405))

    def test_list_types(self):
        ModuleType.objects.create(name="foo", schema={})
        ModuleType.objects.create(name="bar", schema={})

        resp = self.client.get('/module-type')
        resp_json = json.loads(resp.content)

        assert_that(len(resp_json), 2)
        assert_that(
            resp_json,
            has_item(has_entry('name', 'foo')),
        )
        assert_that(
            resp_json,
            has_item(has_entry('name', 'bar')),
        )

    def test_list_types_filter_by_name(self):
        ModuleType.objects.create(name="foo", schema={})
        ModuleType.objects.create(name="bar", schema={})

        resp = self.client.get('/module-type?name=foo')
        resp_json = json.loads(resp.content)

        assert_that(len(resp_json), 1)
        assert_that(
            resp_json,
            has_item(has_entry('name', 'foo')),
        )

    def test_list_types_filter_by_name_case_insensitive(self):
        ModuleType.objects.create(name="foo", schema={})
        ModuleType.objects.create(name="bar", schema={})

        resp = self.client.get('/module-type?name=fOo')
        resp_json = json.loads(resp.content)

        assert_that(len(resp_json), 1)
        assert_that(
            resp_json,
            has_item(has_entry('name', 'foo')),
        )

    def test_add_type(self):
        resp = self.client.post(
            '/module-type',
            data=json.dumps({
                'name': 'a-type',
                'schema': {'type': 'string'},
            }),
            HTTP_AUTHORIZATION='Bearer development-oauth-access-token',
            content_type='application/json')

        assert_that(resp.status_code, is_(equal_to(200)))

        resp_json = json.loads(resp.content)

        assert_that(resp_json, has_key('id'))
        assert_that(resp_json, has_entry('name', 'a-type'))
        assert_that(resp_json, has_entry('schema', {'type': 'string'}))

        stored_types = ModuleType.objects.get(id=resp_json['id'])
        assert_that(stored_types, is_not(None))

    def test_add_type_not_json(self):
        resp = self.client.post(
            '/module-type',
            data=json.dumps({
            }),
            HTTP_AUTHORIZATION='Bearer development-oauth-access-token',
            content_type='application/something-else')

        assert_that(resp.status_code, is_(equal_to(415)))

    def test_add_type_with_no_name(self):
        resp = self.client.post(
            '/module-type',
            data=json.dumps({
                'schema': {'type': 'string'},
            }),
            HTTP_AUTHORIZATION='Bearer development-oauth-access-token',
            content_type='application/json')

        assert_that(resp.status_code, is_(equal_to(400)))

    def test_add_type_with_no_schema(self):
        resp = self.client.post(
            '/module-type',
            data=json.dumps({
                'name': 'a-type',
            }),
            HTTP_AUTHORIZATION='Bearer development-oauth-access-token',
            content_type='application/json')

        assert_that(resp.status_code, is_(equal_to(400)))

    def test_add_type_with_an_invalid_schema(self):
        resp = self.client.post(
            '/module-type',
            data=json.dumps({
                'name': 'a-type',
                'schema': {'type': 'some wrong type'},
            }),
            HTTP_AUTHORIZATION='Bearer development-oauth-access-token',
            content_type='application/json')

        assert_that(resp.status_code, is_(equal_to(400)))

    def test_add_type_with_invalid_json(self):
        resp = self.client.post(
            '/module-type',
            data='not json',
            HTTP_AUTHORIZATION='Bearer development-oauth-access-token',
            content_type='application/json')

        assert_that(resp.status_code, is_(equal_to(400)))
