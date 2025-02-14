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
        return {
            "data": {
                "current_page": page,
                "last_page": page + 1,  # Adjust this if needed for your logic
                "data": ["message1", "message2"]
            }
        }

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
