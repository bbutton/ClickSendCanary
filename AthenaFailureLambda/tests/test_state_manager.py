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

class TestStateManager(unittest.TestCase):

    def setUp(self):
        # Create a mock S3 client
        self.mock_s3 = MagicMock()

        # Create the StateManager with the mock client
        self.state_manager = StateManager(
            s3_client=self.mock_s3,
            bucket_name="test-bucket",
            state_key="test-state.json",
            history_key="test-history.jsonl"
        )

        # Sample states for testing
        self.ok_state = {"alert_level": "OK", "timestamp": "2023-01-01 00:00:00",
                         "total_messages": "100", "failed_messages": "0", "failure_rate": "0.0"}

        self.warning_state = {"alert_level": "WARNING", "timestamp": "2023-01-01 00:10:00",
                              "total_messages": "100", "failed_messages": "5", "failure_rate": "5.0"}

        self.critical_state = {"alert_level": "CRITICAL", "timestamp": "2023-01-01 00:20:00",
                               "total_messages": "100", "failed_messages": "30", "failure_rate": "30.0"}

        # Sample query result
        self.sample_query_result = {
            "total_messages": "100",
            "failed_messages": "5",
            "failure_rate": "5.0",
            "alert_level": "WARNING"
        }

    # Tests for get_previous_state
    def test_exception_thrown_when_get_object_fails(self):
        self.mock_s3.get_object.side_effect = Exception("S3 error")

        with self.assertRaises(Exception):
            self.state_manager.get_previous_state()

        self.mock_s3.get_object.assert_called_once_with(
            Bucket="test-bucket",
            Key="test-state.json"
        )

    def test_previous_state_returned_when_state_file_exists(self):
        self.mock_s3.get_object.return_value = {
            'Body': MagicMock(read=lambda: json.dumps(self.ok_state).encode('utf-8'))
        }

        result = self.state_manager.get_previous_state()

        self.assertEqual(result, self.ok_state)
        self.mock_s3.get_object.assert_called_once_with(
            Bucket="test-bucket",
            Key="test-state.json"
        )

    # Tests for update_current_state
    def test_true_returned_when_s3_put_succeeds(self):
        self.mock_s3.put_object.return_value = {'ResponseMetadata': {'HTTPStatusCode': 200}}

        result = self.state_manager.update_current_state(self.warning_state)

        self.assertTrue(result)
        self.mock_s3.put_object.assert_called_once_with(
            Bucket="test-bucket",
            Key="test-state.json",
            Body=json.dumps(self.warning_state),
            ContentType="application/json"
        )

    def test_false_returned_when_s3_put_fails(self):
        self.mock_s3.put_object.side_effect = Exception("S3 error")

        result = self.state_manager.update_current_state(self.warning_state)

        self.assertFalse(result)
        self.mock_s3.put_object.assert_called_once_with(
            Bucket="test-bucket",
            Key="test-state.json",
            Body=json.dumps(self.warning_state),
            ContentType="application/json"
        )

    # Tests for does_state_file_exist
    def test_true_returned_when_state_file_exists(self):
        self.mock_s3.list_objects_v2.return_value = {'KeyCount': 1}

        result = self.state_manager.does_state_file_exist()

        self.assertTrue(result)
        self.mock_s3.list_objects_v2.assert_called_once_with(
            Bucket="test-bucket",
            Prefix="test-state.json",
            MaxKeys=1
        )

    def test_false_returned_when_state_file_does_not_exist(self):
        self.mock_s3.list_objects_v2.return_value = {'KeyCount': 0}

        result = self.state_manager.does_state_file_exist()

        self.assertFalse(result)
        self.mock_s3.list_objects_v2.assert_called_once_with(
            Bucket="test-bucket",
            Prefix="test-state.json",
            MaxKeys=1
        )

    # Tests for does_history_file_exist
    def test_true_returned_when_history_file_exists(self):
        self.mock_s3.list_objects_v2.return_value = {'KeyCount': 1}

        result = self.state_manager.does_history_file_exist()

        self.assertTrue(result)
        self.mock_s3.list_objects_v2.assert_called_once_with(
            Bucket="test-bucket",
            Prefix="test-history.jsonl",
            MaxKeys=1
        )

    def test_false_returned_when_history_file_does_not_exist(self):
        self.mock_s3.list_objects_v2.return_value = {'KeyCount': 0}

        result = self.state_manager.does_history_file_exist()

        self.assertFalse(result)
        self.mock_s3.list_objects_v2.assert_called_once_with(
            Bucket="test-bucket",
            Prefix="test-history.jsonl",
            MaxKeys=1
        )

    # Tests for add_to_state_history
    def test_new_history_file_created_when_file_does_not_exist(self):
        # History file doesn't exist
        self.state_manager.does_history_file_exist = MagicMock(return_value=False)
        self.mock_s3.put_object.return_value = {'ResponseMetadata': {'HTTPStatusCode': 200}}

        result = self.state_manager.add_to_state_history(self.warning_state)

        self.assertTrue(result)
        self.mock_s3.put_object.assert_called_once_with(
            Bucket="test-bucket",
            Key="test-history.jsonl",
            Body=json.dumps(self.warning_state) + "\n",
            ContentType="application/jsonl"
        )

    def test_record_appended_when_history_file_exists(self):
        # History file exists
        self.state_manager.does_history_file_exist = MagicMock(return_value=True)
        existing_content = json.dumps(self.ok_state) + "\n"
        self.mock_s3.get_object.return_value = {
            'Body': MagicMock(read=lambda: existing_content.encode('utf-8'))
        }
        self.mock_s3.put_object.return_value = {'ResponseMetadata': {'HTTPStatusCode': 200}}

        result = self.state_manager.add_to_state_history(self.warning_state)

        self.assertTrue(result)
        expected_content = existing_content + json.dumps(self.warning_state) + "\n"
        self.mock_s3.put_object.assert_called_once_with(
            Bucket="test-bucket",
            Key="test-history.jsonl",
            Body=expected_content,
            ContentType="application/jsonl"
        )

    def test_false_returned_when_history_update_fails(self):
        self.state_manager.does_history_file_exist = MagicMock(return_value=False)
        self.mock_s3.put_object.side_effect = Exception("S3 error")

        result = self.state_manager.add_to_state_history(self.warning_state)

        self.assertFalse(result)

    # Tests for has_state_changed
    def test_true_returned_when_alert_level_changes(self):
        result = self.state_manager.has_state_changed(self.warning_state, self.ok_state)

        self.assertTrue(result)

    def test_false_returned_when_alert_level_unchanged(self):
        result = self.state_manager.has_state_changed(self.ok_state, self.ok_state)

        self.assertFalse(result)

    def test_true_returned_when_alert_level_missing(self):
        incomplete_state = {"timestamp": "2023-01-01 00:00:00"}

        result = self.state_manager.has_state_changed(incomplete_state, self.ok_state)

        self.assertTrue(result)

    # Tests for create_state_record
    def test_state_record_created_with_timestamp_and_metrics(self):
        # Mock datetime directly in the StateManager method
        original_datetime = datetime.datetime

        try:
            # Create a mock that will replace datetime.datetime
            mock_dt = MagicMock()
            mock_dt.utcnow.return_value.strftime.return_value = "2023-01-01 12:00:00"
            datetime.datetime = mock_dt

            state_record = self.state_manager.create_state_record(self.sample_query_result)

            self.assertEqual(state_record["timestamp"], "2023-01-01 12:00:00")
            self.assertEqual(state_record["alert_level"], "WARNING")
            self.assertEqual(state_record["total_messages"], "100")
            self.assertEqual(state_record["failed_messages"], "5")
            self.assertEqual(state_record["failure_rate"], "5.0")
        finally:
            # Restore the original datetime
            datetime.datetime = original_datetime

    def test_default_values_used_when_metrics_missing(self):
        incomplete_result = {"alert_level": "OK"}

        state_record = self.state_manager.create_state_record(incomplete_result)

        self.assertEqual(state_record["alert_level"], "OK")
        self.assertEqual(state_record["total_messages"], "0")
        self.assertEqual(state_record["failed_messages"], "0")
        self.assertEqual(state_record["failure_rate"], "0.0")
        self.assertIn("timestamp", state_record)

    # Tests for process_state_change
    def test_unknown_previous_state_used_when_state_file_missing(self):
        self.state_manager.does_state_file_exist = MagicMock(return_value=False)
        self.state_manager.update_current_state = MagicMock(return_value=True)
        self.state_manager.add_to_state_history = MagicMock(return_value=True)

        result = self.state_manager.process_state_change(self.sample_query_result)

        self.assertTrue(result["state_changed"])
        self.assertEqual(result["previous_state"]["alert_level"], "UNKNOWN")
        self.assertEqual(result["current_state"]["alert_level"], "WARNING")
        self.state_manager.add_to_state_history.assert_called_once()

    def test_state_change_detected_when_alert_level_changes(self):
        self.state_manager.does_state_file_exist = MagicMock(return_value=True)
        self.state_manager.get_previous_state = MagicMock(return_value=self.ok_state)
        self.state_manager.update_current_state = MagicMock(return_value=True)
        self.state_manager.add_to_state_history = MagicMock(return_value=True)

        result = self.state_manager.process_state_change(self.sample_query_result)

        self.assertTrue(result["state_changed"])
        self.assertEqual(result["previous_state"]["alert_level"], "OK")
        self.assertEqual(result["current_state"]["alert_level"], "WARNING")
        self.state_manager.add_to_state_history.assert_called_once()

    def test_no_state_change_detected_when_alert_level_same(self):
        self.state_manager.does_state_file_exist = MagicMock(return_value=True)
        self.state_manager.get_previous_state = MagicMock(return_value=self.warning_state)
        self.state_manager.has_state_changed = MagicMock(return_value=False)
        self.state_manager.update_current_state = MagicMock(return_value=True)
        self.state_manager.add_to_state_history = MagicMock()

        result = self.state_manager.process_state_change(self.sample_query_result)

        self.assertFalse(result["state_changed"])
        self.assertEqual(result["previous_state"], self.warning_state)
        self.state_manager.add_to_state_history.assert_not_called()

    def test_current_state_always_updated_regardless_of_change(self):
        scenarios = [
            (True, self.ok_state),  # State changed
            (False, self.warning_state)  # State unchanged
        ]

        for state_changed, previous_state in scenarios:
            with self.subTest(state_changed=state_changed):
                # Setup
                self.state_manager.does_state_file_exist = MagicMock(return_value=True)
                self.state_manager.get_previous_state = MagicMock(return_value=previous_state)
                self.state_manager.has_state_changed = MagicMock(return_value=state_changed)
                self.state_manager.update_current_state = MagicMock(return_value=True)
                self.state_manager.add_to_state_history = MagicMock()

                # Act
                self.state_manager.process_state_change(self.sample_query_result)

                # Assert
                self.state_manager.update_current_state.assert_called_once()


if __name__ == '__main__':
    unittest.main()