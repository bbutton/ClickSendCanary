import os
import unittest
from unittest.mock import patch
from src.clicksend_monitor import ClicksendSMSProvider


class TestSinglePageResponse(unittest.TestCase):
    def setUp(self):
        # Set dummy credentials so the provider initializes.
        os.environ["CLICKSEND_USERNAME"] = "dummy_username"
        os.environ["CLICKSEND_API_KEY"] = "dummy_api_key"
        self.provider = ClicksendSMSProvider()

    @patch('clicksend_client.SMSApi.sms_history_get')
    def test_single_page_response(self, mock_sms_history_get):
        # Simulate a one-page API response.
        single_page_response = {
            "data": {
                "total": 2,
                "per_page": 2,
                "current_page": 1,
                "last_page": 1,
                "next_page_url": None,
                "prev_page_url": None,
                "from": 1,
                "to": 2,
                "data": [
                    {"message_id": "msg1", "to": "+15551112222", "body": "Hello"},
                    {"message_id": "msg2", "to": "+15552223333", "body": "World"}
                ]
            }
        }
        # The mocked API call returns the simulated response.
        mock_sms_history_get.return_value = single_page_response

        # Call get_sms_history and verify it returns the list of messages.
        result = self.provider.get_all_sms_history()
        self.assertEqual(result, single_page_response["data"]["data"])


if __name__ == '__main__':
    unittest.main()
