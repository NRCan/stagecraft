import mock
from stagecraft.apps.datasets.models import DataGroup, DataSet, DataType
from stagecraft.libs.backdrop_client import disable_backdrop_connection
from stagecraft.libs.purge_varnish import disable_purge_varnish
from django.test import TestCase
from stagecraft.libs.mass_update import migrate_data_set
from nose.tools import assert_equal


class TestDataSetMassUpdate(TestCase):
    fixtures = ['datasets_testschemas.json']

    def setUp(self):
        self.data_set_mapping = {
                'old_name': "data-scootah",
                'new_data_set': {
                        'data_type': "a_type",
                        'name': "new_data_set",
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
                'old_name': "data-scootah",
                'new_data_set': {
                        'data_type': "realtime",
                        'name': "realtime-mowers",
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

        #existing data set config comes from fixture
        self.new_dataset_config = {
            "auto_ids": "foo,bar,baz",
            "bearer_token": "",
            "capped_size": None,
            "created": "2014-06-05 00:00:00",
            "data_group": "scooters",
            "data_type": "a_type",
            "max_age_expected": 86400,
            "modified": "2014-06-05 00:00:00",
            "name": "new_data_set",
            "queryable": True,
            "raw_queries_allowed": True,
            "realtime": False,
            "upload_filters": "backdrop.filter.1",
            "upload_format": ""
        }
        self.new_dataset_config_already_exists = {
            "auto_ids": "foo,bar,baz",
            "bearer_token": "",
            "capped_size": None,
            "created": "2014-06-05 00:00:00",
            "data_group": "mowers",
            "data_type": "realtime",
            "max_age_expected": 86400,
            "modified": "2014-06-05 00:00:00",
            "name": "realtime-mowers",
            "queryable": True,
            "raw_queries_allowed": True,
            "realtime": False,
            "upload_filters": "backdrop.filter.1",
            "upload_format": ""
        }

        self.existing_data = {
            "data": [
              {
                "_day_start_at": "2014-03-10T00:00:00+00:00",
                "_hour_start_at": "2014-03-10T00:00:00+00:00",
                "_id": "MjAxNC0wMy0xMFQwMDowMDowMCswMDowMC5jYV9lX2NsYWltc19yZWNlaXZlZA==",
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
                "_id": "MjAxNC0wNC0xNFQwMDowMDowMCswMDowMC5jYV9lX2NsYWltc19yZWNlaXZlZA==",
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
                "_day_start_at": "2014-03-10T00:00:00+00:00",
                "_hour_start_at": "2014-03-10T00:00:00+00:00",
                "_id": "MjAxNC0wMy0xMFQwMDowMDowMCswMDowMC5jYV9lX2NsYWltc19yZWNlaXZlZA==",
                "_month_start_at": "2014-03-01T00:00:00+00:00",
                "_quarter_start_at": "2014-01-01T00:00:00+00:00",
                "_timestamp": "2014-03-10T00:00:00+00:00",
                "_updated_at": "2014-06-30T13:46:11.446000+00:00",
                "_week_start_at": "2014-03-10T00:00:00+00:00",
                "comment": None,
                "channel": "paper",
                "period": "week",
                "count": 2294.0
              },
              {
                "_day_start_at": "2014-04-14T00:00:00+00:00",
                "_hour_start_at": "2014-04-14T00:00:00+00:00",
                "_id": "MjAxNC0wNC0xNFQwMDowMDowMCswMDowMC5jYV9lX2NsYWltc19yZWNlaXZlZA==",
                "_month_start_at": "2014-04-01T00:00:00+00:00",
                "_quarter_start_at": "2014-04-01T00:00:00+00:00",
                "_timestamp": "2014-04-14T00:00:00+00:00",
                "_updated_at": "2014-06-30T13:46:11.448000+00:00",
                "_week_start_at": "2014-04-14T00:00:00+00:00",
                "comment": None,
                "channel": "digital",
                "period": "week",
                "count": 6822.0
              }
            ]}

    @mock.patch("performanceplatform.client.DataSet.get")
    @mock.patch("performanceplatform.client.DataSet.post")
    def test_correct_new_data_set_created(self, client_post, client_get):
        client_get.return_value = self.existing_data
        migrate_data_set(self.data_set_mapping['old_name'],
                         self.data_set_mapping['new_data_set'],
                         self.data_set_mapping["data_mapping"])
        client_post.assert_called_once_with(self.newly_mapped_data)
        new_data_set = DataSet.objects.get(name='new_data_set')
        assert_equal(new_data_set.serialize(), self.new_dataset_config)

    @mock.patch("performanceplatform.client.DataSet.get")
    @mock.patch("performanceplatform.client.DataSet.post")
    def test_handles_new_data_set_already_exists(self, client_post, client_get):
        client_get.return_value = self.existing_data
        migrate_data_set(self.data_set_mapping_new_exists['old_name'],
                         self.data_set_mapping_new_exists['new_data_set'],
                         self.data_set_mapping_new_exists["data_mapping"])
        client_post.assert_called_once_with(self.newly_mapped_data)
        new_data_set = DataSet.objects.get(name='realtime-mowers')
        assert_equal(new_data_set.serialize(), self.new_dataset_config_already_exists)


    def test_correct_data_posted_to_new_data_set_given_response(self):
        pass


