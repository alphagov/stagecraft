from oauth2client.client import Storage, OAuth2Credentials
import json


class CredentialStorage(Storage):

    def __init__(self, model_class):
        self.model = model_class

    def locked_get(self):
        """ Make an OAuth 2.0 credentials object from
        a JSON description of it stored in a model's credentials attribute.

        Returns:
        oauth2client.OAuth2Credentials
        """

        db_credentials = json.loads(self.model.credentials)
        oauth2_credentials = OAuth2Credentials.new_from_json(
            json.dumps(db_credentials.get('OAUTH2_CREDENTIALS')))
        oauth2_credentials.set_store(self)
        return oauth2_credentials

    def locked_put(self, oauth2_credentials):
        """ Update a model's credentials attribute with
        a JSON representation of an OAuth 2.0 credentials object.
        """

        db_credentials = json.loads(self.model.credentials)
        db_credentials['OAUTH2_CREDENTIALS'] = json.loads(
            oauth2_credentials.to_json())

        self.model.credentials = json.dumps(db_credentials)
        self.model.save()
