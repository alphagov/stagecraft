import factory
from ...models import Dashboard, Link, ModuleType, Module
from ....organisation.models import Node, NodeType


class DashboardFactory(factory.DjangoModelFactory):
    class Meta:
        model = Dashboard

    published = True
    title = "title"
    slug = factory.Sequence(lambda n: 'slug%s' % n)


class LinkFactory(factory.DjangoModelFactory):
    class Meta:
        model = Link

    url = factory.Sequence(lambda n: 'https://www.gov.uk/link-%s' % n)
    title = 'Link title'
    link_type = 'transaction'
    dashboard = factory.SubFactory(DashboardFactory)


class ModuleTypeFactory(factory.DjangoModelFactory):
    class Meta:
        model = ModuleType

    name = factory.Sequence(lambda n: 'name %s' % n)
    schema = {}


class ModuleFactory(factory.DjangoModelFactory):
    class Meta:
        model = Module

    type = factory.SubFactory(ModuleTypeFactory)
    dashboard = factory.SubFactory(DashboardFactory)
    slug = factory.Sequence(lambda n: 'slug{}'.format(n))
    title = 'title'
    info = []
    options = {}
    order = factory.Sequence(lambda n: n)


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
