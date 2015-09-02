import json
from unittest import TestCase

from hamcrest import (
    assert_that, is_, calling, raises, is_not,
    instance_of, starts_with, has_key, has_entry,
    contains, equal_to, contains_inanyorder)
from django.http import HttpRequest, HttpResponse
from jsonschema import FormatError

from stagecraft.apps.organisation.models import Node, NodeType
from stagecraft.apps.collectors.models import Collector
from stagecraft.apps.collectors.tests.factories import(
    CollectorFactory, CollectorTypeFactory)
from stagecraft.apps.organisation.tests.factories import (
    NodeFactory, NodeTypeFactory
)
from ..resource import (
    FORMAT_CHECKER, ResourceView, resource_re_string,
    UUID_RE_STRING)
from stagecraft.libs.views.utils import create_http_error

from django.conf import settings
from httmock import HTTMock
from stagecraft.apps.datasets.models import OAuthUser
from stagecraft.libs.authorization.tests.test_http import(
    govuk_signon_mock)


class FormatCheckerTestCase(TestCase):

    def test_uuid_check(self):
        assert_that(
            calling(FORMAT_CHECKER.check).with_args('foo', 'uuid'),
            raises(FormatError))
        assert_that(
            calling(FORMAT_CHECKER.check).with_args(123, 'uuid'),
            raises(FormatError))
        assert_that(
            calling(FORMAT_CHECKER.check).with_args({}, 'uuid'),
            raises(FormatError))
        assert_that(
            calling(FORMAT_CHECKER.check).with_args([], 'uuid'),
            raises(FormatError))
        assert_that(
            calling(FORMAT_CHECKER.check).with_args(
                'fc1457d3-d4fe-41a5-8717-b412bee388e4', 'uuid'),
            is_not(raises(FormatError)))


def patched_validate(self):
    if self.name == 'save-and-fail-validation':
        return 'failed validation'
    else:
        return None


Node.validate = patched_validate


class TestResourceView(ResourceView):

    model = Node
    list_filters = {
        'name': 'name__iexact',
    }
    schema = {
        "$schema": "http://json-schema.org/schema#",
        "type": "object",
        "properties": {
            "type_id": {
                "type": "string",
                "format": "uuid",
            },
            "name": {"type": "string"},
            "slug": {"type": "string"},
            "abbreviation": {"type": "string"},
        },
        "required": ["type_id", "name"],
        "additionalProperties": False,
    }

    was_saved = False

    def update_relationships(self, model, model_json, request, parent):
        self.was_saved = model.pk is not None

    def update_model(self, model, model_json, request, parent):
        try:
            node_type = NodeType.objects.get(id=model_json['type_id'])
        except NodeType.DoesNotExist:
            return create_http_error(400, 'no NodeType found', request)

        model.name = model_json['name']
        model.slug = model_json.get('slug', None)
        model.abbreviation = model_json.get('abbreviation', None)
        model.typeOf = node_type

        if model_json['name'] == 'save-and-fail-validation':
            model.save()

    @staticmethod
    def serialize_for_list(model):
        return {
            'id': str(model.id),
            'name': model.name,
            'in_list': True,
        }

    @staticmethod
    def serialize(model):
        return {
            'id': str(model.id),
            'name': model.name,
        }


# To test a class which does not allow anon users to get
class TestResourceViewCollector(TestResourceView):
    model = Collector

    @staticmethod
    def serialize(model):
        return {
            'id': str(model.id),
            'slug': model.slug,
            'name': model.name,
            'query': model.query,
            'options': model.options,
            'entry_point': model.type.entry_point,
            'type': {
                'id': str(model.type.id),
                'slug': model.type.slug,
                'name': model.type.name
            },
            'data_source': {
                'id': str(model.data_source.id),
                'slug': model.data_source.slug,
                'name': model.data_source.name
            },
            'data_set': {
                'data_type': model.data_set.data_type.name,
                'data_group': model.data_set.data_group.name,
                'bearer_token': model.data_set.bearer_token
            },
            'provider': {
                'id': str(model.type.provider.id),
                'slug': model.type.provider.slug,
                'name': model.type.provider.name
            }
        }


