import factory
from ...models import Dashboard
from ....organisation.models import Node, NodeType


class DashboardFactory(factory.DjangoModelFactory):
    class Meta:
        model = Dashboard

    published = True
    title = "title"
    slug = factory.Sequence(lambda n: 'slug%s' % n)


class NodeTypeFactory(factory.DjangoModelFactory):
    class Meta:
        model = NodeType


class DepartmentTypeFactory(NodeTypeFactory):
    name = 'department'


class AgencyTypeFactory(NodeTypeFactory):
    name = 'agency'


class NodeFactory(factory.DjangoModelFactory):
    class Meta:
        model = Node
    name = factory.Sequence(lambda n: 'name-%s' % n)
    abbreviation = factory.Sequence(lambda n: 'abbreviation-%s' % n)
    typeOf = factory.SubFactory(NodeTypeFactory)


class DepartmentFactory(NodeFactory):
    name = factory.Sequence(lambda n: 'department-%s' % n)
    typeOf = factory.SubFactory(DepartmentTypeFactory)


class AgencyFactory(NodeFactory):
    name = factory.Sequence(lambda n: 'agency-%s' % n)
    typeOf = factory.SubFactory(AgencyTypeFactory)


class AgencyWithDepartmentFactory(AgencyFactory):
    parent = factory.SubFactory(DepartmentFactory)
