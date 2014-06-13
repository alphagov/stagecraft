from __future__ import unicode_literals

import json
from nose.tools import assert_equal
from hamcrest import assert_that

from django.test import TestCase
from django_nose.tools import assert_redirects

from stagecraft.apps.datasets.tests.support.test_helpers import (
    is_unauthorized, is_error_response, has_header, has_status)


class LongCacheTestCase(TestCase):

    def test_list_sets_long_cache_headers(self):
        resp = self.client.get(
            '/data-sets',
            HTTP_AUTHORIZATION='Bearer dev-data-set-query-token')
        assert_that(resp, has_header('Cache-Control', 'max-age=31536000'))
        assert_that(resp, has_header('Vary', 'Authorization'))

    def test_detail_sets_long_cache_headers(self):
        resp = self.client.get(
            '/data-sets/set1',
            HTTP_AUTHORIZATION='Bearer dev-data-set-query-token')
        assert_that(resp, has_header('Cache-Control', 'max-age=31536000'))
        assert_that(resp, has_header('Vary', 'Authorization'))


class DataSetsViewsTestCase(TestCase):
    fixtures = ['datasets_testdata.json']

    def test_authorization_header_needed_for_list(self):
        resp = self.client.get('/data-sets')
        assert_that(resp, is_unauthorized())
        assert_that(resp, is_error_response())

    def test_authorization_header_needed_for_detail(self):
        resp = self.client.get('/data-sets/set1')
        assert_that(resp, is_unauthorized())
        assert_that(resp, is_error_response())

    def test_correct_format_authorization_header_needed_for_list(self):
        resp = self.client.get(
            '/data-sets',
            HTTP_AUTHORIZATION='Nearer dev-data-set-query-token')
        assert_that(resp, is_unauthorized())
        assert_that(resp, is_error_response())

    def test_correct_format_authorization_header_needed_for_detail(self):
        resp = self.client.get(
            '/data-sets/set1',
            HTTP_AUTHORIZATION='Nearer dev-data-set-query-token')
        assert_that(resp, is_unauthorized())
        assert_that(resp, is_error_response())

    def test_correct_authorization_header_needed_for_list(self):
        resp = self.client.get(
            '/data-sets',
            HTTP_AUTHORIZATION='Bearer I AM WRONG')
        assert_that(resp, is_unauthorized())
        assert_that(resp, is_error_response())

    def test_correct_authorization_header_needed_for_detail(self):
        resp = self.client.get(
            '/data-sets/set1',
            HTTP_AUTHORIZATION='Bearer I AM WRONG')
        assert_that(resp, is_unauthorized())
        assert_that(resp, is_error_response())

    def test_list(self):
        resp = self.client.get(
            '/data-sets',
            HTTP_AUTHORIZATION='Bearer dev-data-set-query-token')
        assert_equal(resp.status_code, 200)
        expected = [
            {
                'bearer_token': None,
                'capped_size': None,
                'name': 'set1',
                'data_type': 'type1',
                'realtime': False,
                'auto_ids': ['aa'],
                'max_age_expected': 86400,
                'data_group': 'group1',
                'upload_filters': ['backdrop.filter.1'],
                'queryable': True,
                'upload_format': '',
                'raw_queries_allowed': True,
                'published': False,
                'schema': {
                    '$schema': 'http://json-schema.org/schema#',
                    'title': 'Timestamps',
                    'type': 'object',
                    'properties': {
                        '_timestamp': {
                            'description': 'An ISO8601 formatted date time',
                            'type': 'string',
                            'format': 'date-time'
                        }
                    },
                    'required': ['_timestamp']
                }
            },
            {
                'bearer_token': None,
                'capped_size': None,
                'name': 'set2',
                'data_type': 'type1',
                'realtime': False,
                'auto_ids': ['aa', 'bb'],
                'max_age_expected': 86400,
                'data_group': 'group2',
                'upload_filters': ['backdrop.filter.1', 'backdrop.filter.2'],
                'queryable': True,
                'upload_format': '',
                'raw_queries_allowed': True,
                'published': False,
                'schema': {
                    '$schema': 'http://json-schema.org/schema#',
                    'title': 'Timestamps',
                    'type': 'object',
                    'properties': {
                        '_timestamp': {
                            'description': 'An ISO8601 formatted date time',
                            'type': 'string',
                            'format': 'date-time'
                        }
                    },
                    'required': ['_timestamp']
                }
            },
            {
                'name': 'abc_-0123456789',
                'data_group': 'group3',
                'data_type': 'type3',
                'bearer_token': None,
                'capped_size': None,
                'realtime': False,
                'auto_ids': [],
                'max_age_expected': 86400,
                'upload_filters': [],
                'queryable': True,
                'upload_format': '',
                'raw_queries_allowed': True,
                'published': False,
                'schema': {
                    '$schema': 'http://json-schema.org/schema#',
                    'title': 'Timestamps',
                    'type': 'object',
                    'properties': {
                        '_timestamp': {
                            'description': 'An ISO8601 formatted date time',
                            'type': 'string',
                            'format': 'date-time'
                        }
                    },
                    'required': ['_timestamp']
                }
            }
        ]
        assert_equal(json.loads(resp.content.decode('utf-8')), expected)

    def test_list_by_data_group(self):
        resp = self.client.get(
            '/data-sets?data-group=group1',
            HTTP_AUTHORIZATION='Bearer dev-data-set-query-token')
        assert_equal(resp.status_code, 200)
        expected = [
            {
                'bearer_token': None,
                'capped_size': None,
                'name': 'set1',
                'data_type': 'type1',
                'realtime': False,
                'auto_ids': ['aa'],
                'max_age_expected': 86400,
                'data_group': 'group1',
                'upload_filters': ['backdrop.filter.1'],
                'queryable': True,
                'upload_format': '',
                'raw_queries_allowed': True,
                'published': False,
                'schema': {
                    '$schema': 'http://json-schema.org/schema#',
                    'title': 'Timestamps',
                    'type': 'object',
                    'properties': {
                        '_timestamp': {
                            'description': 'An ISO8601 formatted date time',
                            'type': 'string',
                            'format': 'date-time'
                        }
                    },
                    'required': ['_timestamp']
                }
            },
        ]
        assert_equal(json.loads(resp.content.decode('utf-8')), expected)

    def test_list_filtering_works_with_hyphens_or_underscores(self):
        assert_equal(
            self.client.get(
                '/data-sets?data-type=type1',
                HTTP_AUTHORIZATION='Bearer dev-data-set-query-token').content,
            self.client.get(
                '/data-sets?data_type=type1',
                HTTP_AUTHORIZATION='Bearer dev-data-set-query-token').content
        )

        assert_equal(
            self.client.get(
                '/data-sets?data-group=group1',
                HTTP_AUTHORIZATION='Bearer dev-data-set-query-token').content,
            self.client.get(
                '/data-sets?data_group=group1',
                HTTP_AUTHORIZATION='Bearer dev-data-set-query-token').content,
        )

    def test_list_with_trailing_slash_redirects_correctly(self):
        response = self.client.get('/data-sets/?data-type=aaa',
                                   HTTP_AUTHORIZATION=('Bearer '
                                   'dev-data-set-query-token'),
                                   follow=True)
        assert_redirects(response, '/data-sets?data-type=aaa',
                         status_code=301, target_status_code=200)

    def test_list_filtering_works_with_slash_before_query(self):
        assert_equal(
            self.client.get(
                '/data-sets?data-type=type1',
                HTTP_AUTHORIZATION='Bearer dev-data-set-query-token').content,
            self.client.get(
                '/data-sets/?data-type=type1',
                HTTP_AUTHORIZATION='Bearer dev-data-set-query-token',
                follow=True).content
        )

    def test_list_by_data_type(self):
        resp = self.client.get(
            '/data-sets?data-type=type1',
            HTTP_AUTHORIZATION='Bearer dev-data-set-query-token')
        assert_equal(resp.status_code, 200)
        expected = [
            {
                'bearer_token': None,
                'capped_size': None,
                'name': 'set1',
                'data_type': 'type1',
                'realtime': False,
                'auto_ids': ['aa'],
                'max_age_expected': 86400,
                'data_group': 'group1',
                'upload_filters': ['backdrop.filter.1'],
                'queryable': True,
                'upload_format': '',
                'raw_queries_allowed': True,
                'published': False,
                'schema': {
                    '$schema': 'http://json-schema.org/schema#',
                    'title': 'Timestamps',
                    'type': 'object',
                    'properties': {
                        '_timestamp': {
                            'description': 'An ISO8601 formatted date time',
                            'type': 'string',
                            'format': 'date-time'
                        }
                    },
                    'required': ['_timestamp']
                }
            },
            {
                'bearer_token': None,
                'capped_size': None,
                'name': 'set2',
                'data_type': 'type1',
                'realtime': False,
                'auto_ids': ['aa', 'bb'],
                'max_age_expected': 86400,
                'data_group': 'group2',
                'upload_filters': ['backdrop.filter.1', 'backdrop.filter.2'],
                'queryable': True,
                'upload_format': '',
                'raw_queries_allowed': True,
                'published': False,
                'schema': {
                    '$schema': 'http://json-schema.org/schema#',
                    'title': 'Timestamps',
                    'type': 'object',
                    'properties': {
                        '_timestamp': {
                            'description': 'An ISO8601 formatted date time',
                            'type': 'string',
                            'format': 'date-time'
                        }
                    },
                    'required': ['_timestamp']
                }
            },
        ]
        assert_equal(json.loads(resp.content.decode('utf-8')), expected)

    def test_list_nonexistant_key(self):
        resp = self.client.get(
            '/data-sets?nonexistant-key=something',
            HTTP_AUTHORIZATION='Bearer dev-data-set-query-token')
        assert_equal(resp.status_code, 400)

    def test_list_nonexistant_record(self):
        resp = self.client.get(
            '/data-sets?data-group=nonexistant-group',
            HTTP_AUTHORIZATION='Bearer dev-data-set-query-token')
        assert_equal(resp.status_code, 200)
        expected = []
        assert_equal(json.loads(resp.content.decode('utf-8')), expected)

    def test_detail(self):
        resp = self.client.get(
            '/data-sets/set1',
            HTTP_AUTHORIZATION='Bearer dev-data-set-query-token')
        assert_equal(resp.status_code, 200)
        expected = {
            'bearer_token': None,
            'capped_size': None,
            'name': 'set1',
            'data_type': 'type1',
            'realtime': False,
            'auto_ids': ['aa'],
            'max_age_expected': 86400,
            'data_group': 'group1',
            'upload_filters': ['backdrop.filter.1'],
            'queryable': True,
            'upload_format': '',
            'raw_queries_allowed': True,
            'published': False,
            'schema': {
                '$schema': 'http://json-schema.org/schema#',
                'title': 'Timestamps',
                'type': 'object',
                'properties': {
                    '_timestamp': {
                        'description': 'An ISO8601 formatted date time',
                        'type': 'string',
                        'format': 'date-time'
                    }
                },
                'required': ['_timestamp']
            }
        }
        assert_equal(json.loads(resp.content.decode('utf-8')), expected)

    def test_detail_works_with_all_slugfield_characters(self):
        resp = self.client.get(
            '/data-sets/abc_-0123456789',
            HTTP_AUTHORIZATION='Bearer dev-data-set-query-token')
        assert_equal(resp.status_code, 200)
        expected = {
            'name': 'abc_-0123456789',
            'data_group': 'group3',
            'data_type': 'type3',
            'bearer_token': None,
            'capped_size': None,
            'realtime': False,
            'auto_ids': [],
            'max_age_expected': 86400,
            'upload_filters': [],
            'queryable': True,
            'upload_format': '',
            'raw_queries_allowed': True,
            'published': False,
            'schema': {
                '$schema': 'http://json-schema.org/schema#',
                'title': 'Timestamps',
                'type': 'object',
                'properties': {
                    '_timestamp': {
                        'description': 'An ISO8601 formatted date time',
                        'type': 'string',
                        'format': 'date-time'
                    }
                },
                'required': ['_timestamp']
            }
        }
        assert_equal(json.loads(resp.content.decode('utf-8')), expected)

    def test_detail_nonexistant_dataset(self):
        resp = self.client.get(
            '/data-sets/nonexistant-dataset',
            HTTP_AUTHORIZATION='Bearer dev-data-set-query-token')
        assert_equal(resp.status_code, 404)


class HealthCheckTestCase(TestCase):
    fixtures = ['datasets_testdata.json']

    def setUp(self):
        self.response = self.client.get('/_status/data-sets')

    def test_health_check_url_returns_http_200_with_json_message(self):
        assert_that(self.response, has_status(200))
        decoded = json.loads(self.response.content.decode('utf-8'))
        assert_equal(
            decoded,
            {'message': 'Got 3 data sets.'})
