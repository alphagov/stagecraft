import factory
from stagecraft.apps.collectors.models import \
    CollectorType, \
    Provider, \
    Collector, \
    DataSource
from stagecraft.apps.datasets.tests.factories import DataSetFactory


class ProviderFactory(factory.DjangoModelFactory):

    class Meta:
        model = Provider
        django_get_or_create = ('name',)
    name = factory.Sequence(lambda n: 'provider-%s' % n)


class CollectorTypeFactory(factory.DjangoModelFactory):

    class Meta:
        model = CollectorType

    name = factory.Sequence(lambda n: 'collector-type-%s' % n)
    provider = factory.SubFactory(ProviderFactory)
    entry_point = factory.Sequence(lambda n: 'entry_point_%s' % n)


class DataSourceFactory(factory.DjangoModelFactory):

    class Meta:
        model = DataSource
        django_get_or_create = ('name',)
    name = factory.Sequence(lambda n: 'data-source-%s' % n)
    provider = factory.SubFactory(ProviderFactory)


class CollectorFactory(factory.DjangoModelFactory):

    class Meta:
        model = Collector

    type = factory.SubFactory(CollectorTypeFactory)
    data_source = factory.SubFactory(
        DataSourceFactory, provider=factory.SelfAttribute('..type.provider'))
    data_set = factory.SubFactory(DataSetFactory)
