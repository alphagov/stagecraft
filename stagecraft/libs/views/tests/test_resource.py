import json

from django.test.client import RequestFactory
from mock import Mock
from hamcrest import (
    assert_that, is_, calling, raises, is_not,
    instance_of, starts_with, has_key, equal_to
)
from unittest import TestCase

from django.http import HttpRequest, HttpResponse
from jsonschema import FormatError

from stagecraft.apps.organisation.models import Node, NodeType
from stagecraft.apps.organisation.tests.factories import (
    NodeFactory, NodeTypeFactory
)

from ..resource import FORMAT_CHECKER, ResourceView


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

    def update_model(self, model, model_json, request):
        try:
            node_type = NodeType.objects.get(id=model_json['type_id'])
        except NodeType.DoesNotExist:
            return HttpResponse('no NodeType found', status=400)

        model.name = model_json['name']
        model.slug = model_json.get('slug', None)
        model.abbreviation = model_json.get('abbreviation', None)
        model.typeOf = node_type

        if model_json['name'] == 'save-and-fail-validation':
            model.save()

    @staticmethod
    def serialize(model):
        return {
            'id': str(model.id),
            'name': model.name,
        }


class ResourceViewTestCase(TestCase):

    def get(self, args={}, query={}):
        view = TestResourceView()

        request = HttpRequest()
        for (k, v) in query.items():
            request.GET[k] = v

        response = view.get(request, **args)

        assert_that(response, instance_of(HttpResponse))

        try:
            json_response = json.loads(response.content)
        except ValueError:
            json_response = None

        return response.status_code, json_response

    def post(self, body='', content_type='application/json', args={}):
        view = TestResourceView()

        request = HttpRequest()
        request.META['CONTENT_TYPE'] = content_type
        request._body = body

        response = view.post(None, request, **args)

        assert_that(response, instance_of(HttpResponse))

        try:
            json_response = json.loads(response.content)
        except ValueError:
            json_response = None

        return response.status_code, json_response

    def tearDown(self):
        Node.objects.all().delete()

    def test_list(self):
        NodeFactory(name='foo-node-1')
        NodeFactory(name='foo-node-2')

        status_code, json_response = self.get()

        assert_that(status_code, is_(200))
        assert_that(len(json_response), is_(2))
        assert_that(json_response[0]['name'], starts_with('foo-node'))

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
        node = NodeFactory()

        status_code, json_response = self.get({
            'id': 'fc1457d3-d4fe-41a5-8717-b412bee388e4'
        })

        assert_that(status_code, is_(404))

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

    def test_get_or_create(self):
        node = NodeFactory()
        view = TestResourceView()

        model = view._get_or_create_model({})
        assert_that(model.name, is_not(equal_to(node.name)))

        model = view._get_or_create_model({
            'id': str(node.id),
        })
        assert_that(model.name, is_(node.name))

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
