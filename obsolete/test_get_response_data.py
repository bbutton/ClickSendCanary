import os
import sys
import unittest

# Adjust sys.path to include the repository root.
repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if repo_root not in sys.path:
    sys.path.insert(0, repo_root)

# Set dummy credentials for initialization.
os.environ["CLICKSEND_USERNAME"] = "dummy_username"
os.environ["CLICKSEND_API_KEY"] = "dummy_api_key"

from src.clicksend_monitor import ClicksendSMSProvider

class TestGetResponseData(unittest.TestCase):
    def setUp(self):
        self.provider = ClicksendSMSProvider()

    def test_valid_response(self):
        """Test with a valid nested response containing current_page, last_page, and page messages."""
        fake_response = {
            "data": {
                "current_page": 2,
                "last_page": 5,
                "data": [
                    {"message_id": "msg1", "body": "Hello"},
                    {"message_id": "msg2", "body": "World"}
                ]
            }
        }
        current_page, last_page, page_messages = self.provider._get_response_data(fake_response)
        self.assertEqual(current_page, 2)
        self.assertEqual(last_page, 5)
        self.assertEqual(page_messages, [
            {"message_id": "msg1", "body": "Hello"},
            {"message_id": "msg2", "body": "World"}
        ])

    def test_missing_paging_info(self):
        """Test response with an empty 'data' dictionary to check default values."""
        fake_response = {
            "data": {}
        }
        current_page, last_page, page_messages = self.provider._get_response_data(fake_response)
        # Expect defaults: current_page defaults to 1, last_page defaults to current_page (i.e. 1), page_messages defaults to [].
        self.assertEqual(current_page, 1)
        self.assertEqual(last_page, 1)
        self.assertEqual(page_messages, [])

    def test_missing_inner_data(self):
        """Test response where paging info is provided but inner 'data' (the messages) is missing."""
        fake_response = {
            "data": {
                "current_page": 3,
                "last_page": 3
                # Note: No "data" key inside, so should default to []
            }
        }
        current_page, last_page, page_messages = self.provider._get_response_data(fake_response)
        self.assertEqual(current_page, 3)
        self.assertEqual(last_page, 3)
        self.assertEqual(page_messages, [])

if __name__ == '__main__':
    unittest.main()