import logging

from stagecraft.apps.users.models import User
from stagecraft.libs.views.resource import ResourceView

logger = logging.getLogger(__name__)


class UserView(ResourceView):

    model = User

    id_fields = {
        'email': '[\w.%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,4}',
    }

    schema = {
        "$schema": "http://json-schema.org/schema#",
        "type": "object",
        "properties": {
            "email": {
                "type": "string"
            }
        },
        "required": ["email"],
        "additionalProperties": False,
    }

    list_filters = {
        'email': 'email__iexact',
    }

    def update_model(self, model, model_json, request):
        model.email = model_json['email']

    @staticmethod
    def serialize(model):
        return model.serialize()
