import json
import uuid
from datetime import datetime
from django.test import TestCase
from hamcrest import assert_that, equal_to, has_key, has_entries, \
    match_equality
from stagecraft.apps.collectors.tests.factories import ProviderFactory, \
    DataSourceFactory, CollectorTypeFactory, CollectorFactory
from stagecraft.apps.datasets.tests.factories import DataSetFactory
from stagecraft.apps.users.models import User
from stagecraft.libs.authorization.tests.test_http import with_govuk_signon
from stagecraft.libs.backdrop_client import disable_backdrop_connection
from stagecraft.libs.views.utils import to_json
from mock import patch


class ProviderViewTestCase(TestCase):

    def test_get(self):
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
        response = self.client.get(
            '/provider/{}'.format(provider.name),
            HTTP_AUTHORIZATION='Bearer development-oauth-access-token',
            content_type='application/json')

        assert_that(response.status_code, equal_to(200))

        resp_json = json.loads(response.content)

        assert_that(resp_json['id'], equal_to(str(provider.id)))
        assert_that(resp_json['slug'], equal_to(provider.slug))
        assert_that(resp_json['name'], equal_to(provider.name))
        assert_that(resp_json['credentials_schema'], equal_to(
            provider.credentials_schema))

    def test_get_from_unauthorised_client_fails(self):
        provider = ProviderFactory()
        resp = self.client.get(
            '/provider/{}'.format(provider.name))

        assert_that(resp.status_code, equal_to(403))

    def test_list(self):
        provider_1 = ProviderFactory()
        provider_2 = ProviderFactory()

        response = self.client.get(
            '/provider',
            HTTP_AUTHORIZATION='Bearer development-oauth-access-token',
            content_type='application/json')

        assert_that(response.status_code, equal_to(200))

        resp_json = json.loads(response.content)

        assert_that(resp_json, match_equality(
            has_entries({"slug": provider_1.slug})))
        assert_that(resp_json, match_equality(
            has_entries({"slug": provider_2.slug})))

    # The list route requires for_user if you're not an admin and the model
    # has an owner attribute. This test implicitly tests whether the for_user
    # method and the accompanying model Manager class is required.
    @with_govuk_signon(permissions=['collector'])
    def test_can_list_providers_with_collector_permission(self):
        provider = ProviderFactory()

        response = self.client.get(
            '/provider',
            HTTP_AUTHORIZATION='Bearer correct-token')

        assert_that(response.status_code, equal_to(200))

    def test_post(self):
        provider = {
            "name": "some-provider",
            "slug": "some-provider"
        }

        resp = self.client.post(
            '/provider',
            data=json.dumps(provider),
            HTTP_AUTHORIZATION='Bearer development-oauth-access-token',
            content_type='application/json')

        assert_that(resp.status_code, equal_to(200))

        resp_json = json.loads(resp.content)

        assert_that(resp_json, has_key('id'))
        assert_that(resp_json['name'], equal_to('some-provider'))
        assert_that(resp_json['slug'], equal_to('some-provider'))

    def test_post_from_unauthorised_client_fails(self):
        provider = {
            'name': 'some-provider',
            "slug": "some-provider"
        }
        resp = self.client.post(
            '/provider',
            data=json.dumps(provider),
            content_type='application/json')

        assert_that(resp.status_code, equal_to(403))

    def test_put(self):
        provider = ProviderFactory()
        credentials_schema = {
            "$schema": "http://json-schema.org/schema#",
            "type": "object",
            "properties": {
                    "password": {"type": "string"},
            },
            "required": ["password"],
            "additionalProperties": False,
        }

        provider_update = {
            "name": provider.name,
            "slug": provider.slug,
            "credentials_schema": credentials_schema
        }

        response = self.client.put(
            '/provider/{}'.format(provider.id),
            data=json.dumps(provider_update),
            HTTP_AUTHORIZATION='Bearer development-oauth-access-token',
            content_type='application/json')

        assert_that(response.status_code, equal_to(200))

        resp_json = json.loads(response.content)

        assert_that(resp_json['credentials_schema'],
                    equal_to(credentials_schema))


