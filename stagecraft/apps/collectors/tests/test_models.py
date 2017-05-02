from django.test import TestCase
from hamcrest import assert_that, contains_string, not_none, none, equal_to

from stagecraft.apps.collectors.models import DataSource
from stagecraft.apps.collectors.tests.factories import CollectorTypeFactory, \
    CollectorFactory, ProviderFactory, DataSourceFactory
from stagecraft.apps.datasets.tests.factories import DataTypeFactory, \
    DataGroupFactory, DataSetFactory
from stagecraft.apps.users.tests.factories import UserFactory


class CollectorTestCase(TestCase):
    def test_create_produces_a_name(self):
        data_type = DataTypeFactory(name="a_type")
        data_group = DataGroupFactory(name="a_group")

        data_set = DataSetFactory(data_type=data_type, data_group=data_group)
        collector_type = CollectorTypeFactory(name="a_collector_type")

        collector = CollectorFactory(type=collector_type, data_set=data_set)

        assert_that(collector.name, contains_string("a_type"))
        assert_that(collector.name, contains_string("a_group"))
        assert_that(collector.name, contains_string("a_collector_type"))

    def test_query_is_validated_against_collector_type(self):
        collector_type = CollectorTypeFactory(
            query_schema={
                "$schema": "http://json-schema.org/schema#",
                "type": "object",
                "properties": {
                    "filter": {"type": "string"},
                },
                "required": ["filter"],
                "additionalProperties": False,
            })

        collector = CollectorFactory(type=collector_type,
                                     query={"field": "somefield"})

        assert_that(collector.validate(), contains_string("query"))

        collector.query = {"filter": "somefilter"}

        assert_that(collector.validate(), none())

    def test_options_are_validated_against_collector_type(self):
        collector_type = CollectorTypeFactory(
            options_schema={
                "$schema": "http://json-schema.org/schema#",
                "type": "object",
                "properties": {
                    "extras": {"type": "string"},
                },
                "required": ["extras"],
                "additionalProperties": False,
            })

        collector = CollectorFactory(type=collector_type,
                                     options={"field": "somefield"})

        assert_that(collector.validate(), contains_string("options"))

        collector.options = {"extras": "an extra"}

        assert_that(collector.validate(), none())

    def test_requires_common_provider(self):
        provider_1 = ProviderFactory()
        provider_2 = ProviderFactory()

        collector_type = CollectorTypeFactory(provider=provider_1)
        data_source = DataSourceFactory(provider=provider_2)

        collector = CollectorFactory(
            type=collector_type, data_source=data_source)

        assert_that(collector.validate(), contains_string('provider'))

        data_source.provider = provider_1

        assert_that(collector.validate(), none())

    def test_user_is_owner_of_data_source(self):
        user = UserFactory()
        collector = CollectorFactory()
        collector.data_set.owners.add(user)

        assert_that(collector.validate(user=user), contains_string('owner'))
        assert_that(
            collector.validate(user=user), contains_string('data source'))

        collector.data_source.owners.add(user)

        assert_that(collector.validate(user=user), none())

    def test_user_is_owner_of_data_set(self):
        user = UserFactory()
        collector = CollectorFactory()
        collector.data_source.owners.add(user)

        assert_that(collector.validate(user=user), contains_string('owner'))
        assert_that(collector.validate(user=user), contains_string('data set'))

        collector.data_set.owners.add(user)

        assert_that(collector.validate(user=user), none())


class CollectorTypeTestCase(TestCase):
    def test_query_schema_validation(self):
        collector_type = CollectorTypeFactory()
        collector_type.query_schema = {
            "$schema": False,
        }

        assert_that(collector_type.validate(), contains_string("query"))

        collector_type.query_schema = {
            "$schema": "A Schema",
        }

        assert_that(collector_type.validate(), none())

    def test_options_schema_validation(self):
        collector_type = CollectorTypeFactory()
        collector_type.options_schema = {
            "$schema": False,
        }

        assert_that(collector_type.validate(),
                    contains_string("options"))

        collector_type.options_schema = {
            "$schema": "A Schema",
        }

        assert_that(collector_type.validate(), none())


class DataSourceTestCase(TestCase):
    def test_credentials_are_validated_against_provider(self):
        provider = ProviderFactory(
            credentials_schema={
                "$schema": "http://json-schema.org/schema#",
                "type": "object",
                "properties": {
                    "password": {"type": "string"},
                },
                "required": ["password"],
                "additionalProperties": False,
            })
        credentials = '{"name": "something"}'
        data_source = DataSourceFactory(provider=provider, credentials=credentials)
        assert_that(data_source.credentials, credentials)
        assert_that(data_source.validate(), not_none())
        data_source.credentials = '{"password": "somepassword"}'
        assert_that(data_source.validate(), none())

    def test_credentials_have_to_be_JSON(self):
        data_source = DataSourceFactory()
        data_source.credentials = 'not-json'
        assert_that(data_source.validate(), not_none())
        data_source.credentials = '{"foo": "bar"}'
        assert_that(data_source.validate(), none())

    def test_credentials_save_to_database(self):
        data_source = DataSourceFactory()
        data_source.credentials = '{}'
        data_source.save()
        retrieved_data_source = DataSource.objects.get(id=data_source.id)
        assert_that(retrieved_data_source.credentials, equal_to('{}'))


class ProviderTestCase(TestCase):
    def test_schema_validation(self):
        provider = ProviderFactory()
        provider.credentials_schema = {
            "$schema": False,
        }

        assert_that(provider.validate(), contains_string("schema"))

        provider.credentials_schema = {
            "$schema": "A Schema",
        }

        assert_that(provider.validate(), none())
