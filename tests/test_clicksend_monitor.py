import os
import unittest
from unittest.mock import patch
from src.clicksend_monitor import ClicksendSMSProvider

class TestClicksendSMSProvider(unittest.TestCase):
    def setUp(self):
        # For testing, ensure the environment variables are set.
        os.environ["CLICKSEND_USERNAME"] = "dummy_username"
        os.environ["CLICKSEND_API_KEY"] = "dummy_api_key"
        self.provider = ClicksendSMSProvider()

    @patch('clicksend_client.SMSApi.sms_history_get')
    def test_get_sms_history_returns_list(self, mock_sms_history_get):
        # Define a fake API response with a 'data' attribute.
        fake_response = {
            "data": {
                "current_page": 1,
                "last_page": 1,
                "data": [
                    {"message_id": "123", "to": "+15555555555", "body": "Test message", "status": "SUCCESS"}
                ]
            }
        }

        # Patch the sdk method to return our fake response.
        mock_sms_history_get.return_value = fake_response

        # Call our provider method.
        result = self.provider.get_all_sms_history(limit=100)

        # Verify that the returned history is a list with our expected content.
        self.assertIsInstance(result, list)
        self.assertGreater(len(result), 0)
        self.assertEqual(result[0]['message_id'], "123")

if __name__ == '__main__':
    unittest.main()