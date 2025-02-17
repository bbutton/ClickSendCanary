import os
import json
import unittest
from unittest.mock import patch
from src.clicksend_monitor import ClicksendSMSProvider

# A helper class to simulate an object with a 'data' attribute.
class FakeResponseObject:
    def __init__(self, data):
        self.data = data

class TestClicksendSMSProviderResponseHandling(unittest.TestCase):
    def setUp(self):
        # Ensure our environment variables are set for testing.
        os.environ["CLICKSEND_USERNAME"] = "dummy_username"
        os.environ["CLICKSEND_API_KEY"] = "dummy_api_key"
        self.provider = ClicksendSMSProvider()

    @patch('clicksend_client.SMSApi.sms_history_get')
    def test_get_all_sms_history_with_dict_response(self, mock_sms_history_get):
        # Simulate a response that's already a dict.
        fake_data = {
            "data": {
                "current_page": 1,
                "last_page": 1,
                "data": [
                    {"message_id": "123", "to": "+15555555555", "body": "Test message", "status": "SUCCESS"}
                ]
            }
        }
        mock_sms_history_get.return_value = fake_data

        result = self.provider.get_all_sms_history()
        self.assertEqual(result, fake_data["data"]["data"])


if __name__ == '__main__':
    unittest.main()
