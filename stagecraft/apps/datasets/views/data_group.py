from stagecraft.libs.views.resource import ResourceView
from stagecraft.apps.datasets.models import DataGroup
from stagecraft.libs.views.utils import add_items_to_model


class DataGroupView(ResourceView):
    model = DataGroup
    id_fields = {
        'name': '[\w-]+',
    }
    list_filters = {
        "name": "name"
    }

    def update_model(self, model, model_json, request, parent):
        add_items_to_model(model, model_json)

    @staticmethod
    def serialize(model):
        # I know this should be properly extracted out but for now.
        return model.serialize()