class DataSourceViewTestCase(TestCase):

    @classmethod
    def setUpClass(cls):
        cls.provider = ProviderFactory()

    @classmethod
    def tearDownClass(cls):
        cls.provider.delete()

    def test_get(self):
        data_source = DataSourceFactory()
        response = self.client.get(
            '/data-source/{}'.format(data_source.name),
            HTTP_AUTHORIZATION='Bearer development-oauth-access-token',
            content_type='application/json')

        assert_that(response.status_code, equal_to(200))

        resp_json = json.loads(response.content)

        assert_that(resp_json['id'], equal_to(str(data_source.id)))
        assert_that(resp_json['slug'], equal_to(data_source.slug))
        assert_that(resp_json['name'], equal_to(data_source.name))
        assert_that(
            resp_json['provider']['name'], equal_to(data_source.provider.name))
        assert_that(resp_json, not(has_key('credentials')))
        assert_that(resp_json, not(has_key('owners')))

    def test_get_from_unauthorised_client_fails(self):
        data_source = DataSourceFactory()
        resp = self.client.get(
            '/data-source/{}'.format(data_source.name))

        assert_that(resp.status_code, equal_to(403))

    def test_list(self):
        data_source_1 = DataSourceFactory()
        data_source_2 = DataSourceFactory()

        response = self.client.get(
            '/data-source',
            HTTP_AUTHORIZATION='Bearer development-oauth-access-token',
            content_type='application/json')

        assert_that(response.status_code, equal_to(200))

        resp_json = json.loads(response.content)

        assert_that(resp_json, match_equality(
            has_entries({"slug": data_source_1.slug})))
        assert_that(resp_json, match_equality(
            has_entries({"slug": data_source_2.slug})))

    # The list route requires for_user if you're not an admin and the model
    # has an owner attribute. This test implicitly tests whether the for_user
    # method and the accompanying model Manager class is required.
    @with_govuk_signon(permissions=['collector'])
    def test_can_list_data_sources_with_collector_permission(self):
        data_source = DataSourceFactory()

        response = self.client.get(
            '/data-source',
            HTTP_AUTHORIZATION='Bearer correct-token')

        assert_that(response.status_code, equal_to(200))

    def test_post(self):
        data_source = {
            "name": "some-data-source",
            "slug": "some-data-source",
            "provider_id": self.provider.id
        }

        resp = self.client.post(
            '/data-source',
            data=to_json(data_source),
            HTTP_AUTHORIZATION='Bearer development-oauth-access-token',
            content_type='application/json')

        assert_that(resp.status_code, equal_to(200))

        resp_json = json.loads(resp.content)

        assert_that(resp_json, has_key('id'))
        assert_that(resp_json['name'], equal_to('some-data-source'))
        assert_that(resp_json['slug'], equal_to('some-data-source'))
        assert_that(resp_json['provider']['name'], equal_to(
            self.provider.name))

    def test_post_from_unauthorised_client_fails(self):
        data_source = {
            "name": "some-data-source",
            "slug": "some-data-source",
            "provider": self.provider.id
        }
        resp = self.client.post(
            '/data-source',
            data=to_json(data_source),
            content_type='application/json')

        assert_that(resp.status_code, equal_to(403))

    def test_post_with_non_existent_provider_fails(self):
        provider = uuid.UUID('01234a12-1234-1234-5b6c-0de12e3a4f15')
        data_source = {
            'name': 'some-data-source',
            'slug': 'some-data-source',
            'provider_id': provider
        }
        response = self.client.post(
            '/data-source',
            data=to_json(data_source),
            HTTP_AUTHORIZATION='Bearer development-oauth-access-token',
            content_type='application/json')

        assert_that(response.status_code, equal_to(400))

        resp_json = json.loads(response.content)
        assert_that(resp_json['message'], equal_to(
            "No provider with id '{}' found".format(provider)))

    @with_govuk_signon(permissions=['collector'])
    def test_get_404_when_user_not_in_ownership_array(self):
        data_source = DataSourceFactory()
        user, _ = User.objects.get_or_create(
            email='not_correct_user.lastname@gov.uk')
        data_source.owners.add(user)

        resp = self.client.get(
            '/data-source/{}'.format(data_source.slug),
            HTTP_AUTHORIZATION='Bearer correct-token')

        assert_that(resp.status_code, equal_to(404))

    def test_put(self):
        data_source = DataSourceFactory()

        data_source_update = {
            "name": data_source.name,
            "slug": "new_slug",
            "provider_id": data_source.provider.id
        }

        response = self.client.put(
            '/data-source/{}'.format(data_source.slug),
            data=to_json(data_source_update),
            HTTP_AUTHORIZATION='Bearer development-oauth-access-token',
            content_type='application/json')

        assert_that(response.status_code, equal_to(200))
        resp_json = json.loads(response.content)
        assert_that(resp_json['slug'], equal_to("new_slug"))


