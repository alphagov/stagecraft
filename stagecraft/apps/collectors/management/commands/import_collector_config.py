from __future__ import print_function

import json
import functools
import hashlib
import os

from collections import defaultdict

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from stagecraft.apps.collectors.models import (
    Collector, CollectorType, DataSource, Provider
)
from stagecraft.apps.datasets.models import DataSet


entrypoint_information = {
    'performanceplatform.collector.ga': {
        'credentials': 'ga-performanceplatform',
        'repeat': 'daily',
    },
    'performanceplatform.collector.webtrends.reports': {
        'credentials': {
            'nas-applications': 'webtrends-national-apprenticeship-scheme',
            'nhs-choices': 'webtrends-nhs-choices',
        },
        'repeat': 'daily',
    },
    'performanceplatform.collector.webtrends.keymetrics': {
        'credentials': {
            'nas-applications': 'webtrends-national-apprenticeship-scheme',
            'nhs-choices': 'webtrends-nhs-choices',
        },
        'repeat': 'hourly',
    },
    'performanceplatform.collector.ga.trending': {
        'credentials': 'ga-performanceplatform',
        'repeat': 'daily',
    },
    'performanceplatform.collector.ga.contrib.content.table': {
        'credentials': 'ga-performanceplatform',
        'repeat': 'daily',
    },
    'performanceplatform.collector.ga.realtime': {
        'credentials': 'ga-performanceplatform',
        'repeat': '2minute',
    },
    'performanceplatform.collector.pingdom': {
        'credentials': 'pingdom-performanceplatform',
        'repeat': 'hourly',
    },
    'performanceplatform.collector.piwik.core': {
        'credentials': 'piwik-fco',
        'repeat': 'daily',
    },
    'performanceplatform.collector.piwik.realtime': {
        'credentials': 'piwik-fco',
        'repeat': '2minute',
    },
    'performanceplatform.collector.gcloud': {
        'credentials': 'gcloud',
        'repeat': 'hourly',
    },
}


class Command(BaseCommand):

    '''
    Usage: python manage.py import_collector_config <config_dir>

    config_dir: do include the queries directory in config path.
    '''

    args = '<config_dir>'
    help = 'Import collector configuration from repo.'

    def handle(self, *args, **options):
        if not len(args):
            raise CommandError('No config directory given')

        queries_dir = os.path.join(args[0], 'queries')
        config = self.load_config(queries_dir)
        by_slug = self.sort_by_slug(config)

        with transaction.atomic():
            self.delete_generated_collectors()
            self.import_config(by_slug)

    def delete_generated_collectors(self):
        Collector.objects.filter(slug__iregex=r'^.+-[0-9a-f]{8}$').delete()

    def import_config(self, by_slug):
        for slug, config in by_slug.items():
            data_group = config['data-set']['data-group']
            try:
                data_set = DataSet.objects.get(
                    data_group__name=data_group,
                    data_type__name=config['data-set']['data-type'],
                )
            except DataSet.DoesNotExist:
                data_set = None

            collector_type = CollectorType.objects.get(
                entry_point=config['entrypoint'],
            )

            query_info = entrypoint_information[config['entrypoint']]

            data_source_slug = query_info['credentials']
            if type(data_source_slug) == dict:
                data_source_slug = data_source_slug[data_group]

            data_source = DataSource.objects.get(
                slug=data_source_slug,
            )

            if data_set:
                collector = Collector(
                    slug=slug,
                    type=collector_type,
                    data_source=data_source,
                    data_set=data_set,
                    query=config['query'],
                    options=config['options'],
                )

                validation = collector.validate()
                if validation is not None:
                    raise CommandError(
                        '{}: {}'.format(slug, validation)
                    )

                collector.save()

    def sort_by_slug(self, configs):
        by_slug = defaultdict(list)
        for config in configs:
            slug = '{}-{}-{}'.format(
                config['data-set']['data-group'],
                config['data-set']['data-type'],
                self.hash_dicts(config['query'], config['options'])
            )
            by_slug[slug].append(config)

        for slug, configs in by_slug.items():
            if len(configs) > 1:
                raise CommandError(
                    '{} has more than one config'.format(slug)
                )
            by_slug[slug] = configs[0]

        return by_slug

    def hash_dicts(self, *dicts):
        dicts_as_strings = map(json.dumps, dicts)
        return hashlib \
            .sha512(''.join(dicts_as_strings)) \
            .hexdigest()[:8]

    def load_config(self, directory):
        configs = []

        for root, dirs, files in os.walk(directory):
            for config_file in files:
                config = self.parse_config(
                    os.path.join(root, config_file)
                )

                if config is not None:
                    configs.append(config)

        return configs

    def parse_config(self, path):
        with open(path, 'r') as config_file:
            try:
                config = json.load(config_file)
            except ValueError as err:
                print('Error parsing {}: {}'.format(path, err))
                config = None

        return config
