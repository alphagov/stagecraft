import logging
logger = logging.getLogger(__name__)

from django.conf import settings
from json import loads as json_loads
from os import path, listdir

SCHEMA_PATH = 'stagecraft/apps/datasets/schemas/'
schema_root = path.join(
    settings.BASE_DIR,
    SCHEMA_PATH
)


def get_defined_schemas(name=None):
    fetch = path.join(schema_root, name)
    return [s_dir.replace(".json", "") for s_dir in listdir(fetch)]


def load_json_schema(schema_path):

    if ".json" not in schema_path:
        schema_path = schema_path + ".json"

    schema_path = path.join(schema_root, schema_path)

    with open(schema_path) as schema_file:
        return json_loads(schema_file.read())


def get_schema(data_group, data_type):
    schema = {
        "description": "Schema for {}/{}".format(data_group, data_type),
        "definitions": {
            "_timestamp": load_json_schema('timestamp.json'),
        },
        "allOf": [{"$ref": "#/definitions/_timestamp"}]
    }

    if data_type in get_defined_schemas('data-types'):
        try:
            schema['definitions'][data_type] = load_json_schema(
                'data-types/' + data_type)

            schema["allOf"].append(
                {"$ref": "#/definitions/{}".format(data_type)}
            )
        except IOError as e:
            logger.exception(e)

    return schema
