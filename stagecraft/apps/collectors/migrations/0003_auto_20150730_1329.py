# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations

providers = {
    'ga': {
        'name': 'Google Analytics',
        'data_sources': {
            'ga-performanceplatform': {
                'name': 'GA Performance Platform',
            },
        },
        'collector_types': {
            'ga': {
                'name': 'Google Analytics',
                'entry_point': 'performanceplatform.collector.ga',
            },
            'ga-realtime': {
                'name': 'Google Analytics Realtime',
                'entry_point': 'performanceplatform.collector.ga.realtime',
            },
            'ga-trending': {
                'name': 'Google Analytics Trending',
                'entry_point': 'performanceplatform.collector.ga.trending',
            },
            'ga-contrib-content-table': {
                'name': 'Google Analytics Content Table',
                'entry_point': 'performanceplatform.collector.ga.contrib.content.table',
            }
        }
    },
    'pingdom': {
        'name': 'Pingdom',
        'data_sources': {
            'pingdom-performanceplatform': {
                'name': 'Pingdom Performance Platform',
            },
        },
        'collector_types':{
            'pingdom': {
                'name': 'Pingdom',
                'entry_point': 'performanceplatform.collector.pingdom',
            },
        },
    },
    'webtrends': {
        'name': 'Webtrends',
        'data_sources': {
            'webtrends-nhs-choices': {
                'name': 'Webtrends NHS Choices',
            },
            'webtrends-national-apprenticeship-scheme': {
                'name': 'Webtrends National Apprenticeships Scheme',
            },
        },
        'collector_types':{
            'webtrends-reports': {
                'name': 'Webtrends Reports',
                'entry_point': 'performanceplatform.collector.webtrends.reports',
            },
            'webtrends-keymetrics': {
                'name': 'Webtrends Keymetrics',
                'entry_point': 'performanceplatform.collector.webtrends.keymetrics',
            },
        },
    },
    'piwik': {
        'name': 'Piwik',
        'data_sources': {
            'piwik-fco': {
                'name': 'Piwik FCO',
            },
            'piwik-verify': {
                'name': 'Piwik Verify',
            },
        },
        'collector_types':{
            'piwik-core': {
                'name': 'Piwik',
                'entry_point': 'performanceplatform.collector.piwik.core',
            },
            'piwik-realtime': {
                'name': 'Piwik Realtime',
                'entry_point': 'performanceplatform.collector.piwik.realtime',
            },
        },
    },
    'gcloud': {
        'name': 'gcloud',
        'data_sources': {
            'gcloud': {
                'name': 'GCloud',
            },
        },
        'collector_types':{
            'gcloud': {
                'name': 'G-Cloud',
                'entry_point': 'performanceplatform.collector.gcloud',
            },
        },
    },
}


def add_base_data(apps, schema_editor):
    Provider = apps.get_model('collectors', 'Provider')
    DataSource = apps.get_model('collectors', 'DataSource')
    CollectorType = apps.get_model('collectors', 'CollectorType')

    for provider_slug, provider_def in providers.items():
        provider = Provider.objects.create(
            slug=provider_slug,
            name=provider_def['name'],
        )

        for data_source_slug, data_source_def in provider_def['data_sources'].items():
            data_source = DataSource.objects.create(
                slug=data_source_slug,
                name=data_source_def['name'],
                provider=provider,
            )

        for collector_type_slug, collector_type_def in provider_def['collector_types'].items():
            collector_type = CollectorType.objects.create(
                slug=collector_type_slug,
                name=collector_type_def['name'],
                provider=provider,
                entry_point=collector_type_def['entry_point'],
            )


def remove_base_data(apps, schema_editor):
    Provider = apps.get_model('collectors', 'Provider')
    DataSource = apps.get_model('collectors', 'DataSource')
    CollectorType = apps.get_model('collectors', 'CollectorType')

    for provider_slug, provider_def in providers.items():
        Provider.objects.filter(slug=provider_slug).delete()

        for data_source_slug, _ in provider_def['data_sources'].items():
            DataSource.objects.filter(slug=data_source_slug).delete()

        for collector_type_slug, _ in provider_def['collector_types'].items():
            CollectorType.objects.filter(slug=collector_type_slug).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('collectors', '0002_auto_20150730_1328'),
    ]

    operations = [
        migrations.RunPython(add_base_data, remove_base_data)
    ]