class CollectorTypeViewTestCase(TestCase):

    @classmethod
    def setUpClass(cls):
        cls.provider = ProviderFactory()

    @classmethod
    def tearDownClass(cls):
        cls.provider.delete()

    def test_get(self):
        collector_type = CollectorTypeFactory(
            query_schema={
                "$schema": "A Schema",
            },
            options_schema={
                "$schema": "A Schema",
            }
        )
        response = self.client.get(
            '/collector-type/{}'.format(collector_type.name),
            HTTP_AUTHORIZATION='Bearer development-oauth-access-token',
            content_type='application/json')

        assert_that(response.status_code, equal_to(200))

        resp_json = json.loads(response.content)

        assert_that(resp_json['id'], equal_to(str(collector_type.id)))
        assert_that(resp_json['slug'], equal_to(collector_type.slug))
        assert_that(resp_json['name'], equal_to(collector_type.name))
        assert_that(resp_json['entry_point'], equal_to(
            collector_type.entry_point))
        assert_that(resp_json['provider']['name'], equal_to(
            collector_type.provider.name))
        assert_that(resp_json['query_schema'], equal_to(
            collector_type.query_schema))
        assert_that(resp_json['options_schema'], equal_to(
            collector_type.options_schema))

    def test_get_from_unauthorised_client_fails(self):
        collector_type = CollectorTypeFactory()
        resp = self.client.get(
            '/collector-type/{}'.format(collector_type.name))

        assert_that(resp.status_code, equal_to(403))

    def test_list(self):
        collector_type_1 = CollectorTypeFactory()
        collector_type_2 = CollectorTypeFactory()

        response = self.client.get(
            '/collector-type',
            HTTP_AUTHORIZATION='Bearer development-oauth-access-token',
            content_type='application/json')

        assert_that(response.status_code, equal_to(200))

        resp_json = json.loads(response.content)

        assert_that(resp_json, match_equality(
            has_entries({"slug": collector_type_1.slug})))
        assert_that(resp_json, match_equality(
            has_entries({"slug": collector_type_2.slug})))

    # The list route requires for_user if you're not an admin and the model
    # has an owner attribute. This test implicitly tests whether the for_user
    # method and the accompanying model Manager class is required.
    @with_govuk_signon(permissions=['collector'])
    def test_can_list_collector_types_with_collector_permission(self):
        collector_type = CollectorTypeFactory()

        response = self.client.get(
            '/collector-type',
            HTTP_AUTHORIZATION='Bearer correct-token')

        assert_that(response.status_code, equal_to(200))

    def test_post(self):
        collector_type = {
            "slug": "some-collector-type",
            "name": "some-collector-type",
            "entry_point": "some.collector.type",
            "provider_id": self.provider.id
        }

        resp = self.client.post(
            '/collector-type',
            data=to_json(collector_type),
            HTTP_AUTHORIZATION='Bearer development-oauth-access-token',
            content_type='application/json')

        assert_that(resp.status_code, equal_to(200))

        resp_json = json.loads(resp.content)

        assert_that(resp_json, has_key('id'))
        assert_that(resp_json['slug'], equal_to('some-collector-type'))
        assert_that(resp_json['name'], equal_to('some-collector-type'))
        assert_that(resp_json['entry_point'], equal_to('some.collector.type'))
        assert_that(resp_json['provider']['name'], equal_to(
            self.provider.name))

    def test_post_from_unauthorised_client_fails(self):
        collector_type = {
            "slug": "some-collector-type",
            "name": "some-collector-type",
            "entry_point": "some.collector.type",
            "provider": self.provider.id
        }
        resp = self.client.post(
            '/collector-type',
            data=to_json(collector_type),
            content_type='application/json')

        assert_that(resp.status_code, equal_to(403))

    def test_post_with_non_existent_provider_fails(self):
        provider = uuid.UUID('01234a12-1234-1234-5b6c-0de12e3a4f15')
        collector_type = {
            "slug": "some-collector-type",
            "name": "some-collector-type",
            "entry_point": "some.collector.type",
            "provider_id": provider
        }
        response = self.client.post(
            '/collector-type',
            data=to_json(collector_type),
            HTTP_AUTHORIZATION='Bearer development-oauth-access-token',
            content_type='application/json')

        assert_that(response.status_code, equal_to(400))

        resp_json = json.loads(response.content)
        assert_that(resp_json['message'], equal_to(
            "No provider with id '{}' found".format(provider)))

    def test_put(self):
        collector_type = CollectorTypeFactory()

        collector_type_update = {
            "name": collector_type.name,
            "slug": collector_type.slug,
            "entry_point": "new.entry.point",
            "provider_id": collector_type.provider.id
        }

        response = self.client.put(
            '/collector-type/{}'.format(collector_type.slug),
            data=to_json(collector_type_update),
            HTTP_AUTHORIZATION='Bearer development-oauth-access-token',
            content_type='application/json')

        assert_that(response.status_code, equal_to(200))
        resp_json = json.loads(response.content)
        assert_that(resp_json['entry_point'], equal_to("new.entry.point"))


