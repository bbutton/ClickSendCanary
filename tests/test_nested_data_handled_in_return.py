import os
import unittest
from unittest.mock import patch
from src.clicksend_monitor import ClicksendSMSProvider


class TestGetAllSmsHistoryNestedData(unittest.TestCase):
    def setUp(self):
        os.environ["CLICKSEND_USERNAME"] = "dummy_username"
        os.environ["CLICKSEND_API_KEY"] = "dummy_api_key"
        self.provider = ClicksendSMSProvider()

    def fake_response_nested(self, page):
        """
        Simulates a paginated API response where the 'data' key is a dictionary
        containing another 'data' key that holds the list of messages.
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
                "data": {  # Nested data
                    "data": [
                        {"message_id": "msg1", "to": "+1234567890", "body": "Hello"},
                        {"message_id": "msg2", "to": "+1234567891", "body": "World"}
                    ]
                }
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
                "data": {  # Nested data for page 2 as well.
                    "data": [
                        {"message_id": "msg3", "to": "+1234567892", "body": "Again"}
                    ]
                }
            }
        else:
            return {}

    @patch('clicksend_client.SMSApi.sms_history_get')
    def test_get_all_sms_history_with_nested_data(self, mock_sms_history_get):
        def side_effect(*args, **kwargs):
            page = kwargs.get("page", 1)
            return self.fake_response_nested(page)

        mock_sms_history_get.side_effect = side_effect

        # Call get_all_sms_history, which should now extract nested data correctly.
        result = self.provider.get_all_sms_history()
        expected = [
            {"message_id": "msg1", "to": "+1234567890", "body": "Hello"},
            {"message_id": "msg2", "to": "+1234567891", "body": "World"},
            {"message_id": "msg3", "to": "+1234567892", "body": "Again"}
        ]
        self.assertEqual(result, expected)


if __name__ == '__main__':
    unittest.main()