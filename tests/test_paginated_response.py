import os
import json
import unittest
from unittest.mock import patch
from src.clicksend_monitor import ClicksendSMSProvider

# A fake object to simulate an SDK model that implements to_dict().
class FakePaginatedResponse:
    def __init__(self, response_dict):
        self.response_dict = response_dict

    def to_dict(self):
        return self.response_dict

class TestPaginatedResponseHandling(unittest.TestCase):
    def setUp(self):
        # Set dummy credentials so that the provider initializes.
        os.environ["CLICKSEND_USERNAME"] = "dummy_username"
        os.environ["CLICKSEND_API_KEY"] = "dummy_api_key"
        self.provider = ClicksendSMSProvider()

    @patch('clicksend_client.SMSApi.sms_history_get')
    def test_get_sms_history_with_paginated_dict_response(self, mock_sms_history_get):
        # Simulate a paginated response returned as a dictionary.
        paginated_response = {
            "data": {
                "total": 50,
                "per_page": 20,
                "current_page": 1,
                "last_page": 1,
                "next_page_url": "/?page=2",
                "prev_page_url": None,
                "from": 1,
                "to": 20,
                "data": [
                    {"message_id": "abc123", "to": "+15551112222", "body": "Hello"},
                    {"message_id": "def456", "to": "+15553334444", "body": "World"}
                ]
            }
        }

        mock_sms_history_get.return_value = paginated_response

        result = self.provider.get_all_sms_history()
        self.assertEqual(result, paginated_response["data"]["data"])


if __name__ == '__main__':
    unittest.main()