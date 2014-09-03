
import json

from django.test import TestCase
from hamcrest import (
    assert_that, equal_to, is_, none,
    has_entry, has_item,
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
