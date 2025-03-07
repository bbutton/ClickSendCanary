import unittest
from unittest.mock import patch, MagicMock, ANY
import os
import sys
import json
import boto3
from botocore.exceptions import ClientError

# Import the module to test
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import athena_repair_lambda
from athena_repair_lambda import lambda_handler, get_configuration, execute_msck_repair, wait_for_query_completion, AthenaQueryError

class TestAthenaRepairLambda(unittest.TestCase):

    def setUp(self):
        # Set up test environment variables
        os.environ["ATHENA_DATABASE"] = "test-database"
        os.environ["ATHENA_TABLE"] = "test-table"
        os.environ["ATHENA_WORKGROUP"] = "test-workgroup"
        os.environ["S3_OUTPUT_BUCKET"] = "test-bucket"
        os.environ["S3_OUTPUT_PREFIX"] = "test-prefix/"

        # Expected config dictionary based on environment variables
        self.expected_config = {
            "ATHENA_DATABASE": "test-database",
            "ATHENA_TABLE": "test-table",
            "ATHENA_WORKGROUP": "test-workgroup",
            "S3_OUTPUT_BUCKET": "test-bucket",
            "S3_OUTPUT_PREFIX": "test-prefix/"
        }

        # Sample Athena response for successful query start
        self.start_query_response = {
            "QueryExecutionId": "test-execution-id"
        }

        # Sample query execution response states
        self.query_running_response = {
            "QueryExecution": {
                "Status": {
                    "State": "RUNNING"
                }
            }
        }

        self.query_succeeded_response = {
            "QueryExecution": {
                "Status": {
                    "State": "SUCCEEDED"
                }
            }
        }

        self.query_failed_response = {
            "QueryExecution": {
                "Status": {
                    "State": "FAILED",
                    "StateChangeReason": "Test failure reason"
                }
            }
        }

    def tearDown(self):
        # Clean up environment variables
        for key in list(os.environ.keys()):
            if key in [
                "ATHENA_DATABASE",
                "ATHENA_TABLE",
                "ATHENA_WORKGROUP",
                "S3_OUTPUT_BUCKET",
                "S3_OUTPUT_PREFIX"
            ]:
                del os.environ[key]

    def test_get_configuration_success(self):
        # Act
        config = get_configuration()

        # Assert
        self.assertEqual(config, self.expected_config)

    def test_get_configuration_missing_vars(self):
        # Arrange
        del os.environ["ATHENA_DATABASE"]

        # Act & Assert
        with self.assertRaises(ValueError) as context:
            get_configuration()

        self.assertIn("Missing required environment variables", str(context.exception))
        self.assertIn("ATHENA_DATABASE", str(context.exception))

    @patch('boto3.client')
    def test_execute_msck_repair_success(self, mock_boto3_client):
        # Arrange
        mock_athena = MagicMock()
        mock_athena.start_query_execution.return_value = self.start_query_response
        mock_boto3_client.return_value = mock_athena

        # Act
        query_id = execute_msck_repair(self.expected_config)

        # Assert
        self.assertEqual(query_id, "test-execution-id")
        mock_athena.start_query_execution.assert_called_once_with(
            QueryString="MSCK REPAIR TABLE test-database.test-table;",
            QueryExecutionContext={
                'Database': 'test-database'
            },
            ResultConfiguration={
                'OutputLocation': 's3://test-bucket/test-prefix/'
            },
            WorkGroup='test-workgroup'
        )

    @patch('boto3.client')
    def test_execute_msck_repair_error(self, mock_boto3_client):
        # Arrange
        mock_athena = MagicMock()
        mock_athena.start_query_execution.side_effect = Exception("Test error")
        mock_boto3_client.return_value = mock_athena

        # Act & Assert
        with self.assertRaises(AthenaQueryError) as context:
            execute_msck_repair(self.expected_config)

        self.assertIn("Failed to execute Athena query", str(context.exception))

    @patch('boto3.client')
    @patch('time.sleep')
    def test_wait_for_query_completion_success(self, mock_sleep, mock_boto3_client):
        # Arrange
        mock_athena = MagicMock()
        mock_athena.get_query_execution.side_effect = [
            self.query_running_response,
            self.query_succeeded_response
        ]
        mock_boto3_client.return_value = mock_athena

        # Act
        state = wait_for_query_completion("test-execution-id", self.expected_config)

        # Assert
        self.assertEqual(state, "SUCCEEDED")
        self.assertEqual(mock_athena.get_query_execution.call_count, 2)
        mock_athena.get_query_execution.assert_called_with(
            QueryExecutionId="test-execution-id"
        )
        mock_sleep.assert_called_once()

    @patch('boto3.client')
    @patch('time.sleep')
    def test_wait_for_query_completion_failure(self, mock_sleep, mock_boto3_client):
        # Arrange
        mock_athena = MagicMock()
        mock_athena.get_query_execution.return_value = self.query_failed_response
        mock_boto3_client.return_value = mock_athena

        # Act & Assert
        with self.assertRaises(AthenaQueryError) as context:
            wait_for_query_completion("test-execution-id", self.expected_config)

        self.assertIn("Query execution failed", str(context.exception))
        self.assertIn("Test failure reason", str(context.exception))

    @patch('boto3.client')
    @patch('time.sleep')
    def test_wait_for_query_completion_timeout(self, mock_sleep, mock_boto3_client):
        # Arrange
        mock_athena = MagicMock()
        # Always return RUNNING to force timeout
        mock_athena.get_query_execution.return_value = self.query_running_response
        mock_boto3_client.return_value = mock_athena

        # Act & Assert
        with self.assertRaises(AthenaQueryError) as context:
            # Use a short max_wait_seconds to avoid long test
            wait_for_query_completion("test-execution-id", self.expected_config, max_wait_seconds=3, polling_interval=1)

        self.assertIn("Query execution timed out", str(context.exception))

    @patch('athena_repair_lambda.get_configuration')
    @patch('athena_repair_lambda.execute_msck_repair')
    @patch('athena_repair_lambda.wait_for_query_completion')
    def test_lambda_handler_success(self, mock_wait, mock_execute, mock_get_config):
        # Arrange
        mock_get_config.return_value = self.expected_config
        mock_execute.return_value = "test-execution-id"
        mock_wait.return_value = "SUCCEEDED"

        # Act
        result = lambda_handler({}, {})

        # Assert
        self.assertEqual(result["statusCode"], 200)
        response_body = json.loads(result["body"])
        self.assertEqual(response_body["message"], "MSCK REPAIR executed successfully")
        self.assertEqual(response_body["queryExecutionId"], "test-execution-id")
        self.assertEqual(response_body["state"], "SUCCEEDED")

        # Verify function calls
        mock_get_config.assert_called_once()
        mock_execute.assert_called_once_with(self.expected_config)
        mock_wait.assert_called_once_with("test-execution-id", self.expected_config)

    @patch('athena_repair_lambda.get_configuration')
    @patch('athena_repair_lambda.execute_msck_repair')
    def test_lambda_handler_athena_error(self, mock_execute, mock_get_config):
        # Arrange
        mock_get_config.return_value = self.expected_config
        mock_execute.side_effect = AthenaQueryError("Test Athena error")

        # Act
        result = lambda_handler({}, {})

        # Assert
        self.assertEqual(result["statusCode"], 500)
        response_body = json.loads(result["body"])
        self.assertEqual(response_body["error"], "Failed to execute MSCK REPAIR query")
        self.assertEqual(response_body["details"], "Test Athena error")

    @patch('athena_repair_lambda.get_configuration')
    def test_lambda_handler_unexpected_error(self, mock_get_config):
        # Arrange
        mock_get_config.side_effect = Exception("Unexpected test error")

        # Act
        result = lambda_handler({}, {})

        # Assert
        self.assertEqual(result["statusCode"], 500)
        response_body = json.loads(result["body"])
        self.assertEqual(response_body["error"], "Unexpected error occurred")
        self.assertEqual(response_body["details"], "Unexpected test error")


if __name__ == '__main__':
    unittest.main()
