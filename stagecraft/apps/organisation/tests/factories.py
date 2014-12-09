import factory

from ..models import Node, NodeType


class NodeTypeFactory(factory.DjangoModelFactory):
    class Meta:
        model = NodeType

    name = factory.Sequence(lambda n: 'type-name-%s' % n)


class NodeFactory(factory.DjangoModelFactory):
    class Meta:
        model = Node

    name = factory.Sequence(lambda n: 'name-%s' % n)
    abbreviation = factory.Sequence(lambda n: 'abbreviation-%s' % n)
    typeOf = factory.SubFactory(NodeTypeFactory)
