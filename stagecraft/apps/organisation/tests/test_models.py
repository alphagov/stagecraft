from django.core.exceptions import ValidationError
from django.db import IntegrityError
from django.test import TestCase
from hamcrest import assert_that, has_entry, has_key, is_not
from nose.tools import eq_, assert_raises

from ..models import Node, NodeType


class NodeTestCase(TestCase):

    @classmethod
    def setUpClass(cls):
        cls.node_type = NodeType.objects.create(name='foo')

    @classmethod
    def tearDownClass(cls):
        cls.node_type.delete()

    def test_name_must_be_unique(self):
        a = Node.objects.create(name='abc', typeOf=self.node_type)
        a.validate_unique()

        b = Node(name='abc', typeOf=self.node_type)
        assert_raises(ValidationError, lambda: b.validate_unique())

    def test_abbreviation_must_be_unique(self):
        a = Node.objects.create(
            name='foo',
            abbreviation='abc',
            typeOf=self.node_type
        )
        a.validate_unique()

        b = Node(name='bar', abbreviation='abc', typeOf=self.node_type)
        assert_raises(ValidationError, lambda: b.validate_unique())

    def test_requires_typeof(self):
        assert_raises(IntegrityError, lambda: Node.objects.create(name='foo'))

    def test_serialize(self):
        node = Node.objects.create(
            name='foo',
            abbreviation='abc',
            typeOf=self.node_type
        )
        serialized_node = node.serialize()

        assert_that(serialized_node, has_entry('id', str(node.id)))
        assert_that(serialized_node, has_entry('name', 'foo'))
        assert_that(serialized_node, has_entry('abbreviation', 'abc'))
        assert_that(
            serialized_node,
            has_entry('type', node.typeOf.serialize())
        )

    def test_serialize_optional_abbreviation(self):
        node = Node.objects.create(name='foo', typeOf=self.node_type)
        serialized_node = node.serialize()

        assert_that(serialized_node, has_entry('name', 'foo'))
        assert_that(serialized_node, has_entry('abbreviation', 'foo'))

    def test_serialize_resolve_parent(self):
        parent_node = Node.objects.create(name='foo', typeOf=self.node_type)
        node = Node.objects.create(
            name='bar',
            typeOf=self.node_type,
            parent=parent_node
        )

        assert_that(node.serialize(), has_key('parent'))
        assert_that(
            node.serialize(resolve_parent=False),
            is_not(has_key('parent'))
        )

        assert_that(parent_node.serialize(), has_entry('parent', None))

    def test_serialize_resolve_only_one_parent(self):
        super_parent_node = Node.objects.create(
            name='god',
            typeOf=self.node_type
        )
        parent_node = Node.objects.create(
            name='foo',
            typeOf=self.node_type,
            parent=super_parent_node
        )
        node = Node.objects.create(
            name='bar',
            typeOf=self.node_type,
            parent=parent_node
        )

        serialized_node = node.serialize()

        assert_that(serialized_node, has_key('parent'))
        assert_that(serialized_node['parent'], is_not(has_key('parent')))


class NodeTypeTestCase(TestCase):

    def test_name_must_be_unique(self):
        a = NodeType.objects.create(name='abc')
        a.validate_unique()

        b = NodeType(name='abc')
        assert_raises(ValidationError, lambda: b.validate_unique())

    def test_serialize(self):
        node_type = NodeType.objects.create(name='bar')
        serialized_node_type = node_type.serialize()

        assert_that(serialized_node_type, has_entry('name', 'bar'))
        assert_that(serialized_node_type, has_entry('id', str(node_type.id)))
