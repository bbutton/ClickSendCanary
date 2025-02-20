import unittest
from unittest.mock import patch, MagicMock

from src.message_retriever import fetch_and_store_messages
from src.storage import store_messages

class TestMessageRetrieval(unittest.TestCase):

    @patch("src.message_retriever.get_messages")
    def test_interleaved_fetching_for_single_page(self, mock_get_messages,):
        # Simulate a single API call returning messages
        mock_get_messages.return_value = {
            "data": ["msg1", "msg2"],
            "next_page": None  # No more pages
        }

        # Run the function
        fetch_and_store_messages()

        # Ensure the API was called once
        mock_get_messages.assert_called_once()

    @patch("src.message_retriever.get_messages")  # Patch where it's used
    @patch("src.message_retriever.store_messages")  # Patch where it's used
    def test_fetch_and_store_messages(self, mock_store_messages, mock_get_messages):
        # Simulated API response
        mock_get_messages.return_value = {
            "data": {
                "current_page": 1,
                "last_page": 1,
                "data": [
                    {"message_id": "123", "to": "+15555555555", "body": "Test message", "status": "SUCCESS"}
                ]
            }
        }

        # Run the function
        fetch_and_store_messages()

        # Ensure the API was called once
        mock_get_messages.assert_called_once()

        # Ensure storage was called with the retrieved messages
        mock_store_messages.assert_called_once_with([
            {"message_id": "123", "to": "+15555555555", "body": "Test message", "status": "SUCCESS"}
        ])


if __name__ == "__main__":
    unittest.main()