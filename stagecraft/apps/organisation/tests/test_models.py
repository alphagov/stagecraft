from django.core.exceptions import ValidationError
from django.db import IntegrityError
from django.test import TestCase
from hamcrest import assert_that, has_entry, has_key, is_not, is_
from nose.tools import eq_, assert_raises

from ..models import Node, NodeType


def a_node_has_name(name, nodes):
    return len(filter(lambda n: n.name == name, nodes)) > 0


class NodeTestCase(TestCase):

    @classmethod
    def setUpClass(cls):
        cls.node_type = NodeType.objects.create(name='foo')

    @classmethod
    def tearDownClass(cls):
        cls.node_type.delete()

    def test_slug_must_be_slug_not_blank(self):
        a = Node(
            slug='what_is_this?', name='abc', typeOf=self.node_type)
        assert_raises(ValidationError, lambda: a.full_clean())

        b = Node(slug='what-is-this', name='xyx', typeOf=self.node_type)
        b.full_clean()

        c = Node(name='xyz', typeOf=self.node_type)
        assert_raises(ValidationError, lambda: c.full_clean())

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

    def test_multiple_parents(self):
        parent_1 = Node.objects.create(name='1', typeOf=self.node_type)
        parent_2 = Node.objects.create(name='2', typeOf=self.node_type)
        child = Node.objects.create(name='child', typeOf=self.node_type)
        child.parents.add(parent_1)
        child.parents.add(parent_2)
        child.save()

        ancestors_and_self = list(child.get_ancestors(include_self=True))
        assert_that(len(ancestors_and_self), is_(3))
        assert_that(a_node_has_name('1', ancestors_and_self), is_(True))
        assert_that(a_node_has_name('2', ancestors_and_self), is_(True))
        assert_that(a_node_has_name('child', ancestors_and_self), is_(True))


class NodeTypeTestCase(TestCase):

    def test_name_must_be_unique(self):
        a = NodeType.objects.create(name='abc')
        a.validate_unique()

        b = NodeType(name='abc')
        assert_raises(ValidationError, lambda: b.validate_unique())
