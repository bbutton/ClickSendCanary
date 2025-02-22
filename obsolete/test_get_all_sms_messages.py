import os
import sys
import unittest
from unittest.mock import patch
from unittest.mock import MagicMock

# Adjust sys.path to include the repository root.
repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if repo_root not in sys.path:
    sys.path.insert(0, repo_root)

# Set dummy credentials for initialization.
os.environ["CLICKSEND_USERNAME"] = "dummy_username"
os.environ["CLICKSEND_API_KEY"] = "dummy_api_key"

from src.clicksend_monitor import ClicksendSMSProvider

class TestGetAllSmsMessages(unittest.TestCase):
    @patch.object(ClicksendSMSProvider, '_get_normalized_response')
    @patch.object(ClicksendSMSProvider, '_get_response_data')
    def test_get_all_sms_messages_multiple_pages(self, mock_get_response_data, mock_get_normalized_response):
        # Set up fake responses for two pages.
        # When page=1, _get_normalized_response returns "response1"
        # When page=2, returns "response2"
        mock_get_normalized_response.side_effect = ["response1", "response2"]

        # Define how _get_response_data should interpret each fake response.
        def fake_get_response_data(response):
            if response == "response1":
                # Page 1: current_page=1, last_page=2, two messages.
                return (1, 2, [{'message_id': '1'}, {'message_id': '2'}])
            elif response == "response2":
                # Page 2: current_page=2, last_page=2, one message.
                return (2, 2, [{'message_id': '3'}])
            else:
                return (1, 1, [])
        mock_get_response_data.side_effect = fake_get_response_data

        provider = ClicksendSMSProvider(sms_api=MagicMock())
        result = provider.get_all_sms_history(limit=100)
        expected = [{'message_id': '1'}, {'message_id': '2'}, {'message_id': '3'}]
        self.assertEqual(result, expected)

    @patch.object(ClicksendSMSProvider, '_get_normalized_response')
    @patch.object(ClicksendSMSProvider, '_get_response_data')
    def test_get_all_sms_messages_single_page(self, mock_get_response_data, mock_get_normalized_response):
        # Simulate a single-page response.
        mock_get_normalized_response.return_value = "response_single"
        mock_get_response_data.return_value = (1, 1, [{'message_id': '10'}, {'message_id': '20'}])

        provider = ClicksendSMSProvider(sms_api=MagicMock())
        result = provider.get_all_sms_history(limit=100)
        expected = [{'message_id': '10'}, {'message_id': '20'}]
        self.assertEqual(result, expected)

if __name__ == '__main__':
    unittest.main()