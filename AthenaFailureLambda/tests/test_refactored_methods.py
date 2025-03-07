import unittest
from unittest.mock import MagicMock, patch, ANY
import json
import os
import sys
import boto3
from botocore.exceptions import ClientError

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Import the module to test
from athena_failure import (
    lambda_handler,
    execute_failure_detection_query,
    start_athena_query,
    get_failure_detection_query,
    wait_for_query_completion,
    parse_query_results,
    prepare_email_config,
    create_success_response,
    create_error_response,
    AthenaQueryError,
    EmailSendError
)


class TestAthenaFailureLambda(unittest.TestCase):

    def setUp(self):
        # Set up environment variables for testing
        os.environ["ATHENA_WORKGROUP"] = "test-workgroup"
        os.environ["SES_SOURCE_EMAIL"] = "test@example.com"
        os.environ["ALERT_RECIPIENTS"] = "recipient1@example.com, recipient2@example.com"

        # Mock AWS clients
        self.mock_athena = MagicMock()
        self.mock_ses = MagicMock()

        # Sample query result
        self.sample_query_result = {
            "total_messages": "100",
            "failed_messages": "5",
            "failure_rate": "5.0",
            "alert_level": "WARNING"
        }

        # Sample Athena response
        self.sample_athena_response = {
            "ResultSet": {
                "Rows": [
                    {"Data": [{"VarCharValue": "total_messages"}, {"VarCharValue": "failed_messages"},
                              {"VarCharValue": "failure_rate"}, {"VarCharValue": "alert_level"}]},
                    {"Data": [{"VarCharValue": "100"}, {"VarCharValue": "5"},
                              {"VarCharValue": "5.0"}, {"VarCharValue": "WARNING"}]}
                ]
            }
        }

    def tearDown(self):
        # Clean up environment variables
        for env_var in ["ATHENA_WORKGROUP", "SES_SOURCE_EMAIL", "ALERT_RECIPIENTS"]:
            if env_var in os.environ:
                del os.environ[env_var]

    @patch('athena_failure.boto3.client')
    @patch('athena_failure.execute_failure_detection_query')
    @patch('athena_failure.prepare_email_config')
    @patch('athena_failure.send_alert_email')
    def test_lambda_handler_success(self, mock_send_email, mock_prepare_config,
                                    mock_execute_query, mock_boto3_client):
        # Arrange
        mock_boto3_client.side_effect = lambda service, **kwargs: {
            'athena': self.mock_athena,
            'ses': self.mock_ses
        }[service]

        mock_execute_query.return_value = self.sample_query_result
        mock_prepare_config.return_value = {
            "source_email": "test@example.com",
            "recipients": ["recipient1@example.com", "recipient2@example.com"]
        }

        # Act
        result = lambda_handler({}, {})

        # Assert
        self.assertEqual(result["statusCode"], 200)
        response_body = json.loads(result["body"])
        self.assertEqual(response_body["message"], "Function executed successfully")
        self.assertEqual(response_body["result"], self.sample_query_result)

        # Verify function calls
        mock_execute_query.assert_called_once_with(self.mock_athena)
        mock_prepare_config.assert_called_once()
        mock_send_email.assert_called_once()

    @patch('athena_failure.boto3.client')
    @patch('athena_failure.execute_failure_detection_query')
    def test_lambda_handler_athena_error(self, mock_execute_query, mock_boto3_client):
        # Arrange
        mock_boto3_client.side_effect = lambda service, **kwargs: {
            'athena': self.mock_athena,
            'ses': self.mock_ses
        }[service]

        error_message = "Athena query failed"
        mock_execute_query.side_effect = AthenaQueryError(error_message)

        # Act
        result = lambda_handler({}, {})

        # Assert
        self.assertEqual(result["statusCode"], 500)
        response_body = json.loads(result["body"])
        self.assertIn("Athena query failed", response_body["error"])

    def test_get_failure_detection_query(self):
        # Act
        query = get_failure_detection_query()

        # Assert
        self.assertIn("SELECT", query)
        self.assertIn("FROM clicksend_canary.sms_logs", query)
        self.assertIn("WHERE from_unixtime(sent_date)", query)
        self.assertIn("CASE", query)
        self.assertIn("WHEN", query)
        self.assertIn("CRITICAL", query)
        self.assertIn("WARNING", query)

    @patch('athena_failure.get_failure_detection_query')
    def test_start_athena_query(self, mock_get_query):
        # Arrange
        mock_get_query.return_value = "SELECT * FROM test_table"
        self.mock_athena.start_query_execution.return_value = {
            "QueryExecutionId": "test-execution-id"
        }

        # Act
        execution_id = start_athena_query(self.mock_athena)

        # Assert
        self.assertEqual(execution_id, "test-execution-id")
        self.mock_athena.start_query_execution.assert_called_once_with(
            QueryString=mock_get_query.return_value,
            WorkGroup="test-workgroup"
        )

    @patch('athena_failure.time.sleep')
    def test_wait_for_query_completion_success(self, mock_sleep):
        # Arrange
        self.mock_athena.get_query_execution.return_value = {
            "QueryExecution": {
                "Status": {
                    "State": "SUCCEEDED"
                }
            }
        }

        # Act
        wait_for_query_completion(self.mock_athena, "test-execution-id")

        # Assert
        self.mock_athena.get_query_execution.assert_called_with(
            QueryExecutionId="test-execution-id"
        )
        mock_sleep.assert_not_called()  # Should not sleep if query succeeds immediately

    @patch('athena_failure.time.sleep')
    def test_wait_for_query_completion_with_waiting(self, mock_sleep):
        # Arrange
        # First call returns RUNNING, second call returns SUCCEEDED
        self.mock_athena.get_query_execution.side_effect = [
            {
                "QueryExecution": {
                    "Status": {
                        "State": "RUNNING"
                    }
                }
            },
            {
                "QueryExecution": {
                    "Status": {
                        "State": "SUCCEEDED"
                    }
                }
            }
        ]

        # Act
        wait_for_query_completion(self.mock_athena, "test-execution-id")

        # Assert
        self.assertEqual(self.mock_athena.get_query_execution.call_count, 2)
        mock_sleep.assert_called_once_with(1)

    @patch('athena_failure.time.sleep')
    def test_wait_for_query_completion_failure(self, mock_sleep):
        # Arrange
        self.mock_athena.get_query_execution.return_value = {
            "QueryExecution": {
                "Status": {
                    "State": "FAILED"
                }
            }
        }

        # Act & Assert
        with self.assertRaises(AthenaQueryError):
            wait_for_query_completion(self.mock_athena, "test-execution-id")

    def test_parse_query_results(self):
        # Arrange
        self.mock_athena.get_query_results.return_value = self.sample_athena_response

        # Act
        result = parse_query_results(self.mock_athena, "test-execution-id")

        # Assert
        self.assertEqual(result, self.sample_query_result)
        self.mock_athena.get_query_results.assert_called_once_with(
            QueryExecutionId="test-execution-id"
        )

    def test_prepare_email_config(self):
        # Act
        config = prepare_email_config()

        # Assert
        self.assertEqual(config["source_email"], "test@example.com")
        self.assertEqual(config["recipients"], ["recipient1@example.com", "recipient2@example.com"])

    def test_prepare_email_config_missing_env_vars(self):
        # Arrange
        del os.environ["SES_SOURCE_EMAIL"]

        # Act & Assert
        with self.assertRaises(EmailSendError):
            prepare_email_config()

    def test_prepare_email_config_empty_recipients(self):
        # Arrange
        os.environ["ALERT_RECIPIENTS"] = "  ,  "

        # Act & Assert
        with self.assertRaises(EmailSendError):
            prepare_email_config()

    def test_create_success_response(self):
        # Act
        response = create_success_response(self.sample_query_result)

        # Assert
        self.assertEqual(response["statusCode"], 200)
        body = json.loads(response["body"])
        self.assertEqual(body["message"], "Function executed successfully")
        self.assertEqual(body["result"], self.sample_query_result)

    def test_create_error_response(self):
        # Arrange
        exception = Exception("Test error")

        # Act
        response = create_error_response(exception, 500, "Test error message")

        # Assert
        self.assertEqual(response["statusCode"], 500)
        body = json.loads(response["body"])
        self.assertEqual(body["error"], "Test error message")
        self.assertEqual(body["details"], "Test error")
        self.assertIn("stack_trace", body)

    @patch('athena_failure.start_athena_query')
    @patch('athena_failure.wait_for_query_completion')
    @patch('athena_failure.parse_query_results')
    def test_execute_failure_detection_query(self, mock_parse, mock_wait, mock_start):
        # Arrange
        mock_start.return_value = "test-execution-id"
        mock_parse.return_value = self.sample_query_result

        # Act
        result = execute_failure_detection_query(self.mock_athena)

        # Assert
        self.assertEqual(result, self.sample_query_result)
        mock_start.assert_called_once_with(self.mock_athena)
        mock_wait.assert_called_once_with(self.mock_athena, "test-execution-id")
        mock_parse.assert_called_once_with(self.mock_athena, "test-execution-id")

    @patch('athena_failure.start_athena_query')
    def test_execute_failure_detection_query_error(self, mock_start):
        # Arrange
        mock_start.side_effect = Exception("Test error")

        # Act & Assert
        with self.assertRaises(AthenaQueryError):
            execute_failure_detection_query(self.mock_athena)


if __name__ == '__main__':
    unittest.main()