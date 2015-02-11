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

    @factory.post_generation
    def parent(self, create, extracted, **kwargs):
        if not create:
            return

        if extracted:
            self.parents.add(extracted)
