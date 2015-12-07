import os
import json
import sys
from oauth2client.client import GoogleCredentials


def get_credentials_or_die():
    credentials = GoogleCredentials.get_application_default()
    client_email = credentials.serialization_data['client_email']
    private_key = credentials.serialization_data['private_key']
    return client_email, private_key
