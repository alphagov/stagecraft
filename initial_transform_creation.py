from __future__ import print_function
from django.conf import settings

from stagecraft.apps.dashboards.models.dashboard import Dashboard
from stagecraft.apps.dashboards.models.module import ModuleType

from stagecraft.apps.datasets.models.data_group import DataGroup
from stagecraft.apps.datasets.models.data_type import DataType
from stagecraft.apps.datasets.models.data_set import DataSet
from stagecraft.apps.transforms.models import TransformType

import json
import requests
import logging

STAGECRAFT_ROOT = settings.APP_ROOT
BACKDROP_ROOT = settings.BACKDROP_URL


def main():

    # force django to bootstrap logging so we can override it
    env = settings.ENV_HOSTNAME
    logger = logging.getLogger('')
    logger.setLevel(logging.DEBUG)
    logger.addHandler(logging.StreamHandler())

    def find_modules(dashboards, module_type):
        dashboards_not_to_process = [
            'prison-visits',
            'lasting-power-of-attorney',
            'accelerated-possession-eviction',
            # we are going to reconfigure this to use transformed datasets
            # manually
            'standard-dashboard',
            # not worth migrating this dashboard as it is a temp playground
            '204051c53890188126a906b64eeebaad',
            # in progress dashboard, doesnt need migrating for now
            'a09f5e63f8ee45f651647aa51149860a',
        ]
        for dashboard in dashboards:
            if dashboard.slug not in dashboards_not_to_process:
                modules = dashboard.module_set.filter(type__name=module_type)
            else:
                modules = []

            for module in modules:
                yield module

    completion_transform_type = {
        "name": "rate",
        "function": "backdrop.transformers.tasks.rate.compute",
        "schema": {
            "$schema": "http://json-schema.org/draft-03/schema#",
            "type": "object",
            "properties": {
                "denominatorMatcher": {
                    "type": "string",
                    "required": True,
                },
                "numeratorMatcher": {
                    "type": "string",
                    "required": True,
                },
                "matchingAttribute": {
                    "type": "string",
                    "required": True,
                },
                "valueAttribute": {
                    "type": "string",
                    "required": True,
                }
            },
            "additionalProperties": False,
        }
    }

    user_satisfaction_transform_type = {
        "name": "user_satisfaction",
        "function": "backdrop.transformers.tasks.user_satisfaction.compute",
        "schema": {}
    }

    transform_types = [
        completion_transform_type,
        user_satisfaction_transform_type
    ]
    transform_metadata = {
        'rate': {
            'module': 'completion_rate',
            'data_type_append': 'rate',
            'query_parameters': {},
            'options': {
                'denominatorMatcher': 'denominator-matcher',
                'numeratorMatcher': 'numerator-matcher',
                'matchingAttribute': 'matching-attribute',
                'valueAttribute': 'value-attribute',
            },
        },
        'user_satisfaction': {
            'module': 'user_satisfaction_graph',
            'data_type_append': 'weekly',
            'query_parameters': {
                'collect': [
                    'rating_1:sum',
                    'rating_2:sum',
                    'rating_3:sum',
                    'rating_4:sum',
                    'rating_5:sum',
                    'total:sum',
                ],
            },
            'options': {},
        }
    }

    headers = {
        'Authorization': 'Bearer {0}'.format(settings.MIGRATION_SIGNON_TOKEN),
        'Content-Type': 'application/json',
    }

    dashboards = Dashboard.objects.all()

    seen_dashboards = {}

    for transform_type in transform_types:
        transform_type_object = TransformType.objects.get(
            name=transform_type['name'])
        transform_type_id = str(transform_type_object.id)

        metadata = transform_metadata[transform_type['name']]
        for module in find_modules(dashboards, metadata['module']):
            data_group_name = module.data_set.data_group.name
            new_data_group_name = data_group_name
            data_type_name = module.data_set.data_type.name

            if metadata['module'] == 'completion_rate':
                new_data_type_name = module.slug
                dashboards_using_same_datasets = [
                    'book-practical-driving-test',
                    'tax-disc',
                    'sorn',
                    'change-practical-driving-test',
                ]
                if module.dashboard.slug in dashboards_using_same_datasets:
                    new_data_group_name = data_group_name + '-{}'.format(
                        module.dashboard.slug)
                logger.debug(
                    'completion_rate module'
                    'so data type name is module slug: {}'.format(
                        new_data_type_name))
            elif metadata['module'] == 'user_satisfaction_graph':
                new_data_type_name = 'user-satisfaction-score'
                logger.debug(
                    'user_satisfaction_graph module'
                    'so data type name is hardcoded: {}'.format(
                        new_data_type_name))
            else:
                new_data_type_name = data_type_name \
                    + '-' + metadata['data_type_append']
                logger.debug(
                    'manual append to data_type'.format(
                        new_data_type_name))

            (data_group, data_group_created) = DataGroup.objects.get_or_create(
                name=new_data_group_name)
            logger.debug('creating new datatype with object {}, for dataset '
                         '{}-{} and transform {} for module {} and '
                         'dashboard {}'.format(
                             new_data_type_name,
                             new_data_group_name,
                             data_type_name,
                             transform_type['name'],
                             module.slug,
                             module.dashboard.slug,
                         ))
            data_key = '{}-{}'.format(
                new_data_group_name,
                new_data_type_name,
            )

            if seen_dashboards.get(data_key) is not None:
                logger.debug('already seen {}'.format(data_key))

            (data_type, data_type_created) = DataType.objects.get_or_create(
                name=new_data_type_name)

            if data_group_created:
                logger.info('Creating Data group {}'.format(
                    new_data_group_name))
            seen_dashboards[data_key] = True

            existing_data_type = DataType.objects.get(name=data_type_name)
            existing_data_group = DataGroup.objects.get(name=data_group_name)
            existing_data_set = DataSet.objects.get(
                data_group=existing_data_group,
                data_type=existing_data_type
            )

            (data_set, data_set_created) = DataSet.objects.get_or_create(
                data_group=data_group,
                data_type=data_type,
                defaults={'bearer_token': settings.TRANSFORMED_DATA_SET_TOKEN}
            )

            debug_names = ' '.join([
                new_data_group_name, data_type_name, new_data_type_name])
            if data_set_created:
                logger.info("Created data set: " + debug_names)
            else:
                logger.info("Data set already existed: " + debug_names)

            excluded_query_parameters = ['duration']

            query_parameters = dict(metadata['query_parameters'].items() + {
                param: value for param, value
                in module.query_parameters.iteritems()
                if param not in excluded_query_parameters
            }.items())

            transform = {
                "type_id": transform_type_id,
                "input": {
                    "data-group": data_group_name,
                    "data-type": data_type_name,
                },
                "query-parameters": query_parameters,
                "options": {
                    transform_option: module.options[spotlight_option]
                    for transform_option, spotlight_option
                    in metadata['options'].iteritems()},
                "output": {
                    "data-group": new_data_group_name,
                    "data-type": new_data_type_name,
                }
            }

            r = requests.post(
                STAGECRAFT_ROOT + '/transform',
                data=json.dumps(transform),
                headers=headers)

            if r.status_code != 200:
                logger.info(r.text)
                error_message = 'Received error from Stagecraft when making ' \
                    + 'Transform: ' + data_group_name + ' ' \
                    + new_data_type_name
                exit(error_message)

            # Run the transform against the existing data
            backdrop_headers = {
                'Authorization': 'Bearer {0}'.format(
                    existing_data_set.bearer_token),
                'Content-Type': 'application/json',
            }
            r = requests.get(
                '{}/data/{}/{}?limit=1&sort_by=_timestamp:ascending'.format(
                    BACKDROP_ROOT, data_group_name, data_type_name),
                headers=backdrop_headers,
            )

            if r.status_code != 200:
                logger.info(r.text)
                exit('Error getting oldest data point')

            data = r.json()['data']
            if len(data) != 0:
                earliest_timestamp = data[0]['_timestamp']
                run_transform = {
                    "_start_at": earliest_timestamp
                }
                r = requests.post(
                    '{0}/data/{1}/{2}/transform'.format(
                        BACKDROP_ROOT, data_group_name, data_type_name),
                    data=json.dumps(run_transform),
                    headers=backdrop_headers
                )
            else:
                logger.debug(
                    'no need to run initial transform '
                    'for {}{} as empty'.format(
                        data_group_name,
                        data_type_name))

            # Change the existing module
            module.data_set = data_set
            module.query_parameters = {
                'sort_by': '_timestamp:ascending',
            }

            if metadata['module'] == 'completion_rate':
                module.type = ModuleType.objects.get(name='single_timeseries')
                module.options = {
                    "format-options": {
                        "type": "percent"
                    },
                    "value-attribute": "rate",
                    "axes": {
                        "y": [{"label": "Completion percentage"}],
                        "x": {
                            "label": "Date",
                            "key": ["_start_at", "_end_at"],
                            "format": "date"
                        },
                    }
                }
            elif metadata['module'] == 'user_satisfaction_graph':
                module.options = {
                    "trim": False,
                    "total-attribute": "num_responses",
                    "value-attribute": "score",
                    "axis-period": "month",
                    "migrated": True,
                    "axes": {
                        'x': {
                            'label': 'Date',
                            'key': '_start_at',
                            'format': 'date'
                        },
                        'y': [
                            {
                                'label': 'User satisfaction',
                                'key': 'score',
                                'format': 'percent'
                            },
                            {
                                'label': 'Very dissatisfied',
                                'key': 'rating_1',
                                'format': 'integer'
                            },
                            {
                                'label': 'Dissatisfied',
                                'key': 'rating_2',
                                'format': 'integer'
                            },
                            {
                                'label': 'Neither satisfied or dissatisfied',
                                'key': 'rating_3',
                                'format': 'integer'
                            },
                            {
                                'label': 'Satisfied',
                                'key': 'rating_4',
                                'format': 'integer'
                            },
                            {
                                'label': 'Very satisfied',
                                'key': 'rating_5',
                                'format': 'integer'
                            }
                        ]
                    }
                }

            module.full_clean()
            module.save()

    logger.info("Finished creating TransformTypes and Transforms.")


if __name__ == '__main__':
    main()
