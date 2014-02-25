from __future__ import unicode_literals

import json
import reversion

from optparse import make_option

from django.db import transaction
from django.core.management.base import BaseCommand, CommandError

from stagecraft.apps.datasets.models import DataSet, DataGroup, DataType
from stagecraft.libs.backdrop_client import backdrop_connection_disabled


class Command(BaseCommand):
    option_list = BaseCommand.option_list + (
        make_option(
            '--without-backdrop',
            action='store_true',
            dest='without_backdrop',
            default=False,
            help="Don't attempt to create collections in Backdrop"),)

    args = '<backdrop_buckets.json>'
    help = ("Imports a backdrop JSON dump of the ``buckets`` collection. See "
            "the related ``dump_bucket_metadata.py`` tool in Backdrop.")

    def handle(self, *args, **options):
        if not len(args):
            raise CommandError(
                "No buckets.json file specified, see --help")

        for filename in args:
            self.stdout.write("Opening {}".format(filename))

            if options['without_backdrop']:
                self.stdout.write("Disabling Backdrop")
                with backdrop_connection_disabled():
                    self.load_data_sets_from_buckets_json(filename)
            else:
                self.stdout.write("Not disabling Backdrop")
                self.load_data_sets_from_buckets_json(filename)

            self.stdout.write('Finished')

    def load_data_sets_from_buckets_json(self, filename):
        with open(filename, 'r') as f:
            buckets = json.loads(f.read())
            for bucket in buckets:
                self.save_data_set(bucket)

    def save_data_set(self, bucket):
        name = bucket['name']
        if DataSet.objects.filter(name=name).exists():
            self.stdout.write("SKIPPING {} - already exists".format(name))
            return

        with transaction.atomic(), reversion.create_revision():
            #self.stdout.write("Creating DataSet from:\n{}".format(bucket))
            DataSet.objects.create(
                name=name,
                data_group=self.get_or_create(DataGroup, bucket['data_group']),
                data_type=self.get_or_create(DataType, bucket['data_type']),
                raw_queries_allowed=bucket['raw_queries_allowed'],
                bearer_token=bucket['bearer_token'],
                upload_format=bucket['upload_format'] or '',
                upload_filters=self.comma_separate(bucket['upload_filters']),
                auto_ids=self.comma_separate(bucket['auto_ids']),
                queryable=bucket['queryable'],
                realtime=bucket['realtime'],
                capped_size=self.convert_capped_size(bucket['capped_size']),
                max_age_expected=bucket['max_age_expected'])

            self.stdout.write("Created {}".format(name))

    def comma_separate(self, list_of_strings):
        if not list_of_strings:
            return ''
        else:
            return ','.join(list_of_strings) or ''

    def get_or_create(self, model_class, name):
        (obj, new) = model_class.objects.get_or_create(name=name)
        if new:
            self.stdout.write("Created {} called '{}'".format(
                type(model_class), name))
        return obj

    def convert_capped_size(self, size):
        return int(size) if size else 0
