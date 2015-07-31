from __future__ import print_function

import json
import os

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from stagecraft.apps.collectors.models import CollectorType


class Command(BaseCommand):
    args = '<schemas_dir>'
    help = 'Import schemas for collectors app'

    def handle(self, *args, **options):
        if not len(args):
            raise CommandError('No schema directory given')

        collector_type_schemas = self.load_schemas(
            os.path.join(args[0], 'collector-type'),
        )

        with transaction.atomic():
            for slug, schemas in collector_type_schemas.items():
                collector_type = CollectorType.objects.get(slug=slug)
                collector_type.query_schema = schemas['query.json']
                collector_type.options_schema = schemas['options.json']

                print('Validating and saving type {}'.format(slug))

                validation = collector_type.validate()
                if validation is not None:
                    raise CommandError(
                        '{}: {}'.format(slug, validation)
                    )

                collector_type.save()

                print('Validating all collectors of type {}'.format(slug))

                for collector in collector_type.collector_set.all():
                    validation = collector.validate()
                    if validation is not None:
                        raise CommandError(
                            '{}: {}'.format(collector.slug, validation)
                        )

    def load_schemas(self, path):
        schemas = {}
        for schema_file in os.listdir(path):
            schema_path = os.path.join(path, schema_file)

            if os.path.isdir(schema_path):
                schema = self.load_schemas(schema_path)
            else:
                with open(schema_path, 'r') as schema_fd:
                    try:
                        schema = json.load(schema_fd)
                    except ValueError as err:
                        print('Error parsing {}: {}'.format(path, err))
                        schema = None

            schemas[schema_file] = schema

        return schemas
