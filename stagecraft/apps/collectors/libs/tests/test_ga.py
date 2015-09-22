from django.test import TestCase
from hamcrest import assert_that, equal_to, is_, instance_of
from stagecraft.apps.collectors.libs.ga import CredentialStorage
from stagecraft.apps.collectors.tests.factories import DataSourceFactory
from oauth2client.client import OAuth2Credentials
import json


class CredentialStorageTestCase(TestCase):

    def oauth2_credentials(self):
        return {
            "_module": "oauth2client.client",
            "_class": "OAuth2Credentials",
            "access_token": "a token",
            "token_uri": "accounts.foo.com/o/oauth2/token",
            "invalid": False,
            "client_id": "uuid",
            "id_token": None,
            "client_secret": "a secret",
            "token_expiry": "2015-09-30T14:54:59Z",
            "refresh_token": "a token",
            "user_agent": None
        }

    def credentials(self):
        return json.dumps({
            "CLIENT_SECRETS": {
                "installed": {
                    "auth_uri": "accounts.foo.com/o/oauth2/auth",
                    "client_secret": "a secret",
                    "token_uri": "accounts.foo.com/o/oauth2/token",
                    "client_email": "",
                    "redirect_uris": ["urn:ietf:wg:oauth:2.0:oob", "oob"],
                    "client_x509_cert_url": "",
                    "client_id": "uuid",
                    "auth_provider_x509_cert_url": "foo.com/oauth2/certs"
                }
            },
            "OAUTH2_CREDENTIALS": self.oauth2_credentials()
        })

    def test_is_a_bearer_of_oauth2_credentials_for_a_data_source(self):
        model = DataSourceFactory(credentials=self.credentials())
        storage = CredentialStorage(model)
        oauth2_credentials = storage.locked_get()

        assert_that(oauth2_credentials, is_(instance_of(OAuth2Credentials)))
        assert_that(oauth2_credentials.refresh_token, equal_to('a token'))

    def test_is_a_modifier_of_oauth2_credentials_for_a_data_source(self):
        model = DataSourceFactory(credentials=self.credentials())
        storage = CredentialStorage(model)
        oauth2_credentials = self.oauth2_credentials()
        oauth2_credentials['refresh_token'] = 'new token'
        storage.locked_put(
            OAuth2Credentials.new_from_json(json.dumps(oauth2_credentials)))
        storage = storage.locked_get()

        assert_that(storage.refresh_token, equal_to('new token'))
