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
        fake_data = {
            "data": [
                {
                    "message_id": "123456",
                    "to": "+15555555555",
                    "body": "Test message",
                    "status": "SUCCESS",
                    "date": "2020-01-01 00:00:00"
                }
            ]
        }

        # Create a simple fake response object.
        class FakeResponse:
            def __init__(self, data):
                self.data = data

        # Patch the sdk method to return our fake response.
        mock_sms_history_get.return_value = FakeResponse(fake_data["data"])

        # Call our provider method.
        history = self.provider.get_sms_history()

        # Verify that the returned history is a list with our expected content.
        self.assertIsInstance(history, list)
        self.assertGreater(len(history), 0)
        self.assertEqual(history[0]['message_id'], "123456")

if __name__ == '__main__':
    unittest.main()