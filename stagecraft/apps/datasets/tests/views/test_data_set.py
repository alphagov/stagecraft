from __future__ import unicode_literals

import json

from nose.tools import assert_equal

from django.test import TestCase


class DataSetsViewsTestCase(TestCase):
    fixtures = ['datasets_testdata.json']

    def test_list(self):
        resp = self.client.get('/data-sets')
        assert_equal(resp.status_code, 200)
        expected = [
            {
                'bearer_token': '',
                'capped_size': None,
                'name': 'set1',
                'data_type': 'type1',
                'realtime': False,
                'auto_ids': '',
                'max_age_expected': 86400,
                'data_group': 'group1',
                'upload_filters': '',
                'queryable': True,
                'upload_format': '',
                'raw_queries_allowed': True,
            },
            {
                'bearer_token': '',
                'capped_size': None,
                'name': 'set2',
                'data_type': 'type1',
                'realtime': False,
                'auto_ids': '',
                'max_age_expected': 86400,
                'data_group': 'group2',
                'upload_filters': '',
                'queryable': True,
                'upload_format': '',
                'raw_queries_allowed': True,
            },
        ]
        assert_equal(json.loads(resp.content.decode('utf-8')), expected)

    def test_list_by_data_group(self):
        resp = self.client.get('/data-sets?data-group=group1')
        assert_equal(resp.status_code, 200)
        expected = [
            {
                'bearer_token': '',
                'capped_size': None,
                'name': 'set1',
                'data_type': 'type1',
                'realtime': False,
                'auto_ids': '',
                'max_age_expected': 86400,
                'data_group': 'group1',
                'upload_filters': '',
                'queryable': True,
                'upload_format': '',
                'raw_queries_allowed': True,
            },
        ]
        assert_equal(json.loads(resp.content.decode('utf-8')), expected)

    def test_list_filtering_works_with_hyphens_or_underscores(self):
        assert_equal(
            self.client.get('/data-sets?data-type=type1').content,
            self.client.get('/data-sets?data_type=type1').content
        )

        assert_equal(
            self.client.get('/data-sets?data-group=group1').content,
            self.client.get('/data-sets?data_group=group1').content
        )

    def test_list_by_data_type(self):
        resp = self.client.get('/data-sets?data-type=type1')
        assert_equal(resp.status_code, 200)
        expected = [
            {
                'bearer_token': '',
                'capped_size': None,
                'name': 'set1',
                'data_type': 'type1',
                'realtime': False,
                'auto_ids': '',
                'max_age_expected': 86400,
                'data_group': 'group1',
                'upload_filters': '',
                'queryable': True,
                'upload_format': '',
                'raw_queries_allowed': True,
            },
            {
                'bearer_token': '',
                'capped_size': None,
                'name': 'set2',
                'data_type': 'type1',
                'realtime': False,
                'auto_ids': '',
                'max_age_expected': 86400,
                'data_group': 'group2',
                'upload_filters': '',
                'queryable': True,
                'upload_format': '',
                'raw_queries_allowed': True,
            },
        ]
        assert_equal(json.loads(resp.content.decode('utf-8')), expected)

    def test_list_nonexistant_key(self):
        resp = self.client.get('/data-sets?nonexistant-key=something')
        assert_equal(resp.status_code, 400)

    def test_list_nonexistant_record(self):
        resp = self.client.get('/data-sets?data-group=nonexistant-group')
        assert_equal(resp.status_code, 200)
        expected = []
        assert_equal(json.loads(resp.content.decode('utf-8')), expected)

    def test_detail(self):
        resp = self.client.get('/data-sets/set1')
        assert_equal(resp.status_code, 200)
        expected = {
            'bearer_token': '',
            'capped_size': None,
            'name': 'set1',
            'data_type': 'type1',
            'realtime': False,
            'auto_ids': '',
            'max_age_expected': 86400,
            'data_group': 'group1',
            'upload_filters': '',
            'queryable': True,
            'upload_format': '',
            'raw_queries_allowed': True,
        }
        assert_equal(json.loads(resp.content.decode('utf-8')), expected)

    def test_detail_nonexistant_dataset(self):
        resp = self.client.get('/data-sets/nonexistant-dataset')
        assert_equal(resp.status_code, 404)
