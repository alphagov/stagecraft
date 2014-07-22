from __future__ import unicode_literals

import json
from nose.tools import assert_equal
from hamcrest import assert_that, contains, has_entries, equal_to, \
    has_entry

from django.test import TestCase
from django_nose.tools import assert_redirects

from stagecraft.apps.datasets.tests.support.test_helpers import (
    is_unauthorized, is_error_response, has_header, has_status)


class DataSetsViewsTestCase(TestCase):
    assert_equal.__self__.maxDiff = None
    fixtures = ['datasets_testdata.json']

    base_schema = {
        "definitions": {
            "_timestamp": {
                "$schema": "http://json-schema.org/schema#",
                "title": "Timestamps",
                "type": "object",
                "properties": {
                    "_timestamp": {
                        "description": "An ISO8601 formatted date time",
                        "type": "string",
                        "format": "date-time"
                    }
                },
                "required": ["_timestamp"]
            }
        },
        "allOf": [{"$ref": "#/definitions/_timestamp"}]
    }

    def _get_default_schema(self, name=None):
        schema = self.base_schema
        schema["description"] = "Schema for {}".format(name)
        return schema

    def _get_monitoring_schema():
        return {
            "allOf": [
                {
                    "$ref": "#/definitions/_timestamp"
                },
                {
                    "$ref": "#/definitions/monitoring"
                }
            ],
            "description": "Schema for group3/monitoring",
            "definitions": {
                "_timestamp": {
                    "$schema": "http://json-schema.org/schema#",
                    "properties": {
                        "_timestamp": {
                            "description": "An ISO8601 formatted date time",
                            "format": "date-time",
                            "type": "string"
                        }
                    },
                    "required": [
                        "_timestamp"
                    ],
                    "title": "Timestamps",
                    "type": "object"
                },
                "monitoring": {
                    "$schema": "http://json-schema.org/schema#",
                    "properties": {
                        "downtime": {
                            "description": "Integer",
                            "type": "integer"
                        },
                        "uptime": {
                            "description": "Integer",
                            "type": "integer"
                        }
                    },
                    "title": "Monitoring",
                    "type": "object",
                    "required": [
                        "uptime",
                        "downtime"
                    ],
                }
            }
        }

    monitoring_schema = _get_monitoring_schema()

    def test_list_vary_on_authorization_header(self):
        resp = self.client.get(
            '/data-sets',
            HTTP_AUTHORIZATION='Bearer development-oauth-access-token')
        assert_that(resp, has_header('Vary', 'Authorization'))

    def test_detail_vary_on_authorization_header(self):
        resp = self.client.get(
            '/data-sets',
            HTTP_AUTHORIZATION='Bearer development-oauth-access-token')
        assert_that(resp, has_header('Vary', 'Authorization'))

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
            HTTP_AUTHORIZATION='Nearer development-oauth-access-token')
        assert_that(resp, is_unauthorized())
        assert_that(resp, is_error_response())

    def test_correct_format_authorization_header_needed_for_detail(self):
        resp = self.client.get(
            '/data-sets/set1',
            HTTP_AUTHORIZATION='Nearer development-oauth-access-token')
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

    def test_list_only_returns_data_sets_the_user_can_see(self):
        resp = self.client.get(
            '/data-sets',
            HTTP_AUTHORIZATION='Bearer development-oauth-access-token')
        assert_equal(resp.status_code, 200)
        response_object = json.loads(resp.content.decode('utf-8'))
        assert_equal(len(response_object), 4)

    def test_list(self):
        resp = self.client.get(
            '/data-sets',
            HTTP_AUTHORIZATION='Bearer development-oauth-access-token')
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
                'published': False
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
                'published': False
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
                'published': False
            },
            {
                'name': 'monitoring-data-set',
                'data_group': 'group3',
                'data_type': 'monitoring',
                'bearer_token': None,
                'capped_size': None,
                'realtime': False,
                'auto_ids': [],
                'max_age_expected': 86400,
                'upload_filters': [],
                'queryable': True,
                'upload_format': '',
                'raw_queries_allowed': True,
                'published': False
            }
        ]

        response_object = json.loads(resp.content.decode('utf-8'))

        assert_equal(len(response_object), len(expected))
        for i, record in enumerate(expected):
            if record['data_group'] != 'monitoring':
                record['schema'] = self._get_default_schema(
                    record['data_group'] + "/" +
                    record['data_type']
                )
            else:
                record['schema'] = self.monitoring_schema

            assert_equal(
                record, response_object[i]
            )

    def test_list_by_data_group(self):
        resp = self.client.get(
            '/data-sets?data-group=group1',
            HTTP_AUTHORIZATION='Bearer development-oauth-access-token')
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
                'schema': self._get_default_schema('group1/type1')
            },
        ]
        assert_equal(
            json.loads(resp.content.decode('utf-8')),
            expected
        )

    def test_list_filtering_works_with_hyphens_or_underscores(self):
        assert_equal(
            self.client.get(
                '/data-sets?data-type=type1',
                HTTP_AUTHORIZATION='Bearer development-oauth-access-token'
            ).content,
            self.client.get(
                '/data-sets?data_type=type1',
                HTTP_AUTHORIZATION='Bearer development-oauth-access-token'
            ).content
        )

        assert_equal(
            self.client.get(
                '/data-sets?data-group=group1',
                HTTP_AUTHORIZATION='Bearer development-oauth-access-token'
            ).content,
            self.client.get(
                '/data-sets?data_group=group1',
                HTTP_AUTHORIZATION='Bearer development-oauth-access-token'
            ).content,
        )

    def test_list_with_trailing_slash_redirects_correctly(self):
        response = self.client.get(
            '/data-sets/?data-type=aaa',
            HTTP_AUTHORIZATION=('Bearer development-oauth-access-token'),
            follow=True)
        assert_redirects(response, '/data-sets?data-type=aaa',
                         status_code=301, target_status_code=200)

    def test_list_filtering_works_with_slash_before_query(self):
        assert_equal(
            self.client.get(
                '/data-sets?data-type=type1',
                HTTP_AUTHORIZATION='Bearer development-oauth-access-token'
            ).content,
            self.client.get(
                '/data-sets/?data-type=type1',
                HTTP_AUTHORIZATION='Bearer development-oauth-access-token',
                follow=True).content
        )

    def test_list_by_data_type(self):
        resp = self.client.get(
            '/data-sets?data-type=type1',
            HTTP_AUTHORIZATION='Bearer development-oauth-access-token')
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
            },
        ]

        response_object = json.loads(resp.content.decode('utf-8'))
        for i, record in enumerate(expected):
            record['schema'] = self._get_default_schema(
                record['data_group'] + "/" +
                record['data_type']
            )
            assert_equal(
                record, response_object[i]
            )

    def test_list_nonexistant_key(self):
        resp = self.client.get(
            '/data-sets?nonexistant-key=something',
            HTTP_AUTHORIZATION='Bearer development-oauth-access-token')
        assert_equal(resp.status_code, 400)

    def test_list_nonexistant_record(self):
        resp = self.client.get(
            '/data-sets?data-group=nonexistant-group',
            HTTP_AUTHORIZATION='Bearer development-oauth-access-token')
        assert_equal(resp.status_code, 200)
        expected = []
        assert_equal(json.loads(resp.content.decode('utf-8')), expected)

    def test_detail(self):
        resp = self.client.get(
            '/data-sets/set1',
            HTTP_AUTHORIZATION='Bearer development-oauth-access-token')
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
            'schema': self._get_default_schema('group1/type1')
        }
        assert_equal(json.loads(resp.content.decode('utf-8')), expected)

    def test_monitoring_schema(self):

        resp = self.client.get(
            '/data-sets/monitoring-data-set',
            HTTP_AUTHORIZATION='Bearer development-oauth-access-token')
        assert_equal(resp.status_code, 200)

        expected_schema = self.monitoring_schema

        resp_json = json.loads(resp.content.decode('utf-8'))

        assert_equal(resp_json['schema'], expected_schema)

    def test_detail_works_with_all_slugfield_characters(self):
        resp = self.client.get(
            '/data-sets/abc_-0123456789',
            HTTP_AUTHORIZATION='Bearer development-oauth-access-token')
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
            'schema': self._get_default_schema('group3/type3')
        }
        assert_equal(json.loads(resp.content.decode('utf-8')), expected)

    def test_detail_nonexistant_dataset(self):
        resp = self.client.get(
            '/data-sets/nonexistant-dataset',
            HTTP_AUTHORIZATION='Bearer development-oauth-access-token')
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
            {'message': 'Got 5 data sets.'})


