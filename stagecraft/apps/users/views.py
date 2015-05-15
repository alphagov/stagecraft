from collections import OrderedDict
import logging

from django.utils.decorators import method_decorator
from django.views.decorators.cache import never_cache
from django.views.decorators.vary import vary_on_headers

from stagecraft.apps.users.models import User
from stagecraft.libs.authorization.http import permission_required
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
            },
            "data_sets": {
                "type": "object"
            }

        },
        "required": ["email"],
        "additionalProperties": False,
    }

    list_filters = {
        'email': 'email__iexact',
    }

    permissions = {
        'get': 'user',
        'post': 'user',
        'put': 'user',
    }

    @never_cache
    @vary_on_headers('Authorization')
    def get(self, request, *args, **kwargs):
        return super(UserView, self).get(request, **kwargs)

    @never_cache
    @vary_on_headers('Authorization')
    def post(self, request, **kwargs):
        return super(UserView, self).post(request, **kwargs)

    @never_cache
    @vary_on_headers('Authorization')
    def put(self, request, **kwargs):
        return super(UserView, self).put(request, **kwargs)

    def update_model(self, model, model_json, request):
        model.email = model_json['email']

    @staticmethod
    def serialize(model):
        def get_names(data_sets):
            return [data_set.name for data_set in data_sets]

        return OrderedDict([
            ('email',     model.email),
            ('data_sets', get_names(model.data_sets.all()))
        ])
