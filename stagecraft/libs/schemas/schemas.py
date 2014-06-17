from django.conf import settings
from json import loads as json_loads
from os import path


def get_schema(self):

    schema_path = 'stagecraft/apps/datasets/schemas/timestamp.json'

    if(self.data_type == "monitoring"):
        schema_path = 'stagecraft/apps/datasets/schemas/monitoring.json'

    schema_root = path.join(
        settings.BASE_DIR,
        schema_path
    )

    with open(schema_root) as f:
        schema = json_loads(f.read())

    return schema
