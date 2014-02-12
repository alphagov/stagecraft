import json

from django.test import TestCase

from stagecraft.apps.datasets.models import DataSet
from stagecraft.libs.serialize import serialize_to_json


class SerializeTestCase(TestCase):
    fixtures = ['datasets_testdata.json']

    def test_serializing_a_query_set(self):
        query_set = DataSet.objects.filter()
        result = serialize_to_json(query_set)
        expected = [
            {
                'bearer_token': '', 'capped_size': None, 'name': 'set1',
                'data_type': 1, 'realtime': False, 'auto_ids': '',
                'max_age_expected': 86400, 'data_group': 1,
                'upload_filters': '', 'queryable': True, 'upload_format': '',
                'raw_queries_allowed': True,
            },
            {
                'bearer_token': '', 'capped_size': None, 'name': 'set2',
                'data_type': 1, 'realtime': False, 'auto_ids': '',
                'max_age_expected': 86400, 'data_group': 2,
                'upload_filters': '', 'queryable': True, 'upload_format': '',
                'raw_queries_allowed': True,
            },
        ]

        self.assertEqual(expected, json.loads(result))

    def test_serializing_an_empty_query_set(self):
        query_set = DataSet.objects.filter(name='set3')
        result = serialize_to_json(query_set)
        expected = []

        self.assertEqual(expected, json.loads(result))

    def test_serializing_a_model(self):
        model = DataSet.objects.get(name='set1')
        result = serialize_to_json(model)
        expected = {
            'bearer_token': '', 'capped_size': None, 'name': 'set1',
            'data_type': 1, 'realtime': False, 'auto_ids': '',
            'max_age_expected': 86400, 'data_group': 1,
            'upload_filters': '', 'queryable': True, 'upload_format': '',
            'raw_queries_allowed': True,
        }

        self.assertEqual(expected, json.loads(result))
