import mock
from stagecraft.apps.datasets.models import DataSet
from django.test import TestCase
from stagecraft.libs.mass_update import migrate_data_set
from nose.tools import assert_equal


class TestDataSetMassUpdate(TestCase):
    fixtures = ['datasets_testschemas.json']

    def setUp(self):
        self.data_set_mapping = {
            'old_data_set': {
                'data_group': 'scooters',
                'data_type': 'customer-satisfaction'
            },
            'new_data_set': {
                'data_type': "a_type",
                'auto_ids': "foo,bar,baz",
            },
            'data_mapping': {
                'key_mapping': {
                    "key": "channel",
                    "value": "count"
                },
                'value_mapping': {
                    "ca_clerical_received": "paper",
                    "ca_e_claims_received": "digital"
                }
            }
        }

        self.data_set_mapping_new_exists = {
            'old_data_set': {
                'data_group': 'mowers',
                'data_type': 'realtime'
            },
            'new_data_set': {
                'data_group': "mowers",
                'data_type': "realtime",
                'auto_ids': "foo,bar,baz",
            },
            'data_mapping': {
                'key_mapping': {
                    "key": "channel",
                    "value": "count"
                },
                'value_mapping': {
                    "ca_clerical_received": "paper",
                    "ca_e_claims_received": "digital"
                }
            }
        }

        # existing data set config comes from fixture
        self.new_dataset_config = {
            u'auto_ids': [u'foo', u'bar', u'baz'],
            u'bearer_token': None,
            u'capped_size': None,
            u'data_group': u'scooters',
            u'data_type': u'a_type',
            u'max_age_expected': 86400,
            u'name': u'scooters_a_type',
            u'queryable': True,
            u'raw_queries_allowed': True,
            u'realtime': False,
            u'upload_filters': [u'backdrop.filter.1'],
            u'upload_format': u'',
            u'published': False,
        }
        self.new_dataset_config_already_exists = {
            u'auto_ids': [u'foo', u'bar', u'baz'],
            u'bearer_token': None,
            u'capped_size': None,
            u'data_group': u'mowers',
            u'data_type': u'realtime',
            u'max_age_expected': 86400,
            u'name': u'realtime-mowers',
            u'queryable': True,
            u'raw_queries_allowed': True,
            u'realtime': False,
            u'upload_filters': [u'backdrop.filter.1'],
            u'upload_format': u'',
            u'published': False,
        }

        self.existing_data = {
            "data": [
                {
                    "_day_start_at": "2014-03-10T00:00:00+00:00",
                    "_hour_start_at": "2014-03-10T00:00:00+00:00",
                    "_id": "MjAxNC0wMy0xMFQwMDowMDowMCswMDowMC5jYV9l==",
                    "_month_start_at": "2014-03-01T00:00:00+00:00",
                    "_quarter_start_at": "2014-01-01T00:00:00+00:00",
                    "_timestamp": "2014-03-10T00:00:00+00:00",
                    "_updated_at": "2014-06-30T13:46:11.446000+00:00",
                    "_week_start_at": "2014-03-10T00:00:00+00:00",
                    "comment": None,
                    "key": "ca_clerical_received",
                    "period": "week",
                    "value": 2294.0
                },
                {
                    "_day_start_at": "2014-04-14T00:00:00+00:00",
                    "_hour_start_at": "2014-04-14T00:00:00+00:00",
                    "_id": "MjAxNC0wNC0xNFQwMDowMDowMCswMDowMC5jYV9l==",
                    "_month_start_at": "2014-04-01T00:00:00+00:00",
                    "_quarter_start_at": "2014-04-01T00:00:00+00:00",
                    "_timestamp": "2014-04-14T00:00:00+00:00",
                    "_updated_at": "2014-06-30T13:46:11.448000+00:00",
                    "_week_start_at": "2014-04-14T00:00:00+00:00",
                    "comment": None,
                    "key": "ca_e_claims_received",
                    "period": "week",
                    "value": 6822.0
                }
            ]}
        self.newly_mapped_data = {
            "data": [
                {
                    "_id": "MjAxNC0wMy0xMFQwMDowMDowMCswMDowMC5jYV9l==",
                    "_timestamp": "2014-03-10T00:00:00+00:00",
                    "comment": None,
                    "channel": "paper",
                    "period": "week",
                    "count": 2294
                },
                {
                    "_id": "MjAxNC0wNC0xNFQwMDowMDowMCswMDowMC5jYV9l==",
                    "_timestamp": "2014-04-14T00:00:00+00:00",
                    "comment": None,
                    "channel": "digital",
                    "period": "week",
                    "count": 6822
                }
            ]}

    @mock.patch("performanceplatform.client.DataSet.get")
    @mock.patch("performanceplatform.client.DataSet.post")
    def test_correct_new_data_set_created(self, client_post, client_get):
        mock_get_response = mock.Mock()
        mock_get_response.json.return_value = self.existing_data
        client_get.return_value = mock_get_response
        migrate_data_set(self.data_set_mapping['old_data_set'],
                         self.data_set_mapping['new_data_set'],
                         self.data_set_mapping["data_mapping"])
        new_data_set = DataSet.objects.get(name='scooters_a_type')
        new_data_set_serialised = dict(new_data_set.serialize())
        del new_data_set_serialised['schema']
        assert_equal(new_data_set_serialised, self.new_dataset_config)

    @mock.patch("performanceplatform.client.DataSet.get")
    @mock.patch("performanceplatform.client.DataSet.post")
    def test_handles_new_data_set_already_exists(
            self, client_post, client_get):
        mock_get_response = mock.Mock()
        mock_get_response.json.return_value = self.existing_data
        client_get.return_value = mock_get_response
        migrate_data_set(self.data_set_mapping_new_exists['old_data_set'],
                         self.data_set_mapping_new_exists['new_data_set'],
                         self.data_set_mapping_new_exists["data_mapping"])
        new_data_set = DataSet.objects.get(name='realtime-mowers')
        new_data_set_serialised = dict(new_data_set.serialize())
        del new_data_set_serialised['schema']
        assert_equal(new_data_set_serialised,
                     self.new_dataset_config_already_exists)

    @mock.patch("performanceplatform.client.DataSet.get")
    @mock.patch("performanceplatform.client.DataSet.post")
    def test_correct_data_posted_to_new_data_set_given_response(
            self, client_post, client_get):
        mock_get_response = mock.Mock()
        mock_get_response.json.return_value = self.existing_data
        client_get.return_value = mock_get_response
        migrate_data_set(self.data_set_mapping['old_data_set'],
                         self.data_set_mapping['new_data_set'],
                         self.data_set_mapping["data_mapping"])
        client_post.assert_called_once_with(self.newly_mapped_data['data'])