class CollectorViewTestCase(TestCase):

    @classmethod
    def setUpClass(cls):
        cls.provider = ProviderFactory()
        cls.data_source = DataSourceFactory(provider=cls.provider)
        cls.collector_type = CollectorTypeFactory(provider=cls.provider)
        cls.data_set = DataSetFactory()

    @classmethod
    @disable_backdrop_connection
    def tearDownClass(cls):
        cls.provider.delete()
        cls.data_source.delete()
        cls.collector_type.delete()
        cls.data_set.delete()
        cls.data_set.data_group.delete()
        cls.data_set.data_type.delete()

    def test_get(self):
        collector = CollectorFactory()
        response = self.client.get(
            '/collector/{}'.format(collector.slug),
            HTTP_AUTHORIZATION='Bearer development-oauth-access-token',
            content_type='application/json')

        assert_that(response.status_code, equal_to(200))

        resp_json = json.loads(response.content)

        assert_that(resp_json['id'], equal_to(str(collector.id)))
        assert_that(resp_json['slug'], equal_to(collector.slug))
        assert_that(resp_json['name'], equal_to(collector.name))
        assert_that(resp_json['type']['name'], equal_to(
            collector.type.name))
        assert_that(resp_json['type']['slug'], equal_to(
            collector.type.slug))
        assert_that(resp_json['entry_point'], equal_to(
            collector.type.entry_point))
        assert_that(
            resp_json['data_source']['name'], equal_to(
                collector.data_source.name))
        assert_that(resp_json['data_set']['data_type'], equal_to(
            collector.data_set.data_type.name))
        assert_that(resp_json['data_set']['data_group'], equal_to(
            collector.data_set.data_group.name))
        assert_that(resp_json['data_set'], has_key('bearer_token'))
        assert_that(resp_json['query'], equal_to(collector.query))
        assert_that(resp_json['options'], equal_to(collector.options))
        assert_that(resp_json['provider']['slug'], equal_to(
            collector.type.provider.slug))
        assert_that(resp_json['provider']['name'], equal_to(
            collector.type.provider.name))
        assert_that(resp_json, not(has_key('owners')))

    def test_get_from_unauthorised_client_fails(self):
        collector = CollectorFactory()
        resp = self.client.get(
            '/collector/{}'.format(collector.slug))

        assert_that(resp.status_code, equal_to(403))

    def test_list(self):
        collector_1 = CollectorFactory()
        collector_2 = CollectorFactory()

        response = self.client.get(
            '/collector',
            HTTP_AUTHORIZATION='Bearer development-oauth-access-token',
            content_type='application/json')

        assert_that(response.status_code, equal_to(200))

        resp_json = json.loads(response.content)

        assert_that(resp_json, match_equality(
            has_entries({"slug": collector_1.slug})))
        assert_that(resp_json, match_equality(
            has_entries({"slug": collector_2.slug})))

    # The list route requires for_user if you're not an admin and the model
    # has an owner attribute. This test implicitly tests whether the for_user
    # method and the accompanying model Manager class is required.
    @with_govuk_signon(permissions=['collector'])
    def test_can_list_collectors_with_collector_permission(self):
        collector = CollectorFactory()

        response = self.client.get(
            '/collector',
            HTTP_AUTHORIZATION='Bearer correct-token')

        assert_that(response.status_code, equal_to(200))

    def test_post(self):
        collector = {
            "slug": "some-collector",
            "type_id": self.collector_type.id,
            "data_source_id": self.data_source.id,
            "data_set": {
                "data_type": self.data_set.data_type.name,
                "data_group": self.data_set.data_group.name
            }
        }

        resp = self.client.post(
            '/collector',
            data=to_json(collector),
            HTTP_AUTHORIZATION='Bearer development-oauth-access-token',
            content_type='application/json')

        expected_collector_name = "{} {} {}".format(
            self.collector_type.name,
            self.data_set.data_group.name,
            self.data_set.data_type.name
        )

        assert_that(resp.status_code, equal_to(200))

        resp_json = json.loads(resp.content)

        assert_that(resp_json, has_key('id'))
        assert_that(resp_json['slug'], equal_to("some-collector"))
        assert_that(resp_json['name'], equal_to(expected_collector_name))
        assert_that(resp_json['data_source']['name'],
                    equal_to(self.data_source.name))
        assert_that(resp_json['data_set']['data_type'],
                    equal_to(self.data_set.data_type.name))
        assert_that(resp_json['data_set']['data_group'],
                    equal_to(self.data_set.data_group.name))

    def test_post_from_unauthorised_client_fails(self):
        collector = {
            "slug": "some-collector",
            "type_id": self.collector_type.id,
            "data_source": self.data_source.id,
            "data_set": {
                "data_type": self.data_set.data_type.name,
                "data_group": self.data_set.data_group.name
            }
        }
        resp = self.client.post(
            '/collector',
            data=to_json(collector),
            content_type='application/json')

        assert_that(resp.status_code, equal_to(403))

    def test_post_with_non_existent_data_source_fails(self):
        data_source = uuid.UUID('01234a12-1234-1234-5b6c-0de12e3a4f15')
        collector = {
            "slug": "some-collector",
            "type_id": self.collector_type.id,
            "data_source_id": data_source,
            "data_set": {
                "data_type": self.data_set.data_type.name,
                "data_group": self.data_set.data_group.name
            }
        }
        response = self.client.post(
            '/collector',
            data=to_json(collector),
            HTTP_AUTHORIZATION='Bearer development-oauth-access-token',
            content_type='application/json')

        assert_that(response.status_code, equal_to(400))

        resp_json = json.loads(response.content)
        assert_that(resp_json['message'], equal_to(
            "No data source with id '{}' found".format(data_source)))

    def test_post_with_non_existent_collector_type_fails(self):
        collector_type = uuid.UUID('01234a12-1234-1234-5b6c-0de12e3a4f15')
        collector = {
            "slug": "some-collector",
            "type_id": collector_type,
            "data_source_id": self.data_source.id,
            "data_set": {
                "data_type": self.data_set.data_type.name,
                "data_group": self.data_set.data_group.name
            }
        }
        response = self.client.post(
            '/collector',
            data=to_json(collector),
            HTTP_AUTHORIZATION='Bearer development-oauth-access-token',
            content_type='application/json')

        assert_that(response.status_code, equal_to(400))

        resp_json = json.loads(response.content)
        assert_that(resp_json['message'], equal_to(
            "No collector type with id '{}' found".format(collector_type)))

    def test_post_with_non_existent_data_set_fails(self):
        data_set = {
            "data_type": "some-data-type",
            "data_group": "some-data-group"
        }
        collector = {
            "slug": "some-collector",
            "type_id": self.collector_type.id,
            "data_source_id": self.data_source.id,
            "data_set": data_set
        }
        response = self.client.post(
            '/collector',
            data=to_json(collector),
            HTTP_AUTHORIZATION='Bearer development-oauth-access-token',
            content_type='application/json')

        assert_that(response.status_code, equal_to(400))

        resp_json = json.loads(response.content)
        assert_that(resp_json['message'], equal_to(
            "No data set with data group '{}' and data type '{}' found"
            "".format(data_set['data_group'], data_set['data_type'])))

    @with_govuk_signon(permissions=['collector'])
    def test_get_404_when_user_not_in_ownership_array(self):
        collector = CollectorFactory()
        user, _ = User.objects.get_or_create(
            email='not_correct_user.lastname@gov.uk')
        collector.owners.add(user)

        resp = self.client.get(
            '/collector/{}'.format(collector.slug),
            HTTP_AUTHORIZATION='Bearer correct-token')

        assert_that(resp.status_code, equal_to(404))

    @with_govuk_signon(permissions=['collector'])
    def test_get_404_when_user_not_in_data_source_ownership_array(self):
        data_source = DataSourceFactory()
        data_source_user, _ = User.objects.get_or_create(
            email='data_source_user.lastname@gov.uk')
        data_source.owners.add(data_source_user)

        collector = CollectorFactory(data_source=data_source)
        collector_user, _ = User.objects.get_or_create(
            email='some.user@digital.cabinet-office.gov.uk')
        collector.owners.add(collector_user)

        resp = self.client.get(
            '/collector/{}'.format(collector.slug),
            HTTP_AUTHORIZATION='Bearer correct-token')

        assert_that(resp.status_code, equal_to(404))

    @with_govuk_signon(permissions=['collector'])
    def test_get_404_when_user_not_in_data_set_ownership_array(self):
        data_set = DataSetFactory()
        data_set_user, _ = User.objects.get_or_create(
            email='data_source_user.lastname@gov.uk')
        data_set.owners.add(data_set_user)

        collector = CollectorFactory(data_set=data_set)
        collector_user, _ = User.objects.get_or_create(
            email='some.user@digital.cabinet-office.gov.uk')
        collector.owners.add(collector_user)

        resp = self.client.get(
            '/collector/{}'.format(collector.slug),
            HTTP_AUTHORIZATION='Bearer correct-token')

        assert_that(resp.status_code, equal_to(404))

    def test_put(self):
        collector = CollectorFactory()

        data_source = DataSourceFactory(provider=collector.type.provider)

        collector_update = {
            "slug": collector.slug,
            "type_id": collector.type.id,
            "data_source_id": data_source.id,
            "data_set": {
                "data_type": collector.data_set.data_type.name,
                "data_group": collector.data_set.data_group.name
            }
        }

        response = self.client.put(
            '/collector/{}'.format(collector.slug),
            data=to_json(collector_update),
            HTTP_AUTHORIZATION='Bearer development-oauth-access-token',
            content_type='application/json')

        assert_that(response.status_code, equal_to(200))
        resp_json = json.loads(response.content)
        assert_that(resp_json['data_source']['name'],
                    equal_to(data_source.name))

    @with_govuk_signon(permissions=['collector'])
    def test_put_404_when_user_not_in_data_set_ownership_array(self):

        collector = CollectorFactory()
        collector_user, _ = User.objects.get_or_create(
            email='some.user@digital.cabinet-office.gov.uk')
        collector.owners.add(collector_user)

        data_set = DataSetFactory()
        data_set_user, _ = User.objects.get_or_create(
            email='data_source_user.lastname@gov.uk')
        data_set.owners.add(data_set_user)

        collector_update = {
            "slug": collector.slug,
            "type_id": collector.type.id,
            "data_source_id": collector.data_source.id,
            "data_set": {
                "data_type": data_set.data_type.name,
                "data_group": data_set.data_group.name
            }
        }

        response = self.client.put(
            '/collector/{}'.format(collector.slug),
            data=to_json(collector_update),
            HTTP_AUTHORIZATION='Bearer correct-token',
            content_type='application/json')

        assert_that(response.status_code, equal_to(404))

    @with_govuk_signon(permissions=['collector'])
    def test_put_404_when_user_not_in_data_source_ownership_array(self):
        collector = CollectorFactory()
        collector_user, _ = User.objects.get_or_create(
            email='some.user@digital.cabinet-office.gov.uk')
        collector.owners.add(collector_user)

        data_source = DataSourceFactory()
        data_source_user, _ = User.objects.get_or_create(
            email='data_source_user.lastname@gov.uk')
        data_source.owners.add(data_source_user)

        collector_update = {
            "slug": collector.slug,
            "type_id": collector.type.id,
            "data_source_id": data_source.id,
            "data_set": {
                "data_type": collector.data_set.data_type.name,
                "data_group": collector.data_set.data_group.name
            }
        }

        response = self.client.put(
            '/collector/{}'.format(collector.slug),
            data=to_json(collector_update),
            HTTP_AUTHORIZATION='Bearer correct-token',
            content_type='application/json')

        assert_that(response.status_code, equal_to(404))


