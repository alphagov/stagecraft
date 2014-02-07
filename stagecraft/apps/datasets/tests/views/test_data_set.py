import json

from django.test import TestCase


class DataSetsViewsTestCase(TestCase):
    fixtures = ['datasets_testdata.json']

    def test_list(self):
        resp = self.client.get('/data-sets')
        self.assertEqual(resp.status_code, 200)
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
        self.assertEqual(json.loads(resp.content), expected)

    def test_list_by_data_group(self):
        resp = self.client.get('/data-sets?data-group=group1')
        self.assertEqual(resp.status_code, 200)
        expected = [
            {
                'bearer_token': '', 'capped_size': None, 'name': 'set1',
                'data_type': 1, 'realtime': False, 'auto_ids': '',
                'max_age_expected': 86400, 'data_group': 1,
                'upload_filters': '', 'queryable': True, 'upload_format': '',
                'raw_queries_allowed': True,
            },
        ]
        self.assertEqual(json.loads(resp.content), expected)

    def test_list_by_data_type(self):
        resp = self.client.get('/data-sets?data-type=type1')
        self.assertEqual(resp.status_code, 200)
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
        self.assertEqual(json.loads(resp.content), expected)

    def test_list_nonexistant_key(self):
        resp = self.client.get('/data-sets?nonexistant-key=something')
        self.assertEqual(resp.status_code, 404)

    def test_list_nonexistant_record(self):
        resp = self.client.get('/data-sets?data-group=nonexistant-group')
        self.assertEqual(resp.status_code, 200)
        expected = []
        self.assertEqual(json.loads(resp.content), expected)

    def test_detail(self):
        resp = self.client.get('/data-sets/set1')
        self.assertEqual(resp.status_code, 200)
        expected = {
            'bearer_token': '', 'capped_size': None, 'name': 'set1',
            'data_type': 1, 'realtime': False, 'auto_ids': '',
            'max_age_expected': 86400, 'data_group': 1,
            'upload_filters': '', 'queryable': True, 'upload_format': '',
            'raw_queries_allowed': True,
        }
        self.assertEqual(json.loads(resp.content), expected)

    def test_detail_nonexistant_dataset(self):
        resp = self.client.get('/data-sets/nonexistant-dataset')
        self.assertEqual(resp.status_code, 404)