class DataSetsSchemasTestCase(TestCase):
    assert_equal.__self__.maxDiff = None
    fixtures = ['datasets_testschemas.json']

    def test_transactions_by_channel_schema(self):

        resp = self.client.get(
            '/data-sets/jonathan_datagroup_transactions_by_channel',
            HTTP_AUTHORIZATION='Bearer development-oauth-access-token'
        )
        assert_equal(resp.status_code, 200)

        resp_json = json.loads(resp.content.decode('utf-8'))
        schema = resp_json['schema']

        assert_that(
            schema,
            has_entries(
                'allOf',
                contains(
                    has_entries({
                        "$ref": equal_to("#/definitions/_timestamp")
                    }),
                    has_entries({
                        "$ref": equal_to(
                            "#/definitions/transactions-by-channel")
                    })
                )
            )
        )

        assert_that(
            schema,
            has_entry(
                'definitions', contains(
                    'transactions-by-channel', '_timestamp'
                )
            )
        )
        assert_that(
            schema['definitions']['transactions-by-channel'],
            has_entry(
                'required',
                contains(
                    "count",
                    "channel"
                )
            )
        )

    def test_customer_satisfaction_schema(self):

        resp = self.client.get(
            '/data-sets/data-scootah',
            HTTP_AUTHORIZATION='Bearer development-oauth-access-token'
        )
        assert_equal(resp.status_code, 200)

        resp_json = json.loads(resp.content.decode('utf-8'))
        schema = resp_json['schema']

        assert_that(
            schema,
            has_entries(
                'allOf',
                contains(
                    has_entries({
                        "$ref": equal_to("#/definitions/_timestamp")
                    }),
                    has_entries({
                        "$ref": equal_to("#/definitions/customer-satisfaction")
                    })
                )
            )
        )

        assert_that(
            schema,
            has_entry(
                'definitions', contains(
                    'customer-satisfaction', '_timestamp'
                )
            )
        )

        assert_that(
            schema['definitions']['customer-satisfaction'],
            has_entry(
                'required',
                contains(
                    "comments",
                    "rating_1",
                    "rating_2",
                    "rating_3",
                    "rating_4",
                    "rating_5",
                    "slug",
                    "total"
                )
            )
        )

    def test_realtime_dataset(self):

        resp = self.client.get(
            '/data-sets/realtime-mowers',
            HTTP_AUTHORIZATION='Bearer development-oauth-access-token'
        )
        assert_equal(resp.status_code, 200)

        resp_json = json.loads(resp.content.decode('utf-8'))
        schema = resp_json['schema']

        assert_that(
            schema,
            has_entries(
                'allOf',
                contains(
                    has_entries({
                        "$ref": equal_to("#/definitions/_timestamp")
                    }),
                    has_entries({
                        "$ref": equal_to("#/definitions/realtime")
                    })
                )
            )
        )

        assert_that(
            schema,
            has_entry(
                'definitions', contains(
                    '_timestamp', 'realtime'
                )
            )
        )

        assert_that(
            schema['definitions']['realtime'],
            has_entry(
                'required',
                contains(
                    "for_url",
                    "unique_visitors"
                )
            )
        )
