# tests/test_email_alert.py
import unittest
from unittest.mock import MagicMock
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src import email_alert  # our module to be created

class TestEmailAlert(unittest.TestCase):
    def setUp(self):
        # Create a mock SES client that records calls to send_email
        self.mock_ses_client = MagicMock()
        self.config = {
            "source_email": "alerts@example.com",
            "recipients": ["user1@example.com", "user2@example.com"]
        }

    def test_send_critical_email(self):
        query_result = {
            "total_messages": 100,
            "failed_messages": 30,
            "failure_rate": 30.0,
            "alert_level": "CRITICAL"
        }

        email_alert.send_alert_email(query_result, self.config, self.mock_ses_client)

        self.mock_ses_client.send_email.assert_called_once()

        args, kwargs = self.mock_ses_client.send_email.call_args
        subject_data = kwargs["Message"]["Subject"]["Data"]
        body_data = kwargs["Message"]["Body"]["Text"]["Data"]

        self.assertIn("Critical", subject_data)
        self.assertIn("Alert Level: CRITICAL", body_data)
        self.assertIn("Total Messages: 100", body_data)
        self.assertIn("Failed Messages: 30", body_data)
        self.assertIn("Failure Rate: 30.0%", body_data)

    def test_send_warning_email(self):
        query_result = {
            "total_messages": 100,
            "failed_messages": 5,
            "failure_rate": 5.0,
            "alert_level": "WARNING"
        }

        email_alert.send_alert_email(query_result, self.config, self.mock_ses_client)

        self.mock_ses_client.send_email.assert_called_once()

        args, kwargs = self.mock_ses_client.send_email.call_args
        subject_data = kwargs["Message"]["Subject"]["Data"]
        body_data = kwargs["Message"]["Body"]["Text"]["Data"]

        self.assertIn("Warning", subject_data)
        self.assertIn("Alert Level: WARNING", body_data)
        self.assertIn("Total Messages: 100", body_data)
        self.assertIn("Failed Messages: 5", body_data)
        self.assertIn("Failure Rate: 5.0%", body_data)

    def test_send_resolved_email(self):
        query_result = {
            "total_messages": 100,
            "failed_messages": 0,
            "failure_rate": 0.0,
            "alert_level": "OK"
        }

        email_alert.send_alert_email(query_result, self.config, self.mock_ses_client)

        self.mock_ses_client.send_email.assert_called_once()

        args, kwargs = self.mock_ses_client.send_email.call_args
        subject_data = kwargs["Message"]["Subject"]["Data"]
        body_data = kwargs["Message"]["Body"]["Text"]["Data"]

        self.assertIn("Cleared", subject_data)
        self.assertIn("Alert Level: OK", body_data)
        self.assertIn("Total Messages: 100", body_data)
        self.assertIn("Failed Messages: 0", body_data)
        self.assertIn("Failure Rate: 0.0%", body_data)

if __name__ == "__main__":
    unittest.main()