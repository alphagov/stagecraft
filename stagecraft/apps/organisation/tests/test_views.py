import json

from django.conf import settings
from django.test import TestCase
from hamcrest import (
    assert_that, equal_to, has_entry,
    has_item, has_key
)
from httmock import HTTMock

from .factories import NodeFactory, NodeTypeFactory

from stagecraft.libs.authorization.tests.test_http import govuk_signon_mock


class NodeViewsTestCase(TestCase):

    def setUp(self):
        thing = NodeTypeFactory(
            id='ea72e3e1-13b8-4bf6-9ffb-7cd0d2f168d4',
            name='Thing',
        )
        department = NodeTypeFactory(
            id='f9510fef-a879-4cf8-bcfb-9e0871579f5a',
            name='Department',
        )

        cheese = NodeFactory(
            id='f59bddcc-4494-46f8-a2c9-884030fa3087',
            name='Cheese',
            abbreviation=None,
            typeOf=department,
        )
        brie = NodeFactory(
            id='edc9aa07-f45f-4d93-9f9c-d9d760f08019',
            name='Brie',
            abbreviation='BR',
            typeOf=thing,
        )
        brie.parents.add(cheese)

    def test_root_view_only_get_post(self):
        delete_resp = self.client.delete(
            '/organisation/node',
            HTTP_AUTHORIZATION='Bearer development-oauth-access-token')
        put_resp = self.client.put(
            '/organisation/node',
            HTTP_AUTHORIZATION='Bearer development-oauth-access-token')

        assert_that(delete_resp.status_code, equal_to(405))
        assert_that(put_resp.status_code, equal_to(405))

    def test_list_nodes(self):
        resp = self.client.get(
            '/organisation/node',
            HTTP_AUTHORIZATION='Bearer development-oauth-access-token'
        )
        resp_json = json.loads(resp.content)

        assert_that(len(resp_json), equal_to(2))
        assert_that(
            resp_json,
            has_item(has_entry('id', 'edc9aa07-f45f-4d93-9f9c-d9d760f08019'))
        )
        assert_that(
            resp_json,
            has_item(has_entry('id', 'f59bddcc-4494-46f8-a2c9-884030fa3087'))
        )

    def test_list_nodes_filter_by_name(self):
        resp = self.client.get(
            '/organisation/node?name=Brie',
            HTTP_AUTHORIZATION='Bearer development-oauth-access-token'
        )
        resp_json = json.loads(resp.content)

        assert_that(len(resp_json), equal_to(1))
        assert_that(
            resp_json,
            has_item(has_entry('id', 'edc9aa07-f45f-4d93-9f9c-d9d760f08019'))
        )

    def test_list_nodes_filter_by_name(self):
        resp = self.client.get(
            '/organisation/node?abbreviation=BR',
            HTTP_AUTHORIZATION='Bearer development-oauth-access-token'
        )
        resp_json = json.loads(resp.content)

        assert_that(len(resp_json), equal_to(1))
        assert_that(
            resp_json,
            has_item(has_entry('id', 'edc9aa07-f45f-4d93-9f9c-d9d760f08019'))
        )

    def test_list_nodes_filter_by_both(self):
        resp = self.client.get(
            '/organisation/node?name=Brie&&abbreviation=BR',
            HTTP_AUTHORIZATION='Bearer development-oauth-access-token'
        )
        resp_json = json.loads(resp.content)

        assert_that(len(resp_json), equal_to(1))
        assert_that(
            resp_json,
            has_item(has_entry('id', 'edc9aa07-f45f-4d93-9f9c-d9d760f08019'))
        )

    def test_list_nodes_filter_by_both_is_and(self):
        resp = self.client.get(
            '/organisation/node?name=Cheese&&abbreviation=BR',
            HTTP_AUTHORIZATION='Bearer development-oauth-access-token'
        )
        resp_json = json.loads(resp.content)

        assert_that(len(resp_json), equal_to(0))

    def test_list_nodes_filter_by_is_case_insensitive(self):
        resp = self.client.get(
            '/organisation/node?name=brie&&abbreviation=br',
            HTTP_AUTHORIZATION='Bearer development-oauth-access-token'
        )
        resp_json = json.loads(resp.content)

        assert_that(len(resp_json), equal_to(1))
        assert_that(
            resp_json,
            has_item(has_entry('id', 'edc9aa07-f45f-4d93-9f9c-d9d760f08019'))
        )

    def test_get_nodes_ancestors(self):
        node_uuid = 'edc9aa07-f45f-4d93-9f9c-d9d760f08019'
        resp = self.client.get(
            '/organisation/node/{}/ancestors'.format(node_uuid),
            HTTP_AUTHORIZATION='Bearer development-oauth-access-token'
        )
        resp_json = json.loads(resp.content)

        assert_that(len(resp_json), equal_to(1))
        assert_that(
            resp_json[0],
            has_entry('id', 'f59bddcc-4494-46f8-a2c9-884030fa3087')
        )

    def test_get_nodes_ancestors_with_self(self):
        node_uuid = 'edc9aa07-f45f-4d93-9f9c-d9d760f08019'
        resp = self.client.get(
            '/organisation/node/{}/ancestors?self=true'.format(node_uuid),
            HTTP_AUTHORIZATION='Bearer development-oauth-access-token'
        )
        resp_json = json.loads(resp.content)

        assert_that(len(resp_json), equal_to(2))
        assert_that(
            resp_json[0],
            has_entry('id', 'f59bddcc-4494-46f8-a2c9-884030fa3087')
        )
        assert_that(
            resp_json[1],
            has_entry('id', 'edc9aa07-f45f-4d93-9f9c-d9d760f08019')
        )

    def test_add_node(self):
        resp = self.client.post(
            '/organisation/node',
            data=json.dumps({
                'name': 'Edam',
                'abbreviation': 'ED',
                'slug': 'wha',
                'type_id': 'ea72e3e1-13b8-4bf6-9ffb-7cd0d2f168d4',
                'parent_id': 'f59bddcc-4494-46f8-a2c9-884030fa3087'
            }),
            HTTP_AUTHORIZATION='Bearer development-oauth-access-token',
            content_type='application/json')

        assert_that(resp.status_code, equal_to(200))

        resp_json = json.loads(resp.content)

        assert_that(resp_json, has_key('id'))
        assert_that(resp_json['name'], equal_to('Edam'))
        assert_that(resp_json['abbreviation'], equal_to('ED'))
        assert_that(resp_json['parent']['name'], equal_to('Cheese'))
        assert_that(resp_json['type']['name'], equal_to('Thing'))

    def test_add_node_bad_json(self):
        resp = self.client.post(
            '/organisation/node',
            data='{"agfagd',
            HTTP_AUTHORIZATION='Bearer development-oauth-access-token',
            content_type='application/json')

        assert_that(resp.status_code, equal_to(400))

    def test_add_node_missing_name(self):
        resp = self.client.post(
            '/organisation/node',
            data=json.dumps({
                'abbreviation': 'ED',
                'type_id': 'ea72e3e1-13b8-4bf6-9ffb-7cd0d2f168d4',
                'parent_id': 'f59bddcc-4494-46f8-a2c9-884030fa3087'
            }),
            HTTP_AUTHORIZATION='Bearer development-oauth-access-token',
            content_type='application/json')

        assert_that(resp.status_code, equal_to(400))

    def test_add_node_missing_type(self):
        resp = self.client.post(
            '/organisation/node',
            data=json.dumps({
                'name': 'Edam',
                'abbreviation': 'ED',
                'parent_id': 'f59bddcc-4494-46f8-a2c9-884030fa3087'
            }),
            HTTP_AUTHORIZATION='Bearer development-oauth-access-token',
            content_type='application/json')

        assert_that(resp.status_code, equal_to(400))

    def test_add_node_non_existant_type(self):
        resp = self.client.post(
            '/organisation/node',
            data=json.dumps({
                'name': 'Edam',
                'abbreviation': 'ED',
                'type_id': '00000000-0000-0000-0000-000000000000',
                'parent_id': 'f59bddcc-4494-46f8-a2c9-884030fa3087'
            }),
            HTTP_AUTHORIZATION='Bearer development-oauth-access-token',
            content_type='application/json')

        assert_that(resp.status_code, equal_to(400))

    def test_add_node_non_existant_parent(self):
        resp = self.client.post(
            '/organisation/node',
            data=json.dumps({
                'name': 'Edam',
                'abbreviation': 'ED',
                'type_id': 'ea72e3e1-13b8-4bf6-9ffb-7cd0d2f168d4',
                'parent_id': '00000000-0000-0000-0000-000000000000'
            }),
            HTTP_AUTHORIZATION='Bearer development-oauth-access-token',
            content_type='application/json')

        assert_that(resp.status_code, equal_to(400))

    def test_add_node_type_id_not_uuid(self):
        resp = self.client.post(
            '/organisation/node',
            data=json.dumps({
                'name': 'Edam',
                'abbreviation': 'ED',
                'type_id': 'foo',
                'parent_id': 'f59bddcc-4494-46f8-a2c9-884030fa3087'
            }),
            HTTP_AUTHORIZATION='Bearer development-oauth-access-token',
            content_type='application/json')

        assert_that(resp.status_code, equal_to(400))

    def test_add_node_parent_id_not_uuid(self):
        resp = self.client.post(
            '/organisation/node',
            data=json.dumps({
                'name': 'Edam',
                'abbreviation': 'ED',
                'type_id': 'ea72e3e1-13b8-4bf6-9ffb-7cd0d2f168d4',
                'parent_id': 'foo'
            }),
            HTTP_AUTHORIZATION='Bearer development-oauth-access-token',
            content_type='application/json')

        assert_that(resp.status_code, equal_to(400))

    def test_add_node_with_no_parent(self):
        resp = self.client.post(
            '/organisation/node',
            data=json.dumps({
                'name': 'Edam',
                'slug': 'abc',
                'abbreviation': 'ED',
                'type_id': 'ea72e3e1-13b8-4bf6-9ffb-7cd0d2f168d4'
            }),
            HTTP_AUTHORIZATION='Bearer development-oauth-access-token',
            content_type='application/json')

        assert_that(resp.status_code, equal_to(200))

        resp_json = json.loads(resp.content)

        assert_that(resp_json, has_entry('parent', None))

    def test_add_node_with_no_abbr(self):
        resp = self.client.post(
            '/organisation/node',
            data=json.dumps({
                'name': 'Edam',
                'slug': 'whoo',
                'type_id': 'ea72e3e1-13b8-4bf6-9ffb-7cd0d2f168d4'
            }),
            HTTP_AUTHORIZATION='Bearer development-oauth-access-token',
            content_type='application/json')

        assert_that(resp.status_code, equal_to(200))

        resp_json = json.loads(resp.content)
        assert_that(resp_json, has_entry('abbreviation', 'Edam'))

    def tearDown(self):
        settings.USE_DEVELOPMENT_USERS = True

    def test_add_node_without_permission(self):
        settings.USE_DEVELOPMENT_USERS = False
        signon = govuk_signon_mock(
            permissions=['signin'],
            email='some.user@digital.cabinet-office.gov.uk')

        with HTTMock(signon):
            resp = self.client.post(
                '/organisation/node',
                data=json.dumps({
                    'name': 'Edam',
                    'type_id': 'ea72e3e1-13b8-4bf6-9ffb-7cd0d2f168d4'
                }),
                HTTP_AUTHORIZATION='Bearer correct-token',
                content_type='application/json')

            assert_that(resp.status_code, equal_to(403))


