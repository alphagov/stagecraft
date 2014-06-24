from jsonschema.validators import validator_for

from stagecraft.libs.schemas.schemas import get_defined_schemas, get_schema


def test_data_type_schemas_are_valid():
    for data_type in get_defined_schemas('data-types'):
        yield check_data_type_schema_is_valid, data_type


def check_data_type_schema_is_valid(data_type):
    schema = get_schema('example', data_type)
    validator_for(schema).check_schema(schema)
