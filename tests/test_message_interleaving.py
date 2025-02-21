import unittest
from unittest.mock import patch

from src.clicksend_api import fetch_all_messages


@patch("src.message_retriever.store_messages")
@patch("src.clicksend_api.get_messages")
def test_fetch_and_store_all_messages(self, mock_get_messages, mock_store_messages):
    mock_get_messages.side_effect = [
        {
            "data": {
                "current_page": 1,
                "last_page": 2,
                "data": [
                    {"message_id": "123", "to": "+15555555555", "body": "Test message 1", "status": "SUCCESS"}
                ]
            }
        },
        {
            "data": {
                "current_page": 2,
                "last_page": 2,
                "data": [
                    {"message_id": "456", "to": "+15555555555", "body": "Test message 2", "status": "SUCCESS"}
                ]
            }
        }
    ]

    fetch_and_store_all_messages("test_user", "test_key", "2024-02-19 00:00:00", "2024-02-19 23:59:59")

    self.assertEqual(mock_get_messages.call_count, 2)
    self.assertEqual(mock_store_messages.call_count, 2)

    mock_store_messages.assert_any_call([
        {"message_id": "123", "to": "+15555555555", "body": "Test message 1", "status": "SUCCESS"}
    ])
    mock_store_messages.assert_any_call([
        {"message_id": "456", "to": "+15555555555", "body": "Test message 2", "status": "SUCCESS"}
    ])