class NodeTypeViewsTestCase(TestCase):

    def setUp(self):
        thing = NodeTypeFactory(
            id='ea72e3e1-13b8-4bf6-9ffb-7cd0d2f168d4',
            name='Thing',
        )
        department = NodeTypeFactory(
            id='f9510fef-a879-4cf8-bcfb-9e0871579f5a',
            name='Department',
        )

        cheese = NodeFactory(
            id='f59bddcc-4494-46f8-a2c9-884030fa3087',
            name='Cheese',
            abbreviation=None,
            typeOf=department,
        )
        brie = NodeFactory(
            id='edc9aa07-f45f-4d93-9f9c-d9d760f08019',
            name='Brie',
            abbreviation='BR',
            typeOf=thing,
        )
        brie.parents.add(cheese)

    def test_root_view_only_get_post(self):
        delete_resp = self.client.delete(
            '/organisation/type',
            HTTP_AUTHORIZATION='Bearer development-oauth-access-token')
        put_resp = self.client.put(
            '/organisation/type',
            HTTP_AUTHORIZATION='Bearer development-oauth-access-token')

        assert_that(delete_resp.status_code, equal_to(405))
        assert_that(put_resp.status_code, equal_to(405))

    def test_list_types(self):
        resp = self.client.get(
            '/organisation/type',
            HTTP_AUTHORIZATION='Bearer development-oauth-access-token'
        )
        resp_json = json.loads(resp.content)

        assert_that(len(resp_json), equal_to(2))
        assert_that(
            resp_json,
            has_item(has_entry('id', 'ea72e3e1-13b8-4bf6-9ffb-7cd0d2f168d4'))
        )
        assert_that(
            resp_json,
            has_item(has_entry('id', 'f9510fef-a879-4cf8-bcfb-9e0871579f5a'))
        )

    def test_list_types_filter_name(self):
        resp = self.client.get(
            '/organisation/type?name=Thing',
            HTTP_AUTHORIZATION='Bearer development-oauth-access-token'
        )
        resp_json = json.loads(resp.content)

        assert_that(len(resp_json), equal_to(1))
        assert_that(
            resp_json,
            has_item(has_entry('id', 'ea72e3e1-13b8-4bf6-9ffb-7cd0d2f168d4'))
        )

    def test_list_types_filter_name_should_be_case_insensitive(self):
        resp = self.client.get(
            '/organisation/type?name=thing',
            HTTP_AUTHORIZATION='Bearer development-oauth-access-token'
        )
        resp_json = json.loads(resp.content)

        assert_that(len(resp_json), equal_to(1))
        assert_that(
            resp_json,
            has_item(has_entry('id', 'ea72e3e1-13b8-4bf6-9ffb-7cd0d2f168d4'))
        )

    def test_add_type(self):
        resp = self.client.post(
            '/organisation/type',
            data=json.dumps({
                'name': 'Agency'
            }),
            HTTP_AUTHORIZATION='Bearer development-oauth-access-token',
            content_type='application/json')

        assert_that(resp.status_code, equal_to(200))

        resp_json = json.loads(resp.content)
        assert_that(resp_json, has_key('id'))
        assert_that(resp_json, has_entry('name', 'Agency'))

    def test_add_type_bad_json(self):
        resp = self.client.post(
            '/organisation/type',
            data='{"foo":"b',
            HTTP_AUTHORIZATION='Bearer development-oauth-access-token',
            content_type='application/json')

        assert_that(resp.status_code, equal_to(400))

    def test_add_type_no_name(self):
        resp = self.client.post(
            '/organisation/type',
            data=json.dumps({
            }),
            HTTP_AUTHORIZATION='Bearer development-oauth-access-token',
            content_type='application/json')

        assert_that(resp.status_code, equal_to(400))