class TestResourceViewChild(TestResourceView):

    def update_relationships(self, model, model_json, request, parent):
        if parent:
            model.parents.add(parent)

    @staticmethod
    def serialize_for_list(model):
        return {
            'id': str(model.id),
            'name': model.name,
            "foo": "bar"
        }

    @staticmethod
    def serialize(model):
        return {
            'id': str(model.id),
            'name': model.name,
            "foo": "bar"
        }


TestResourceView.sub_resources = {
    'child': TestResourceViewChild(),
}


class TestResourceViewMultipleIDs(ResourceView):

    model = Node
    id_fields = {
        'id': '[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}',
        'slug': '[\w-]+',
    }

    @staticmethod
    def serialize(model):
        return {
            'id': str(model.id),
            'name': model.name,
        }


class ResourceViewTestCase(TestCase):

    @classmethod
    def setUpClass(cls):
        cls.collector_type1 = CollectorTypeFactory(name="a_collector_type1")
        cls.collector1 = CollectorFactory(type=cls.collector_type1)
        cls.collector_type2 = CollectorTypeFactory(name="a_collector_type2")
        cls.collector2 = CollectorFactory(type=cls.collector_type2)

    def tearDown(self):
        Node.objects.all().delete()
        OAuthUser.objects.all().delete()
        settings.USE_DEVELOPMENT_USERS = True

    def get(self, args={}, query={}, cls=TestResourceView, user=None):
        view = cls()

        request = HttpRequest()
        request.method = 'GET'
        for (k, v) in query.items():
            request.GET[k] = v

        response = view.get(request, **args)

        assert_that(response, instance_of(HttpResponse))

        try:
            json_response = json.loads(response.content)
        except ValueError:
            json_response = None

        return response.status_code, json_response

    def _do(self, action, body, content_type, args):
        view = TestResourceView()

        request = HttpRequest()
        request.method = action
        request.META['CONTENT_TYPE'] = content_type
        request.META['HTTP_AUTHORIZATION'] = \
            'Bearer development-oauth-access-token'
        request._body = body

        if action == 'POST':
            response = view.post(request, **args)
        elif action == 'PUT':
            response = view.put(request, **args)
        elif action == 'DELETE':
            response = view.delete(request, **args)
        else:
            raise Exception('Invalid action {}'.format(action))

        assert_that(response, instance_of(HttpResponse))

        try:
            json_response = json.loads(response.content)
        except ValueError:
            json_response = None

        return response.status_code, json_response

    def post(self, body='', content_type='application/json', args={}):
        return self._do('POST', body, content_type, args)

    def put(self, body='', content_type='application/json', args={}):
        return self._do('PUT', body, content_type, args)

    def delete(self, body='', content_type='application/json', args={}):
        return self._do('DELETE', body, content_type, args)

    def test_user_filtering_only_with_user_set(self):
        node = NodeFactory()

        status_code, json_response = self.get(args={
            'id': str(node.id),
        }, user={
            'permissions': [
                'signin',
            ],
        })

        assert_that(status_code, is_(200))
        assert_that(json_response['name'], is_(node.name))

    def test_list(self):
        NodeFactory(name='foo-node-1')
        NodeFactory(name='foo-node-2')

        status_code, json_response = self.get()

        assert_that(status_code, is_(200))
        assert_that(len(json_response), is_(2))
        assert_that(json_response[0]['name'], starts_with('foo-node'))

    def test_list_serializes_with_diff_func(self):
        NodeFactory(name='foo-node-1')
        NodeFactory(name='foo-node-2')

        status_code, json_response = self.get()

        assert_that(status_code, is_(200))
        assert_that(json_response[0]['in_list'], is_(True))

    def test_list_serializes_with_diff_func_allows_ordering(self):
        NodeFactory(name='foo-node-1', slug='b')
        NodeFactory(name='foo-node-2', slug='a')

        TestResourceView.order_by = 'name'
        status_code, json_response = self.get()

        assert_that(status_code, is_(200))
        assert_that(json_response[0]['name'], is_('foo-node-1'))

        TestResourceView.order_by = 'slug'
        status_code, json_response = self.get()

        assert_that(status_code, is_(200))
        assert_that(json_response[0]['name'], is_('foo-node-2'))

    def test_resource_re_string_multiple_ids(self):
        re = resource_re_string('node', TestResourceViewMultipleIDs)
        assert_that(re, is_(
            '^node(?:/((?P<id>{})|(?P<slug>[\\w-]+))'
            '(?:/(?P<sub_resource>[a-z]+))?)?'.format(
                UUID_RE_STRING)))

    def test_multiple_ids(self):
        node = NodeFactory(name='foo-node-1', slug='foo-node-1')

        status_code, id_response = self.get(
            {'id': str(node.id)},
            cls=TestResourceViewMultipleIDs
        )

        assert_that(status_code, is_(200))

        status_code, slug_response = self.get(
            {'slug': node.slug},
            cls=TestResourceViewMultipleIDs
        )

        assert_that(status_code, is_(200))
        assert_that(slug_response, is_(id_response))

    def test_list_filters(self):
        NodeFactory(name='foo')
        NodeFactory(name='bar')

        status_code, json_response = self.get(query={
            'name': 'bAr',
        })

        assert_that(status_code, is_(200))
        assert_that(len(json_response), is_(1))
        assert_that(json_response[0]['name'], is_('bar'))

    def test_list_empty(self):
        status_code, json_response = self.get()

        assert_that(status_code, is_(200))
        assert_that(len(json_response), is_(0))

    def test_get(self):
        node = NodeFactory()

        status_code, json_response = self.get({'id': node.id})

        assert_that(status_code, is_(200))
        assert_that(json_response['name'], is_(node.name))

    def test_get_does_not_exist(self):
        NodeFactory()

        status_code, json_response = self.get({
            'id': 'fc1457d3-d4fe-41a5-8717-b412bee388e4'
        })

        assert_that(status_code, is_(404))

    def test_list_returns_all_instances_if_user_has_admin_permission(self):
        view = TestResourceViewCollector()

        request = HttpRequest()
        request.method = 'GET'
        request.META['HTTP_AUTHORIZATION'] = \
            'Bearer correct-token'

        settings.USE_DEVELOPMENT_USERS = False
        signon = govuk_signon_mock(permissions=['admin'])
        with HTTMock(signon):
            response = view.get(request)

            try:
                json_response = json.loads(response.content)
            except ValueError:
                json_response = None

            assert_that(response.status_code, is_(200))
            assert_that(len(json_response), is_(2))
            assert_that(json_response, contains_inanyorder(
                has_entry("name", starts_with(
                    self.__class__.collector_type1.name)),
                has_entry("name", starts_with(
                    self.__class__.collector_type2.name))))

    def test_detail_returns_unowned_if_user_has_admin_permission(self):
        view = TestResourceViewCollector()

        request = HttpRequest()
        request.method = 'GET'
        request.META['HTTP_AUTHORIZATION'] = \
            'Bearer correct-token'

        settings.USE_DEVELOPMENT_USERS = False
        signon = govuk_signon_mock(permissions=['admin'])
        with HTTMock(signon):
            response = view.get(request, **{'id': self.collector1.id})

            try:
                json_response = json.loads(response.content)
            except ValueError:
                json_response = None

            assert_that(response.status_code, is_(200))
            assert_that(json_response['id'], equal_to(
                str(self.__class__.collector1.id)))

    def test_list_returns_all_if_omniscient_nd_collector_view_but_no_ownership(
            self):
        view = TestResourceViewCollector()

        request = HttpRequest()
        request.method = 'GET'
        request.META['HTTP_AUTHORIZATION'] = \
            'Bearer correct-token'

        settings.USE_DEVELOPMENT_USERS = False
        signon = govuk_signon_mock(
            permissions=['omniscient', 'collector-view'])
        with HTTMock(signon):
            response = view.get(request)

            try:
                json_response = json.loads(response.content)
            except ValueError:
                json_response = None

            assert_that(response.status_code, is_(200))
            assert_that(len(json_response), is_(2))
            assert_that(json_response, contains_inanyorder(
                has_entry("name", starts_with(
                    self.__class__.collector_type1.name)),
                has_entry("name", starts_with(
                    self.__class__.collector_type2.name))))

    def test_list_returns_403_if_omniscient_no_collector_view(
            self):
        view = TestResourceViewCollector()

        request = HttpRequest()
        request.method = 'GET'
        request.META['HTTP_AUTHORIZATION'] = \
            'Bearer correct-token'

        settings.USE_DEVELOPMENT_USERS = False
        signon = govuk_signon_mock(permissions=['omniscient'])
        with HTTMock(signon):
            response = view.get(request)
            assert_that(response.status_code, is_(403))

    def test_list_returns_empty_list_if_collector_view_not_omniscient(
            self):
        view = TestResourceViewCollector()

        request = HttpRequest()
        request.method = 'GET'
        request.META['HTTP_AUTHORIZATION'] = \
            'Bearer correct-token'

        settings.USE_DEVELOPMENT_USERS = False
        signon = govuk_signon_mock(permissions=['collector-view'])
        with HTTMock(signon):
            response = view.get(request)

            try:
                json_response = json.loads(response.content)
            except ValueError:
                json_response = None

            assert_that(response.status_code, is_(200))
            assert_that(len(json_response), is_(0))

    def test_detail_returns_if_omniscient_nd_collector_view_no_ownership(self):
        view = TestResourceViewCollector()

        request = HttpRequest()
        request.method = 'GET'
        request.META['HTTP_AUTHORIZATION'] = \
            'Bearer correct-token'

        settings.USE_DEVELOPMENT_USERS = False
        signon = govuk_signon_mock(
            permissions=['omniscient', 'collector-view'])
        with HTTMock(signon):
            response = view.get(request, **{'id': self.collector1.id})

            try:
                json_response = json.loads(response.content)
            except ValueError:
                json_response = None

            assert_that(response.status_code, is_(200))
            assert_that(json_response['id'], equal_to(
                str(self.__class__.collector1.id)))

    def test_detail_returns_403_if_omniscient_no_collector_view(self):
        view = TestResourceViewCollector()

        request = HttpRequest()
        request.method = 'GET'
        request.META['HTTP_AUTHORIZATION'] = \
            'Bearer correct-token'

        settings.USE_DEVELOPMENT_USERS = False
        signon = govuk_signon_mock(
            permissions=['omniscient'])
        with HTTMock(signon):
            response = view.get(request, **{'id': self.collector1.id})
            assert_that(response.status_code, is_(403))

    def test_detail_returns_404_if_collector_view_not_omniscient(self):
        view = TestResourceViewCollector()

        request = HttpRequest()
        request.method = 'GET'
        request.META['HTTP_AUTHORIZATION'] = \
            'Bearer correct-token'

        settings.USE_DEVELOPMENT_USERS = False
        signon = govuk_signon_mock(permissions=['collector-view'])
        with HTTMock(signon):
            response = view.get(request, **{'id': self.collector1.id})
            assert_that(response.status_code, is_(404))

    # --------------------------------------
    # sub view tests
    # --------------------------------------

    def test_post(self):
        node_type = NodeTypeFactory()
        post_object = {
            'type_id': str(node_type.id),
            'name': 'foo',
            'slug': 'xtx'
        }
        status_code, json_response = self.post(body=json.dumps(post_object))

        assert_that(status_code, is_(200))
        assert_that(json_response['name'], is_('foo'))
        assert_that(json_response, has_key('id'))

    def test_post_must_be_json(self):
        status_code, _ = self.post(content_type='text/plain')
        assert_that(status_code, is_(415))

    def test_post_body_must_be_json(self):
        status_code, _ = self.post(body='not json')
        assert_that(status_code, is_(400))

    def test_post_must_validate_schema(self):
        post_object = {
            'type_id': 'not a uuid',
            'name': 'foo',
        }
        status_code, _ = self.post(body=json.dumps(post_object))
        assert_that(status_code, is_(400))

    def test_rollsback_on_failure(self):
        node_type = NodeTypeFactory()
        post_object = {
            'type_id': str(node_type.id),
            'name': 'save-and-fail-validation',
            'slug': 'save-and',
        }
        status_code, json_response = self.post(body=json.dumps(post_object))

        assert_that(status_code, is_(400))
        assert_that(
            calling(Node.objects.get).with_args(
                name='save-and-fail-validation'),
            raises(Node.DoesNotExist),
        )

    def test_post_doesnt_update(self):
        node_type = NodeTypeFactory()
        post_object = {
            'type_id': str(node_type.id),
            'name': 'foo',
            'slug': 'xtx'
        }
        status_code, json_response = self.post(body=json.dumps(post_object))

        assert_that(status_code, is_(200))

        post_object['id'] = json_response['id']
        post_object['name'] = 'foobar'
        status_code, json_response = self.post(body=json.dumps(post_object))

        assert_that(status_code, is_(400))

    def test_put(self):
        node_type = NodeTypeFactory()
        post_object = {
            'type_id': str(node_type.id),
            'name': 'foo',
            'slug': 'xtx'
        }
        status_code, post_json_response = self.post(
            body=json.dumps(post_object))

        assert_that(status_code, is_(200))

        post_object['name'] = 'foobar'
        status_code, put_json_response = self.put(
            body=json.dumps(post_object),
            args={
                'id': post_json_response['id'],
            },
        )

        assert_that(status_code, is_(200))
        assert_that(put_json_response['name'], is_('foobar'))
        assert_that(put_json_response['id'], post_json_response['id'])

    def test_update_relationships(self):
        node_type = NodeTypeFactory()
        view = TestResourceView()

        request = HttpRequest()
        request.method = 'POST'
        request.META['CONTENT_TYPE'] = 'application/json'
        request.META['HTTP_AUTHORIZATION'] = \
            'Bearer development-oauth-access-token'
        request._body = json.dumps({
            'type_id': str(node_type.id),
            'name': 'foo',
            'slug': 'xtx',
        })

        response = view.post(request)

        assert_that(response, instance_of(HttpResponse))
        assert_that(response.status_code, is_(200))
        assert_that(view.was_saved, is_(True))

    def test_sub_resource_returns_child_object(self):
        node = NodeFactory()
        status_code, sub_resource = self.get(args={
            "id": node.id,
            "sub_resource": "child"})

        assert_that(status_code, is_(200))
        assert_that(sub_resource, contains(has_entry("foo", "bar")))

    def test_sub_resource_delete_returns_405(self):
        node = NodeFactory()
        status_code, sub_resource = self.delete(args={
            "id": node.id,
            "sub_resource": "child"})

        assert_that(status_code, is_(405))

    def test_if_post_with_id_bad_request(self):
        status_code, resp = self.post(args={
            'id': 'fc1457d3-d4fe-41a5-8717-b412bee388e4',
        })
        assert_that(status_code, is_(405))

    def test_post_to_a_sub_resource(self):
        node = NodeFactory()
        node_type = NodeTypeFactory()
        status_code, resp = self.post(args={
            'id': node.id,
            'sub_resource': 'child',
        }, body=json.dumps({
            'type_id': str(node_type.id),
            'slug': 'a-node',
            'name': 'a-node',
        }))
        assert_that(status_code, is_(200))
        assert_that(node.node_set.count(), is_(1))

    def test_post_404s_if_parent_doesnt_exist(self):
        status_code, resp = self.post(args={
            'id': 'fc1457d3-d4fe-41a5-8717-b412bee388e4',
            'sub_resource': 'child',
        }, body=json.dumps({
        }))
        assert_that(status_code, is_(404))

    def test_post_to_sub_resource_validates_against_schema(self):
        node = NodeFactory()
        status_code, response = self.post(args={
            'id': node.id,
            'sub_resource': 'child',
        }, body=json.dumps({}))
        assert_that(status_code, is_(400))

    def test_create_http_error(self):
        status = 400
        message = "Detail for 400 Bad Request"
        request = HttpRequest()

        error = create_http_error(status, message, request)

        err = json.loads(error.content)

        assert_that(error.status_code, equal_to(400))
        assert_that(err["errors"][0]["detail"],
                    equal_to("Detail for 400 Bad Request"))

    def test_delete(self):
        node = NodeFactory()
        Node.published = False
        try:
            status_code, response = self.delete(args={
                'id': node.id,
            })
            assert_that(status_code, is_(200))
            assert_that(len(Node.objects.filter(id=node.id)), equal_to(0))
        finally:
            delattr(Node, "published")

    def test_delete_no_published_attr(self):
        node = NodeFactory()
        status_code, response = self.delete(args={
            'id': node.id,
        })
        assert_that(status_code, is_(405))

    def test_delete_published(self):
        node = NodeFactory()
        Node.published = True
        try:
            status_code, response = self.delete(args={
                'id': node.id,
            })
            assert_that(status_code, is_(400))
            assert_that(len(Node.objects.filter(id=node.id)), equal_to(1))
        finally:
            delattr(Node, "published")
