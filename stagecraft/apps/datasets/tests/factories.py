import factory

from ..models import DataSet, DataType, DataGroup


class DataGroupFactory(factory.DjangoModelFactory):

    class Meta:
        model = DataGroup
    name = factory.Sequence(lambda n: 'data-group-%s' % n)


class DataTypeFactory(factory.DjangoModelFactory):

    class Meta:
        model = DataType
    name = factory.Sequence(lambda n: 'data-type-%s' % n)


class DataSetFactory(factory.DjangoModelFactory):

    class Meta:
        model = DataSet

    data_type = factory.SubFactory(DataTypeFactory)
    data_group = factory.SubFactory(DataGroupFactory)
