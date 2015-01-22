from __future__ import print_function
from django.conf import settings

from stagecraft.apps.dashboards.models.dashboard import Dashboard
from stagecraft.apps.dashboards.models.module import ModuleType

from stagecraft.apps.datasets.models.data_group import DataGroup
from stagecraft.apps.datasets.models.data_type import DataType
from stagecraft.apps.datasets.models.data_set import DataSet
from stagecraft.apps.transforms.models import TransformType
from django.db.models import Q
import operator

import json
import requests
import logging

STAGECRAFT_ROOT = settings.APP_ROOT
BACKDROP_ROOT = settings.BACKDROP_URL

headers = {
    'Authorization': 'Bearer {0}'.format(settings.MIGRATION_SIGNON_TOKEN),
    'Content-Type': 'application/json',
}


def main():

    # force django to bootstrap logging so we can override it
    env = settings.ENV_HOSTNAME
    logger = logging.getLogger('')
    logger.setLevel(logging.DEBUG)
    logger.addHandler(logging.StreamHandler())

    data_types = [
        'completion-rate',
        'user-satisfaction-score',
        'digital-takeup',
    ]

    (transform_type, _) = TransformType.objects.get_or_create(
        name="latest_dataset_value",
        function='backdrop.transformers.tasks.latest_dataset_value.compute'
    )

    for data_type in data_types:
        transform = {
            "type_id": str(transform_type.id),
            "input": {
                "data-group": '*',
                "data-type": data_type,
            },
            "query-parameters": {},
            "options": {
            },
            "output": {
                "data-group": "service-aggregates",
                "data-type": "latest-dataset-values",
            }
        }

        r = requests.post(
            STAGECRAFT_ROOT + '/transform',
            data=json.dumps(transform),
            headers=headers)

        if r.status_code != 200:
            logger.info(r.text)
            logger.info(r.status_code)
            error_message = 'Transform already exists in Stagecraft making ' \
                + 'Transform: ' + data_type_name
            logger.info(error_message)

    # get all the datasets for the given data types
    data_sets = DataSet.objects.filter(
        reduce(
            operator.or_,
            map(lambda data_type: Q(data_type__name=data_type),
                data_types),
            Q()))
    for data_set in data_sets:
        # Run the transform against the existing data
        backdrop_headers = {
            'Authorization': 'Bearer {0}'.format(
                data_set.bearer_token),
            'Content-Type': 'application/json',
        }
        r = requests.get(
            '{}/data/{}/{}?limit=1&sort_by=_timestamp:descending'.format(
                BACKDROP_ROOT, data_set.data_group.name,
                data_set.data_type.name),
            headers=backdrop_headers,
        )

        if r.status_code != 200:
            logger.info(r.text)
            exit('Error getting oldest data point')

        data = r.json()['data']
        if len(data) != 0:
            latest_timestamp = data[0]['_timestamp']
            run_transform = {
                "_start_at": latest_timestamp
            }
            r = requests.post(
                '{0}/data/{1}/{2}/transform'.format(
                    BACKDROP_ROOT, data_set.data_group.name,
                    data_set.data_type.name),
                data=json.dumps(run_transform),
                headers=backdrop_headers
            )
        else:
            logger.debug(
                'no need to run initial transform '
                'for {}{} as empty'.format(
                    data_set.data_group.name,
                    data_set.data_type.name))

    logger.info("Finished creating latest data transforms")


if __name__ == '__main__':
    main()
