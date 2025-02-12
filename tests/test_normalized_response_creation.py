import os
import json
import unittest
import ast
from unittest.mock import patch
from src.clicksend_monitor import ClicksendSMSProvider

class TestNormalizedResponse(unittest.TestCase):
    def setUp(self):
        os.environ["CLICKSEND_USERNAME"] = "dummy_username"
        os.environ["CLICKSEND_API_KEY"] = "dummy_api_key"
        self.provider = ClicksendSMSProvider()

    @patch('clicksend_client.SMSApi.sms_history_get')
    def test_helper_with_dict(self, mock_sms_history_get):
        # Simulate an API response that is already a dictionary.
        fake_response = {
            "total": 1,
            "data": [{"message_id": "123", "to": "+15555555555", "body": "Test message"}]
        }
        mock_sms_history_get.return_value = fake_response
        normalized = self.provider._get_normalized_response()
        self.assertIsInstance(normalized, dict)
        self.assertEqual(normalized, fake_response)

    @patch('clicksend_client.SMSApi.sms_history_get')
    def test_helper_with_json_string(self, mock_sms_history_get):
        # Simulate an API response that is a plain JSON string.
        fake_response = {
            "total": 1,
            "data": [{"message_id": "456", "to": "+15556667777", "body": "Another message"}]
        }
        json_str = json.dumps(fake_response)
        mock_sms_history_get.return_value = json_str
        normalized = self.provider._get_normalized_response()
        self.assertIsInstance(normalized, dict)
        self.assertEqual(normalized, fake_response)

    @patch('clicksend_client.SMSApi.sms_history_get')
    def test_helper_with_literal_eval(self, mock_sms_history_get):
        # Simulate an API response as a string that isn't valid JSON, but is a Python literal.
        fake_response = {
            "total": 1,
            "data": [{"message_id": "789", "to": "+15557778888", "body": "Literal message"}]
        }
        # Using Python's repr() gives us a string with single quotes.
        literal_str = repr(fake_response)
        mock_sms_history_get.return_value = literal_str
        normalized = self.provider._get_normalized_response()
        self.assertIsInstance(normalized, dict)
        self.assertEqual(normalized, fake_response)

if __name__ == '__main__':
    unittest.main()