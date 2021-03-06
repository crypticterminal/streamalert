"""
Copyright 2017-present, Airbnb Inc.

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

   http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
"""
# pylint: disable=attribute-defined-outside-init,protected-access
import json
import os

from mock import Mock, patch
from nose.tools import assert_equal, assert_raises, assert_true, raises

from stream_alert.athena_partition_refresh.main import AthenaRefresher, AthenaRefreshError
from stream_alert.shared.config import load_config

from tests.unit.helpers.aws_mocks import MockAthenaClient


# Without this time.sleep patch, backoff performs sleep
# operations and drastically slows down testing
@patch('time.sleep', Mock())
class TestAthenaRefresher(object):
    """Test class for AthenaRefresher"""

    @patch('stream_alert.athena_partition_refresh.main.load_config',
           Mock(return_value=load_config('tests/unit/conf/')))
    @patch.dict(os.environ, {'AWS_DEFAULT_REGION': 'us-east-1'})
    @patch('stream_alert.shared.athena.boto3')
    def setup(self, boto_patch):
        """Setup the AthenaRefresher tests"""
        boto_patch.client.return_value = MockAthenaClient()
        self._refresher = AthenaRefresher()

    def test_add_partitions(self):
        """AthenaRefresher - Add Partitions"""
        self._refresher._s3_buckets_and_keys = {
            'unit-testing.streamalerts': {
                'alerts/dt=2017-08-26-14/rule_name_alerts-1304134918401.json',
                'alerts/dt=2017-08-27-14/rule_name_alerts-1304134918401.json'
            },
            'unit-testing.streamalert.data': {
                'log_type_1/2017/08/26/14/test-data-11111-22222-33333.snappy',
                'log_type_2/2017/08/26/14/test-data-11111-22222-33333.snappy',
                'log_type_2/2017/08/26/15/test-data-11111-22222-33333.snappy',
                'log_type_2/2017/08/26/16/test-data-11111-22222-33333.snappy',
                'log_type_3/2017/08/26/14/test-data-11111-22222-33333.snappy',
                'log_type_1/2017/08/26/11/test-data-11111-22222-33333.snappy'
            },
            'test-bucket-with-data': {
                '2017/08/26/14/rule_name_alerts-1304134918401.json',
                '2017/08/28/14/rule_name_alerts-1304134918401.json',
                '2017/07/30/14/rule_name_alerts-1304134918401.json'
            }
        }
        result = self._refresher._add_partitions()

        assert_true(result)

    @patch('logging.Logger.error')
    def test_add_partitions_none(self, log_mock):
        """AthenaRefresher - Add Partitions, None to Add"""
        result = self._refresher._add_partitions()
        log_mock.assert_called_with('No partitons to add')
        assert_equal(result, False)

    def test_get_partitions_from_keys(self):
        """AthenaRefresher - Get Partitions From Keys"""
        expected_result = {
            'alerts': {
                '(dt = \'2017-08-26-14\')': ('\'s3://unit-testing.streamalerts/'
                                             'alerts/dt=2017-08-26-14\''),
                '(dt = \'2017-08-27-14\')': ('\'s3://unit-testing.streamalerts/'
                                             'alerts/dt=2017-08-27-14\''),
                '(dt = \'2017-08-26-15\')': ('\'s3://unit-testing.streamalerts/'
                                             'alerts/2017/08/26/15\'')
            },
            'log_type_1': {
                '(dt = \'2017-08-26-14\')': ('\'s3://unit-testing.streamalert.data/'
                                             'log_type_1/2017/08/26/14\'')
            },
            'log_type_2': {
                '(dt = \'2017-08-26-14\')': ('\'s3://unit-testing.streamalert.data/'
                                             'log_type_2/2017/08/26/14\''),
                '(dt = \'2017-08-26-15\')': ('\'s3://unit-testing.streamalert.data/'
                                             'log_type_2/2017/08/26/15\''),
                '(dt = \'2017-08-26-16\')': ('\'s3://unit-testing.streamalert.data/'
                                             'log_type_2/2017/08/26/16\''),
            },
            'log_type_3': {
                '(dt = \'2017-08-26-14\')': ('\'s3://unit-testing.streamalert.data/'
                                             'log_type_3/2017/08/26/14\''),
            }
        }

        self._refresher._s3_buckets_and_keys = {
            'unit-testing.streamalerts': {
                'alerts/dt=2017-08-26-14/rule_name_alerts-1304134918401.json',
                'alerts/dt=2017-08-27-14/rule_name_alerts-1304134918401.json',
                'alerts/2017/08/26/15/rule_name_alerts-1304134918401.json'
            },
            'unit-testing.streamalert.data': {
                'log_type_1/2017/08/26/14/test-data-11111-22222-33333.snappy',
                'log_type_2/2017/08/26/14/test-data-11111-22222-33333.snappy',
                'log_type_2/2017/08/26/14/test-data-11111-22222-33334.snappy',
                'log_type_2/2017/08/26/15/test-data-11111-22222-33333.snappy',
                'log_type_2/2017/08/26/16/test-data-11111-22222-33333.snappy',
                'log_type_3/2017/08/26/14/test-data-11111-22222-33333.snappy',
            },
            'test-bucket-with-data': {
                '2017/08/26/14/rule_name_alerts-1304134918401.json',
                '2017/07/30/14/rule_name_alerts-1304134918401.json'
            }
        }

        result = self._refresher._get_partitions_from_keys()

        assert_equal(result, expected_result)

    @patch('logging.Logger.error')
    def test_get_partitions_from_keys_error(self, log_mock):
        """AthenaRefresher - Get Partitions From Keys, Bad Key"""
        bad_key = 'bad_match_string'
        self._refresher._s3_buckets_and_keys = {
            'unit-testing.streamalerts': {
                bad_key
            }
        }

        result = self._refresher._get_partitions_from_keys()

        log_mock.assert_called_with('The key %s does not match any regex, skipping', bad_key)
        assert_equal(result, dict())

    @staticmethod
    def _s3_record(count):
        return {
            'Records': [
                {
                    's3': {
                        'bucket': {
                            'name': 'unit-testing.streamalerts'
                        },
                        'object': {
                            'key': ('alerts/dt=2017/08/{:02d}/'
                                    '14/02/test.json'.format(val+1))
                        }
                    }
                } for val in range(count)
            ]
        }

    @staticmethod
    def _create_test_message(count=2):
        """Helper function for creating an sqs messsage body"""
        count = min(count, 30)
        return {
            'Records': [
                {
                    'body': json.dumps(TestAthenaRefresher._s3_record(count)),
                    'messageId': "40d4fac0-64a1-4a20-8be4-893c51aebca1",
                    "attributes": {
                        "SentTimestamp": "1534284301036"
                    }
                }
            ]
        }

    @patch('logging.Logger.debug')
    @patch('stream_alert.athena_partition_refresh.main.AthenaRefresher._add_partitions')
    def test_run(self, add_mock, log_mock):
        """AthenaRefresher - Run"""
        add_mock.return_value = True
        self._refresher.run(self._create_test_message(1))
        log_mock.assert_called_with(
            'Received notification for object \'%s\' in bucket \'%s\'',
            'alerts/dt=2017/08/01/14/02/test.json',
            'unit-testing.streamalerts'
        )

    @raises(AthenaRefreshError)
    def test_run_no_messages(self):
        """AthenaRefresher - Run, No Messages"""
        self._refresher.run(self._create_test_message(0))

    @patch('logging.Logger.error')
    def test_run_invalid_bucket(self, log_mock):
        """AthenaRefresher - Run, Bad Bucket Name"""
        event = self._create_test_message(0)
        s3_record = self._s3_record(1)
        s3_record['Records'][0]['s3']['bucket']['name'] = 'bad.bucket.name'
        event['Records'][0]['body'] = json.dumps(s3_record)
        assert_raises(AthenaRefreshError, self._refresher.run, event)
        log_mock.assert_called_with('No partitons to add')
