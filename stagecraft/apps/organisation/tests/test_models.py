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


class NodeTypeTestCase(TestCase):

    def test_name_must_be_unique(self):
        a = NodeType.objects.create(name='abc')
        a.validate_unique()

        b = NodeType(name='abc')
        assert_raises(ValidationError, lambda: b.validate_unique())
