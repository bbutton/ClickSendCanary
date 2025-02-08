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
            "total": 50,
            "per_page": 20,
            "current_page": 1,
            "last_page": 3,
            "next_page_url": "http://api.example.com/next",
            "prev_page_url": None,
            "from": 1,
            "to": 20,
            "data": [
                {"message_id": "abc123", "to": "+15551112222", "body": "Hello"},
                {"message_id": "def456", "to": "+15553334444", "body": "World"}
            ]
        }
        mock_sms_history_get.return_value = paginated_response

        result = self.provider.get_sms_history()
        self.assertEqual(result, paginated_response["data"])

    @patch('clicksend_client.SMSApi.sms_history_get')
    def test_get_sms_history_with_paginated_string_response(self, mock_sms_history_get):
        # Simulate a paginated response returned as a JSON string.
        paginated_response = {
            "total": 30,
            "per_page": 10,
            "current_page": 1,
            "last_page": 3,
            "next_page_url": "http://api.example.com/next",
            "prev_page_url": None,
            "from": 1,
            "to": 10,
            "data": [
                {"message_id": "ghi789", "to": "+15557778888", "body": "Foo"},
                {"message_id": "jkl012", "to": "+15559990000", "body": "Bar"}
            ]
        }
        json_string = json.dumps(paginated_response)
        mock_sms_history_get.return_value = json_string

        result = self.provider.get_sms_history()
        self.assertEqual(result, paginated_response["data"])

    @patch('clicksend_client.SMSApi.sms_history_get')
    def test_get_sms_history_with_paginated_object_response(self, mock_sms_history_get):
        # Simulate a paginated response returned as an object with a to_dict() method.
        paginated_response = {
            "total": 100,
            "per_page": 25,
            "current_page": 1,
            "last_page": 4,
            "next_page_url": "http://api.example.com/next",
            "prev_page_url": None,
            "from": 1,
            "to": 25,
            "data": [
                {"message_id": "mno345", "to": "+15551112222", "body": "Baz"},
                {"message_id": "pqr678", "to": "+15553334444", "body": "Qux"}
            ]
        }
        fake_object_response = FakePaginatedResponse(paginated_response)
        mock_sms_history_get.return_value = fake_object_response

        result = self.provider.get_sms_history()
        self.assertEqual(result, paginated_response["data"])

if __name__ == '__main__':
    unittest.main()