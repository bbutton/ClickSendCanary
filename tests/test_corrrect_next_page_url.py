import os
import unittest
from unittest.mock import patch
from src.clicksend_monitor import ClicksendSMSProvider


class TestNextPageUrlValidation(unittest.TestCase):
    def setUp(self):
        os.environ["CLICKSEND_USERNAME"] = "dummy_username"
        os.environ["CLICKSEND_API_KEY"] = "dummy_api_key"
        self.provider = ClicksendSMSProvider()

    def fake_incorrect_response(self, page):
        """
        For page 1, returns a response with an incorrect next_page_url.
        For page 2, returns a normal response.
        """
        if page == 1:
            # Incorrect next_page_url (should be "/?page=2", but is not)
            return {
                "total": 3,
                "per_page": 2,
                "current_page": 1,
                "last_page": 2,
                "next_page_url": "/?page=332",  # Incorrect value!
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
    def test_incorrect_next_page_url_raises_error(self, mock_sms_history_get):
        def side_effect(*args, **kwargs):
            page = kwargs.get("page", 1)
            return self.fake_incorrect_response(page)

        mock_sms_history_get.side_effect = side_effect

        # We expect that the method will raise a ValueError due to the incorrect next_page_url.
        with self.assertRaises(ValueError):
            self.provider.get_all_sms_history()


if __name__ == '__main__':
    unittest.main()
