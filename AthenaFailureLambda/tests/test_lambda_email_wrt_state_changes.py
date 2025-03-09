import unittest
from unittest.mock import MagicMock, patch
import json
import datetime
import boto3
import sys
import os
from botocore.exceptions import ClientError

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from src.state_manager import StateManager, StateError
from athena_failure import lambda_handler, send_alert_email, execute_failure_detection_query

class TestAthenaFailureLambdaEmails(unittest.TestCase):

    def setUp(self):
        # Set up environment variables
        os.environ["ATHENA_WORKGROUP"] = "test-workgroup"
        os.environ["SES_SOURCE_EMAIL"] = "test@example.com"
        os.environ["ALERT_RECIPIENTS"] = "recipient1@example.com, recipient2@example.com"

        # Mock AWS clients
        self.mock_athena = MagicMock()
        self.mock_s3 = MagicMock()
        self.mock_ses = MagicMock()

        # Set up patcher for boto3.client
        self.boto3_patcher = patch('boto3.client')
        self.mock_boto3 = self.boto3_patcher.start()
        self.mock_boto3.side_effect = lambda service, **kwargs: {
            'athena': self.mock_athena,
            's3': self.mock_s3,
            'ses': self.mock_ses
        }.get(service, MagicMock())

        # Mock the state_manager
        self.state_manager_patcher = patch('src.state_manager.StateManager')
        self.mock_state_manager_class = self.state_manager_patcher.start()
        self.mock_state_manager = MagicMock()
        self.mock_state_manager_class.return_value = self.mock_state_manager

        # Mock the execute_failure_detection_query function
        self.query_patcher = patch('athena_failure.execute_failure_detection_query')
        self.mock_query = self.query_patcher.start()

        # Mock the send_alert_email function
        self.email_patcher = patch('athena_failure.send_alert_email')
        self.mock_send_email = self.email_patcher.start()

    def tearDown(self):
        # Stop all patchers
        self.boto3_patcher.stop()
        self.state_manager_patcher.stop()
        self.query_patcher.stop()
        self.email_patcher.stop()

        # Clear environment variables
        for env_var in ["ATHENA_WORKGROUP", "SES_SOURCE_EMAIL", "ALERT_RECIPIENTS"]:
            if env_var in os.environ:
                del os.environ[env_var]


    def test_email_sent_when_alert_state_changes(self):
        query_result = {
            "alert_level": "WARNING",
            "total_messages": "100",
            "failed_messages": "5",
            "failure_rate": "5.0"
        }
        self.mock_query.return_value = query_result

        self.mock_s3.list_objects_v2.return_value = {'KeyCount': 1}
        self.mock_s3.get_object.return_value = {
            'Body': MagicMock(read=lambda: json.dumps({
                "alert_level": "OK",
                "timestamp": "2022-12-31 23:50:00"
            }).encode('utf-8'))
        }
        self.mock_s3.put_object.return_value = {'ResponseMetadata': {'HTTPStatusCode': 200}}

        result = lambda_handler({}, {})

        self.assertEqual(result["statusCode"], 200)
        self.mock_send_email.assert_called_once()


    def test_no_email_sent_when_alert_state_unchanged(self):
        query_result = {
            "alert_level": "WARNING",
            "total_messages": "100",
            "failed_messages": "5",
            "failure_rate": "5.0"
        }
        self.mock_query.return_value = query_result

        self.mock_s3.list_objects_v2.return_value = {'KeyCount': 1}
        self.mock_s3.get_object.return_value = {
            'Body': MagicMock(read=lambda: json.dumps({
                "alert_level": "WARNING",
                "timestamp": "2022-12-31 23:50:00"
            }).encode('utf-8'))
        }
        self.mock_s3.put_object.return_value = {'ResponseMetadata': {'HTTPStatusCode': 200}}

        result = lambda_handler({}, {})

        self.assertEqual(result["statusCode"], 200)
        self.mock_send_email.assert_not_called()


    def test_email_sent_on_first_run(self):
        query_result = {
            "alert_level": "WARNING",
            "total_messages": "100",
            "failed_messages": "5",
            "failure_rate": "5.0"
        }
        self.mock_query.return_value = query_result

        self.mock_s3.list_objects_v2.return_value = {'KeyCount': 0}
        self.mock_s3.put_object.return_value = {'ResponseMetadata': {'HTTPStatusCode': 200}}

        result = lambda_handler({}, {})

        self.assertEqual(result["statusCode"], 200)
        self.mock_send_email.assert_called_once()
