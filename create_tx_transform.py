from django.conf import settings

from stagecraft.apps.datasets.models.data_group import DataGroup
from stagecraft.apps.datasets.models.data_type import DataType
from stagecraft.apps.datasets.models.data_set import DataSet
from stagecraft.apps.transforms.models import TransformType, Transform
from django.db.utils import IntegrityError

import random
from itertools import repeat

import json
import requests
import logging

STAGECRAFT_ROOT = settings.APP_ROOT
BACKDROP_ROOT = settings.BACKDROP_URL

headers = {
    'Authorization': 'Bearer {0}'.format(settings.MIGRATION_SIGNON_TOKEN),
    'Content-Type': 'application/json',
}


def generate_bearer_token():
    chars = "abcdefghjkmnpqrstuvwxyz23456789"
    return "".join(map(random.choice, repeat(chars, 64)))


def class_to_endpoint(klass):
    return {
        Transform: '/transform',
        TransformType: '/transform-type'
    }[klass]


def get_or_create_with_api(klass, payload, id_field):
    transform_type = klass.objects.filter(
        **{id_field: payload[id_field]}).first()
    if not transform_type:
        create_with_api(klass, payload)
        transform_type = klass.objects.filter(
            **{id_field: payload[id_field]}).first()
    return transform_type


def create_with_api(klass, payload):
    headers = {
        'Authorization': 'Bearer {0}'.format(settings.MIGRATION_SIGNON_TOKEN),
        'Content-Type': 'application/json',
    }
    response = requests.post(
        STAGECRAFT_ROOT + class_to_endpoint(klass),
        data=json.dumps(payload),
        headers=headers)
    response.raise_for_status()
    return response


def main():

    # force django to bootstrap logging so we can override it
    logger = logging.getLogger('')
    logger.setLevel(logging.DEBUG)
    logger.addHandler(logging.StreamHandler())

    aggregate_data_group_name = 'service-aggregates'
    (aggregate_data_group, _) = DataGroup.objects.get_or_create(
        name=aggregate_data_group_name)
    aggregate_data_type_name = 'latest-dataset-values'
    (aggregate_data_type, _) = DataType.objects.get_or_create(
        name=aggregate_data_type_name)
    try:
        DataSet.objects.create(
            data_type=aggregate_data_type,
            data_group=aggregate_data_group,
            bearer_token=generate_bearer_token()
        )
    except IntegrityError:
        DataSet.objects.get(
            data_type__name=aggregate_data_type_name,
            data_group__name=aggregate_data_group_name,
        )

    latest_transaction_values_transform = {
        "name": "latest_transaction_values",
        "function": "backdrop.transformers.tasks.latest_trans"
                    "action_explorer_values.compute",
        "schema": {}
    }

    transform_type = get_or_create_with_api(
        TransformType,
        latest_transaction_values_transform,
        'name')

    input_type = DataType.objects.get(name='summaries')
    input_group = DataGroup.objects.get(name='transactional-services')
    payload = {
        "type_id": str(transform_type.id),
        "input": {
            "data-type": input_type.name,
            "data-group": input_group.name,
        },
        "query-parameters": {},
        "options": {},
        "output": {
            "data-type": aggregate_data_type.name,
            "data-group": aggregate_data_group.name,
        },
    }
    get_or_create_with_api(
        Transform,
        payload,
        'type_id')
    data_set = DataSet.objects.get(
        data_type__name=input_type.name,
        data_group__name=input_group.name)

    backdrop_headers = {
        'Authorization': 'Bearer {0}'.format(
            data_set.bearer_token),
        'Content-Type': 'application/json',
    }
    run_transform = {
        "_start_at": "2011-04-01T00:00:00+00:00",
        "_end_at": "2015-01-28T00:00:00+00:00"
    }
    requests.post(
        '{0}/data/{1}/{2}/transform'.format(
            BACKDROP_ROOT, data_set.data_group.name,
            data_set.data_type.name),
        data=json.dumps(run_transform),
        headers=backdrop_headers
    )
    print(len(TransformType.objects.all()))
    print(len(Transform.objects.all()))

    logger.info("Finished creating latest data transforms")


if __name__ == '__main__':
    main()
