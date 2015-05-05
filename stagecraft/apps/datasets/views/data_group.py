from stagecraft.libs.views.resource import ResourceView
from stagecraft.apps.datasets.models import DataGroup
from django.utils.decorators import method_decorator
from django.views.decorators.cache import never_cache
from django.views.decorators.vary import vary_on_headers
from stagecraft.libs.authorization.http import permission_required


class DataGroupView(ResourceView):
    model = DataGroup
    list_filters = {
        "name": "name"
    }

    @method_decorator(permission_required('signin'))
    @method_decorator(never_cache)
    @method_decorator(vary_on_headers('Authorization'))
    def get(self, user, request, **kwargs):
        kwargs['user'] = user
        return super(DataGroupView, self).get(
            request,
            **kwargs)

    @method_decorator(permission_required('signin'))
    @method_decorator(never_cache)
    @method_decorator(vary_on_headers('Authorization'))
    def post(self, user, request, **kwargs):
        return super(DataGroupView, self).post(user, request, **kwargs)

    def update_model(self, model, model_json, request):
        for (key, value) in model_json.items():
            setattr(model, key, value)

    @staticmethod
    def serialize(model):
        # I know this should be properly extracted out but for now.
        return model.serialize()