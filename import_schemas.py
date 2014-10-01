#!/usr/bin/env python
# encoding: utf-8

from stagecraft.apps.dashboards.models.module import(
    ModuleType,
    Module)
import os
import json
import pprint
import jsonschema

# For this script to work correctly, you need to run
# run it like this:
# workon/source the virtualenv
# run export DJANGO_SETTINGS_MODULE=stagecraft.settings.production
# venv/bin/python import.py


def get_schema_for_module_type(name):
    path = os.path.join(
        os.path.dirname(__file__),
        'tools/import_schemas/schema/modules_json/{}_schema.json'.format(name))
    try:
        with open(path, "r") as file:
            schema = file.read()
    except IOError as e:
        print "NO SCHEMA FOUND - USING DEFAULT"
        print name
        print "^NO SCHEMA FOUND - USING DEFAULT"
        path = os.path.join(
            os.path.dirname(__file__),
            'tools/import_schemas/schema/module_schema.json'.format(name))
        with open(path, "r") as file:
            schema = file.read()
    schema_dict = json.loads(schema)
    return schema_dict


def check_module_type_schemas_correct():
    for module_type, new_schema in module_types_with_proper_schemas():
        try:
            module_type.validate_schema()
        except jsonschema.exceptions.SchemaError as e:
            print "==============="
            print module_type.name
            print "==============="
            raise e


def clear_module_type_schemas():
    for module_type, new_schema in module_types_with_proper_schemas():
        update_module_type_schema(module_type, schema={})


def update_module_type_with_correct_schemas():
    for module_type, new_schema in module_types_with_proper_schemas():
        update_module_type_schema(module_type, schema=new_schema)


def update_module_type_schema(module_type, schema={}):
    module_type.schema = schema
    module_type.save()


def module_types_with_proper_schemas():
    module_types_with_proper_schemas = [
        (module_type, get_schema_for_module_type(module_type.name))
        for module_type in ModuleType.objects.all()
    ]
    return module_types_with_proper_schemas


def validate_all_modules():
    for module in Module.objects.all():
        module.validate_options()
        print "======"
        print "{} valid in {} dashboard".format(
            module.slug, module.dashboard.slug)
        print "^====="
    return True


def validate_all_modules_against_files():
    for module in Module.objects.all():
        schema = get_schema_for_module_type(module.type.name)
        jsonschema.validate(module.options, schema)
        print "======"
        print "{} valid in {} dashboard".format(
            module.slug, module.dashboard.slug)
        print "^====="
    return True


if __name__ == '__main__':
    print "Clearing schemas"
    clear_module_type_schemas()
    print "Checking schemas valid"
    check_module_type_schemas_correct()
    print "Checking current modules valid"
    validate_all_modules_against_files()
    print "Setting module type schemas"
    update_module_type_with_correct_schemas()
    print "Checking current modules valid using real method"
    validate_all_modules()
