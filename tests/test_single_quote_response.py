import os
import unittest
from unittest.mock import patch
from src.clicksend_monitor import ClicksendSMSProvider

class TestSingleQuoteResponse(unittest.TestCase):
    def setUp(self):
        # Set dummy credentials via environment variables
        os.environ["CLICKSEND_USERNAME"] = "dummy_username"
        os.environ["CLICKSEND_API_KEY"] = "dummy_api_key"
        self.provider = ClicksendSMSProvider()

    @patch('clicksend_client.SMSApi.sms_history_get')
    def test_get_sms_history_with_single_quote_string(self, mock_sms_history_get):
        # Create a fake response where the string representation uses single quotes.
        # This mimics the scenario where the API response string isn't valid JSON.
        fake_data = {'data': [{'message_id': '555', 'status': 'SUCCESS', 'to': '+15555667788'}]}
        # Using Python's repr produces a string with single quotes.
        single_quote_response = str(fake_data)
        mock_sms_history_get.return_value = single_quote_response

        # When we call get_sms_history, it should parse the string (using our fallback)
        # and return the list of messages from fake_data.
        result = self.provider.get_sms_history()
        self.assertEqual(result, fake_data["data"])

if __name__ == '__main__':
    unittest.main()
