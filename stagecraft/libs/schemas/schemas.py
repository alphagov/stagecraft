import logging
logger = logging.getLogger(__name__)

from django.conf import settings
from json import loads as json_loads
from os import path

SCHEMA_PATH = 'stagecraft/apps/datasets/schemas/'
schema_root = path.join(
    settings.BASE_DIR,
    SCHEMA_PATH
)
DEFINED_SCHEMAS = {
    'data_types': ['monitoring']
}


def load_json_schema(schema_name):

    if not ".json" in schema_name:
        schema_name = schema_name + ".json"

    schema_path = path.join(schema_root, schema_name)

    with open(schema_path) as schema_file:
        return json_loads(schema_file.read())


def get_schema(self):
    schema = {
        "description": "Schema for {}".format(self.name),
        "definitions": {
            "_timestamp": load_json_schema('timestamp.json'),
        },
        "allOf": [{"$ref": "#/definitions/timestamp"}]
    }

    data_type = self.data_type.name
    if data_type in DEFINED_SCHEMAS['data_types']:
        try:
            schema['definitions'][data_type] = load_json_schema(
                self.data_type.name)

            schema["allOf"].append(
                {"$ref": "#/definitions/{}".format(data_type)}
            )
        except IOError as e:
            logger.exception(e)

    return schema
