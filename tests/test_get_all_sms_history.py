import os
import unittest
from unittest.mock import patch
from src.clicksend_monitor import ClicksendSMSProvider


class TestGetAllSmsHistory(unittest.TestCase):
    def setUp(self):
        # Set dummy credentials so the provider initializes.
        os.environ["CLICKSEND_USERNAME"] = "dummy_username"
        os.environ["CLICKSEND_API_KEY"] = "dummy_api_key"
        self.provider = ClicksendSMSProvider()

    def fake_response(self, page):
        """
        Returns a fake paginated API response.

        For page 1:
          - Returns 2 messages.
          - Indicates that the next page URL is "/?page=2".
          - 'current_page' is 1 and 'last_page' is 2.

        For page 2:
          - Returns 1 message.
          - 'next_page_url' is None.
        """
        if page == 1:
            return {
                "total": 3,
                "per_page": 2,
                "current_page": 1,
                "last_page": 2,
                "next_page_url": "/?page=2",
                "prev_page_url": None,
                "from": 1,
                "to": 2,
                "data": [
                    {"message_id": "msg1", "to": "+1234567890", "body": "Hello"},
                    {"message_id": "msg2", "to": "+1234567891", "body": "World"}
                ]
            }
        elif page == 2:
            return {
                "total": 3,
                "per_page": 2,
                "current_page": 2,
                "last_page": 2,
                "next_page_url": None,
                "prev_page_url": "/?page=1",
                "from": 3,
                "to": 3,
                "data": [
                    {"message_id": "msg3", "to": "+1234567892", "body": "Again"}
                ]
            }
        else:
            return {}

    @patch('clicksend_client.SMSApi.sms_history_get')
    def test_get_all_sms_history(self, mock_sms_history_get):
        # Configure the side effect of the mocked method based on the 'page' parameter.
        def side_effect(*args, **kwargs):
            page = kwargs.get("page", 1)
            return self.fake_response(page)

        mock_sms_history_get.side_effect = side_effect

        # Now call the method that should retrieve all pages.
        result = self.provider.get_all_sms_history()

        # Expected combined list of messages from both pages.
        expected = [
            {"message_id": "msg1", "to": "+1234567890", "body": "Hello"},
            {"message_id": "msg2", "to": "+1234567891", "body": "World"},
            {"message_id": "msg3", "to": "+1234567892", "body": "Again"}
        ]
        self.assertEqual(result, expected)


if __name__ == '__main__':
    unittest.main()