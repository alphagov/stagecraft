
import json

from django.test import TestCase
from hamcrest import (
    assert_that, equal_to, is_,
    has_entry, has_item, has_key, is_not
)

from stagecraft.apps.datasets.models import DataGroup, DataType, DataSet
from stagecraft.libs.backdrop_client import disable_backdrop_connection
from ...models import Dashboard, Module, ModuleType


class ModuleViewsTestCase(TestCase):

    @classmethod
    def setUpClass(cls):
        cls.data_group = DataGroup.objects.create(name='group')
        cls.data_type = DataType.objects.create(name='type')

        cls.data_set = DataSet.objects.create(
            data_group=cls.data_group,
            data_type=cls.data_type,
        )

        cls.module_type = ModuleType.objects.create(
            name='a-type',
            schema={
                'type': 'object',
                'properties': {
                    'thing': {
                        'type': 'string',
                    },
                },
                'required': ['thing'],
            }
        )

        cls.dashboard = Dashboard.objects.create(
            published=True,
            title='A service',
            slug='some/slug',
        )

    @classmethod
    @disable_backdrop_connection
    def tearDownClass(cls):
        cls.data_set.delete()
        cls.data_type.delete()
        cls.data_group.delete()

        cls.module_type.delete()
        cls.dashboard.delete()

    def test_modules_on_dashboard_only_get_post(self):
        delete_resp = self.client.delete(
            '/dashboard/{}/module'.format(str(self.dashboard.id)),
            HTTP_AUTHORIZATION='Bearer development-oauth-access-token')
        put_resp = self.client.put(
            '/dashboard/{}/module'.format(str(self.dashboard.id)),
            HTTP_AUTHORIZATION='Bearer development-oauth-access-token')

        assert_that(delete_resp.status_code, equal_to(405))
        assert_that(put_resp.status_code, equal_to(405))

    def test_list_modules_on_dashboard(self):
        dashboard2 = Dashboard.objects.create(
            published=True,
            title='A service',
            slug='some/slug2',
        )
        module1 = Module.objects.create(
            type=self.module_type,
            dashboard=self.dashboard,
            slug='module-1',
            options={},
            order=1)
        module2 = Module.objects.create(
            type=self.module_type,
            dashboard=self.dashboard,
            slug='module-2',
            options={},
            order=2)
        module3 = Module.objects.create(
            type=self.module_type,
            dashboard=dashboard2,
            slug='module-3',
            options={},
            order=1)

        resp = self.client.get(
            '/dashboard/{}/module'.format(self.dashboard.id))

        assert_that(resp.status_code, is_(equal_to(200)))

        resp_json = json.loads(resp.content)

        assert_that(len(resp_json), is_(equal_to(2)))
        assert_that(
            resp_json,
            has_item(has_entry('id', str(module1.id))))
        assert_that(
            resp_json,
            has_item(has_entry('id', str(module2.id))))
        assert_that(
            resp_json,
            is_not(has_item(has_entry('id', str(module3.id)))))

        module1.delete()
        module2.delete()
        module3.delete()
        dashboard2.delete()

    def test_add_a_module_to_a_dashboard(self):
        resp = self.client.post(
            '/dashboard/{}/module'.format(self.dashboard.id),
            data=json.dumps({
                'slug': 'a-module',
                'type_id': str(self.module_type.id),
                'title': 'Some module',
                'description': 'Some text about the module',
                'info': ['foo'],
                'options': {
                    'thing': 'a value',
                },
                'order': 1,
            }),
            HTTP_AUTHORIZATION='Bearer development-oauth-access-token',
            content_type='application/json')

        assert_that(resp.status_code, is_(equal_to(200)))

        resp_json = json.loads(resp.content)

        assert_that(resp_json, has_key('id'))
        assert_that(resp_json, has_entry('slug', 'a-module'))
        assert_that(resp_json, has_entry('options', {'thing': 'a value'}))

        stored_module = Module.objects.get(id=resp_json['id'])
        assert_that(stored_module, is_not(None))

    def test_add_a_module_with_no_type(self):
        resp = self.client.post(
            '/dashboard/{}/module'.format(self.dashboard.id),
            data=json.dumps({
                'slug': 'a-module',
                'title': 'Some module',
                'description': 'Some text about the module',
                'info': ['foo'],
                'options': {
                    'thing': 'a value',
                },
            }),
            HTTP_AUTHORIZATION='Bearer development-oauth-access-token',
            content_type='application/json')

        assert_that(resp.status_code, is_(equal_to(400)))

    def test_add_a_module_to_a_non_existant_dashboard(self):
        resp = self.client.post(
            '/dashboard/391213f0-336f-11e4-8c21-0800200c9a66/module',
            data=json.dumps({
                'slug': 'a-module',
                'type_id': str(self.module_type.id),
                'title': 'Some module',
                'description': 'Some text about the module',
                'info': ['foo'],
                'options': {
                    'thing': 'a value',
                },
            }),
            HTTP_AUTHORIZATION='Bearer development-oauth-access-token',
            content_type='application/json')

        assert_that(resp.status_code, is_(equal_to(404)))

    def test_add_a_module_with_a_data_set_that_doesnt_exist(self):
        resp = self.client.post(
            '/dashboard/{}/module'.format(self.dashboard.id),
            data=json.dumps({
                'slug': 'a-module',
                'type_id': str(self.module_type.id),
                'data_group': 'bad-group',
                'data_type': 'bad-type',
                'title': 'Some module',
                'description': 'Some text about the module',
                'info': ['foo'],
                'options': {
                    'thing': 'a value',
                },
            }),
            HTTP_AUTHORIZATION='Bearer development-oauth-access-token',
            content_type='application/json')

        assert_that(resp.status_code, is_(equal_to(400)))

    def test_add_a_module_with_a_data_set(self):
        resp = self.client.post(
            '/dashboard/{}/module'.format(self.dashboard.id),
            data=json.dumps({
                'slug': 'a-module',
                'type_id': str(self.module_type.id),
                'data_type': str(self.data_type.name),
                'data_group': str(self.data_group.name),
                'title': 'Some module',
                'description': 'Some text about the module',
                'info': ['foo'],
                'options': {
                    'thing': 'a value',
                },
                'order': 1,
            }),
            HTTP_AUTHORIZATION='Bearer development-oauth-access-token',
            content_type='application/json')

        assert_that(resp.status_code, is_(equal_to(200)))

    def test_add_a_module_with_a_data_set_and_a_query(self):
        resp = self.client.post(
            '/dashboard/{}/module'.format(self.dashboard.id),
            data=json.dumps({
                'slug': 'a-module',
                'type_id': str(self.module_type.id),
                'data_type': str(self.data_type.name),
                'data_group': str(self.data_group.name),
                'title': 'Some module',
                'description': 'Some text about the module',
                'info': ['foo'],
                'options': {
                    'thing': 'a value',
                },
                'query_parameters': {
                    'sort_by': 'thing:desc',
                },
                'order': 1,
            }),
            HTTP_AUTHORIZATION='Bearer development-oauth-access-token',
            content_type='application/json')

        assert_that(resp.status_code, is_(equal_to(200)))

        # do some parsing and that

    def test_add_a_module_with_a_query_but_no_data_set(self):
        resp = self.client.post(
            '/dashboard/{}/module'.format(self.dashboard.id),
            data=json.dumps({
                'slug': 'a-module',
                'type_id': str(self.module_type.id),
                'title': 'Some module',
                'description': 'Some text about the module',
                'info': ['foo'],
                'options': {
                    'thing': 'a value',
                },
                'query_parameters': {
                    'collect': ['thing:invalid-collect-thing']
                },
            }),
            HTTP_AUTHORIZATION='Bearer development-oauth-access-token',
            content_type='application/json')

        assert_that(resp.status_code, is_(equal_to(400)))

    def test_add_a_module_to_a_dashboard_that_options_violates_schema(self):
        resp = self.client.post(
            '/dashboard/{}/module'.format(self.dashboard.id),
            data=json.dumps({
                'slug': 'a-module',
                'type_id': str(self.module_type.id),
                'title': 'Some module',
                'description': 'Some text about the module',
                'info': ['foo'],
                'options': {
                },
            }),
            HTTP_AUTHORIZATION='Bearer development-oauth-access-token',
            content_type='application/json')

        assert_that(resp.status_code, is_(equal_to(400)))

    def test_add_a_module_to_a_dashboard_queryparams_violates_schema(self):
        resp = self.client.post(
            '/dashboard/{}/module'.format(self.dashboard.id),
            data=json.dumps({
                'slug': 'a-module',
                'type_id': str(self.module_type.id),
                'data_type': str(self.data_type.name),
                'data_group': str(self.data_group.name),
                'title': 'Some module',
                'description': 'Some text about the module',
                'info': ['foo'],
                'options': {
                    'thing': 'a value',
                },
                'query_parameters': {
                    'collect': ['thing:invalid-collect-thing']
                },
            }),
            HTTP_AUTHORIZATION='Bearer development-oauth-access-token',
            content_type='application/json')

        assert_that(resp.status_code, is_(equal_to(400)))

    def test_add_a_module_to_a_dashboard_bad_json(self):
        resp = self.client.post(
            '/dashboard/{}/module'.format(self.dashboard.id),
            data='not json',
            HTTP_AUTHORIZATION='Bearer development-oauth-access-token',
            content_type='application/json')

        assert_that(resp.status_code, is_(equal_to(400)))

    def test_add_a_module_fails_with_bad_content_type(self):
        resp = self.client.post(
            '/dashboard/{}/module'.format(self.dashboard.id),
            data=json.dumps({
                'slug': 'a-module',
                'type_id': str(self.module_type.id),
                'title': 'Some module',
                'description': 'Some text about the module',
                'info': ['foo'],
                'options': {
                    'thing': 'a value',
                },
            }),
            HTTP_AUTHORIZATION='Bearer development-oauth-access-token',
            content_type='application/not-a-type')

        assert_that(resp.status_code, is_(equal_to(415)))


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
