import factory
from django.contrib.messages.storage.fallback import FallbackStorage
from django.http import HttpRequest

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


class RequestFactory(HttpRequest):
    session = 'session'

    def __init__(self):
        super(RequestFactory, self).__init__()
        self._messages = FallbackStorage(self)

    def get_messages(self):
        return getattr(self._messages, '_queued_messages')

    def get_message_strings(self):
        return [str(m) for m in self.get_messages()]
