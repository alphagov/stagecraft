from django.test import TestCase
from hamcrest import assert_that, equal_to
from mock import patch, ANY
from stagecraft.apps.collectors.libs.ga import CredentialStorage
from stagecraft.apps.collectors.models import CollectorType
from stagecraft.apps.collectors.tasks import (
    run_collector,
    run_collectors_by_type
)
from stagecraft.apps.collectors.tests.factories import (
    CollectorFactory,
    DataSourceFactory
)
import json


class TestCeleryTasks(TestCase):

    @patch("performanceplatform.collector.ga.main")
    def test_run_collector(self, mock_ga_collector):
        # Collector Types are created through a migration and should exist in
        # the test database.
        collector_type = CollectorType.objects.get(slug="ga")
        collector = CollectorFactory(type=collector_type)

        run_collector(collector.slug, "2015-08-01", "2015-08-08")

        assert_that(mock_ga_collector.called, equal_to(True))

    @patch("stagecraft.apps.collectors.tasks.group")
    def test_run_collectors_by_type(self, mock_group):
        collector_type = CollectorType.objects.get(slug='ga')
        CollectorFactory(type=collector_type)
        CollectorFactory(type=collector_type)
        another_collector_type = CollectorType.objects.get(slug='gcloud')
        CollectorFactory(type=another_collector_type)

        run_collectors_by_type(
            collector_type.slug, another_collector_type.slug)

        assert_that(mock_group.call_count, equal_to(2))

    @patch("performanceplatform.collector.ga.main")
    def test_run_collector_with_no_start_and_end_dates(
            self, mock_ga_collector):
        # Collector Types are created through a migration and should exist in
        # the test database.
        collector_type = CollectorType.objects.get(slug="ga")
        collector = CollectorFactory(type=collector_type)

        run_collector(collector.slug)

        assert_that(mock_ga_collector.called, equal_to(True))

    @patch("performanceplatform.collector.ga.main")
    @patch("stagecraft.apps.collectors.tasks.CredentialStorage")
    def test_run_collector_with_oauth2_credentials(
            self, mock_credential_storage_class, mock_ga_collector):

        def credentials():
            return json.dumps({
                "CLIENT_SECRETS": {
                    "installed": {
                        "auth_uri": "accounts.foo.com/o/oauth2/auth",
                        "client_secret": "a client secret",
                        "token_uri": "accounts.foo.com/o/oauth2/token",
                        "client_email": "",
                        "redirect_uris": ["urn:ietf:wg:oauth:2.0:oob", "oob"],
                        "client_x509_cert_url": "",
                        "client_id": "a client id",
                        "auth_provider_x509_cert_url": "foo.com/oauth2/certs"
                    }
                },
                "OAUTH2_CREDENTIALS": {
                    "_module": "oauth2client.client",
                    "_class": "OAuth2Credentials",
                    "access_token": "an access token",
                    "token_uri": "accounts.foo.com/o/oauth2/token",
                    "invalid": False,
                    "client_id": "a client id",
                    "id_token": None,
                    "client_secret": "a client secret",
                    "token_expiry": "2015-09-30T14:54:59Z",
                    "refresh_token": "a refresh token",
                    "user_agent": None
                }
            })

        # Collector Types are created through a migration and should exist in
        # the test database.
        collector_type = CollectorType.objects.get(slug="ga")
        data_source = DataSourceFactory(credentials=credentials())
        collector = CollectorFactory(
            type=collector_type, data_source=data_source)
        mock_storage_object = CredentialStorage(data_source)
        mock_credential_storage_class.return_value = mock_storage_object
        run_collector(collector.slug)
        expected_secret = json.loads(credentials()).get("CLIENT_SECRETS")
        expected_credentials = {
            "CLIENT_SECRETS": expected_secret,
            "OAUTH2_CREDENTIALS": mock_storage_object
        }
        mock_ga_collector.assert_called_with(
            expected_credentials, ANY, ANY, ANY, ANY, ANY)
