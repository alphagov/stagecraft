from __future__ import print_function
from django.conf import settings

from stagecraft.apps.dashboards.models.dashboard import Dashboard
from stagecraft.apps.dashboards.models.module import ModuleType

from stagecraft.apps.datasets.models.data_group import DataGroup
from stagecraft.apps.datasets.models.data_type import DataType
from stagecraft.apps.datasets.models.data_set import DataSet
from stagecraft.apps.transforms.models import TransformType, Transform
from django.db.models import Q
from django.db.utils import IntegrityError
import operator

import random
from itertools import repeat

import json
import requests
import logging

import datetime
import string

STAGECRAFT_ROOT = settings.APP_ROOT
BACKDROP_ROOT = settings.BACKDROP_URL

headers = {
    'Authorization': 'Bearer {0}'.format(settings.MIGRATION_SIGNON_TOKEN),
    'Content-Type': 'application/json',
}


def generate_bearer_token():
    chars = "abcdefghjkmnpqrstuvwxyz23456789"
    return "".join(map(random.choice, repeat(chars, 64)))


def add_day(timestamp):
    """
    >>> add_day('2014-11-24T00:00:00+00:00') # doctest: +SKIP
    '2014-11-25T00:00:00+00:00'
    >>> add_day('2014-10-31T00:00:00+00:00') # doctest: +SKIP
    '2014-11-01T00:00:00+00:00'
    """
    date = datetime.datetime.strptime(
        string.split(timestamp, '+')[0], '%Y-%m-%dT%H:%M:%S')
    next_day_date = date + datetime.timedelta(days=1)
    return next_day_date.isoformat() + '+00:00'


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
    aggregate_data_group_name = 'service-aggregates'
    (aggregate_data_group, _) = DataGroup.objects.get_or_create(
        name=aggregate_data_group_name)
    aggregate_data_type_name = 'latest-dataset-values'
    (aggregate_data_type, _) = DataType.objects.get_or_create(
        name=aggregate_data_type_name)
    try:
        aggregate_data_set = DataSet.objects.create(
            data_type=aggregate_data_type,
            data_group=aggregate_data_group,
            bearer_token=generate_bearer_token()
        )
    except IntegrityError:
        aggregate_data_set = DataSet.objects.get(
            data_type__name=aggregate_data_type_name,
            data_group__name=aggregate_data_group_name,
        )

    (transform_type, _) = TransformType.objects.get_or_create(
        name="latest_dataset_value",
        function='backdrop.transformers.tasks.latest_dataset_value.compute',
    )

    for data_type in data_types:
        input_type = DataType.objects.get(name=data_type)
        transform = Transform.objects.get_or_create(
            type=transform_type,
            input_type=input_type,
            output_type=aggregate_data_type,
            output_group=aggregate_data_group
        )
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
            '{}/data/{}/{}?limit=20&sort_by=_timestamp:descending'.format(
                BACKDROP_ROOT, data_set.data_group.name,
                data_set.data_type.name),
            headers=backdrop_headers,
        )

        if r.status_code != 200:
            logger.info(r.text)
            exit('Error getting oldest data point')

        data = r.json()['data']
        if len(data) != 0:
            for data_point in data:
                has_data = False
                latest_timestamp = data_point['_timestamp']
                if data_point.get('score') or data_point.get('rate'):
                    has_data = True
                    logger.debug('Data found for {}'.format(data_set.name))
                    run_transform = {
                        "_start_at": latest_timestamp,
                        "_end_at": add_day(latest_timestamp),
                    }
                    r = requests.post(
                        '{0}/data/{1}/{2}/transform'.format(
                            BACKDROP_ROOT, data_set.data_group.name,
                            data_set.data_type.name),
                        data=json.dumps(run_transform),
                        headers=backdrop_headers
                    )
                    break
            if not has_data:
                logger.debug('No data found for {}'.format(data_set.name))

        else:
            logger.debug(
                'no need to run initial transform '
                'for {}{} as empty'.format(
                    data_set.data_group.name,
                    data_set.data_type.name))

    logger.info("Finished creating latest data transforms")


if __name__ == '__main__':
    main()