@patch('stagecraft.apps.collectors.views.run_collector_task')
class RunCollectorTest(TestCase):

    @with_govuk_signon(permissions=['admin'])
    def test_run_collector(self, run_collector_mock):
        collector = CollectorFactory()
        response = self.client.post(
            '/collector-run/{}'.format(collector.slug),
            HTTP_AUTHORIZATION='Bearer correct-token',
            content_type='application/json'
        )
        assert_that(response.status_code, equal_to(200))
        run_collector_mock.delay.assert_called_with(collector.slug)

    @with_govuk_signon(permissions=['collector'])
    def test_returns_404_if_collector_does_not_exist(self, run_collector_mock):
        response = self.client.post(
            '/collector-run/{}'.format('non-existent-slug'),
            HTTP_AUTHORIZATION='Bearer correct-token',
            content_type='application/json'
        )
        assert_that(response.status_code, equal_to(404))

    @with_govuk_signon(permissions=['collector'])
    def test_returns_404_if_user_not_owner(self, run_collector_mock):
        collector = CollectorFactory()
        user, _ = User.objects.get_or_create(
            email='not_correct_user.lastname@gov.uk')
        collector.owners.add(user)
        response = self.client.post(
            '/collector-run/{}'.format(collector.slug),
            HTTP_AUTHORIZATION='Bearer correct-token',
            content_type='application/json'
        )
        assert_that(response.status_code, equal_to(404))

    @with_govuk_signon(permissions=['signin'])
    def test_requires_collectors_permission(self, run_collector_mock):
        collector = CollectorFactory()
        response = self.client.post(
            '/collector-run/{}'.format(collector.slug),
            HTTP_AUTHORIZATION='Bearer correct-token',
            content_type='application/json'
        )
        assert_that(response.status_code, equal_to(403))

    @with_govuk_signon(permissions=['admin'])
    def test_run_collector_with_start_and_end_dates(self, run_collector_mock):
        collector = CollectorFactory()
        start_date = datetime(2015, 8, 1).strftime('%Y-%m-%d')
        end_date = datetime(2015, 8, 9).strftime('%Y-%m-%d')

        response = self.client.post(
            '/collector-run/{}?start_at={}&end_at={}'.format(
                collector.slug, start_date, end_date),
            HTTP_AUTHORIZATION='Bearer correct-token',
            content_type='application/json'
        )
        assert_that(response.status_code, equal_to(200))
        run_collector_mock.delay.assert_called_with(
            collector.slug, "2015-08-01", "2015-08-09")

    @with_govuk_signon(permissions=['admin'])
    def test_400_if_only_start_date(self, run_collector_mock):
        collector = CollectorFactory()
        start_date = datetime(2015, 8, 1).strftime('%Y-%m-%d')

        response = self.client.post(
            '/collector-run/{}?start_at={}'.format(
                collector.slug, start_date),
            HTTP_AUTHORIZATION='Bearer correct-token',
            content_type='application/json'
        )
        assert_that(response.status_code, equal_to(400))

    @with_govuk_signon(permissions=['admin'])
    def test_400_if_only_end_date(self, run_collector_mock):
        collector = CollectorFactory()
        end_date = datetime(2015, 8, 9).strftime('%Y-%m-%d')

        response = self.client.post(
            '/collector-run/{}?end_at={}'.format(
                collector.slug, end_date),
            HTTP_AUTHORIZATION='Bearer correct-token',
            content_type='application/json'
        )
        assert_that(response.status_code, equal_to(400))
