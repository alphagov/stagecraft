from django.conf import settings
from json import loads as json_loads
from os import path


def get_schema():
    schema_root = path.join(
        settings.BASE_DIR,
        'stagecraft/apps/datasets/schemas/timestamp.json'
    )
    with open(schema_root) as f:
        schema = json_loads(f.read())

    return schema
