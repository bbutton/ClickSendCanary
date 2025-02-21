import unittest
from unittest.mock import patch

from src.clicksend_api import fetch_all_messages

import unittest
from unittest.mock import patch
from src.clicksend_api import get_messages

class TestClickSendAPI(unittest.TestCase):

    @patch("src.clicksend_api.requests.get")
    def test_get_messages_success(self, mock_requests_get):
        mock_requests_get.return_value.status_code = 200
        mock_requests_get.return_value.json.return_value = {
            "data": {
                "current_page": 1,
                "last_page": 3,
                "data": [
                    {"message_id": "123", "to": "+15555555555", "body": "Test message", "status": "SUCCESS"},
                    {"message_id": "456", "to": "+16666666666", "body": "Another test", "status": "FAILED"}
                ]
            }
        }

        response = get_messages("test_user", "test_key", 1708300800, 1708387199)

        expected = {
            "messages": [
                {"message_id": "123", "to": "+15555555555", "body": "Test message", "status": "SUCCESS"},
                {"message_id": "456", "to": "+16666666666", "body": "Another test", "status": "FAILED"}
            ],
            "current_page": 1,
            "last_page": 3
        }

        self.assertEqual(response, expected)

    @patch("src.clicksend_api.requests.get")
    def test_get_messages_returns_empty_list_on_404(self, mock_requests_get):
        mock_requests_get.return_value.status_code = 404
        mock_requests_get.return_value.text = "Not Found"

        response = get_messages("test_user", "test_key", 1708300800, 1708387199)

        expected = {"messages": [], "current_page": 1, "last_page": 1}
        self.assertEqual(response, expected)

    @patch("src.clicksend_api.requests.get")
    def test_get_messages_returns_none_on_500(self, mock_requests_get):
        mock_requests_get.return_value.status_code = 500
        mock_requests_get.return_value.text = "Internal Server Error"

        response = get_messages("test_user", "test_key", 1708300800, 1708387199)

        self.assertIsNone(response)


if __name__ == "__main__":
    unittest.main()

class TestMessageRetrieval(unittest.TestCase):

    @patch("src.clicksend_api.get_messages")
    def test_fetch_all_messages_single_page(self, mock_get_messages):
        mock_get_messages.return_value = {
            "data": {
                "current_page": 1,
                "last_page": 1,
                "data": [
                    {"message_id": "123", "to": "+15555555555", "body": "Test message", "status": "SUCCESS"}
                ]
            }
        }

        messages = list(fetch_all_messages("test_user", "test_key", "2024-02-18 18:00:00", "2024-02-19 17:59:59"))

        self.assertEqual(len(messages), 1)
        self.assertEqual(messages[0], [
            {"message_id": "123", "to": "+15555555555", "body": "Test message", "status": "SUCCESS"}
        ])
        mock_get_messages.assert_called_once_with("test_user", "test_key", 1708300800, 1708387199, 1)

    @patch("src.clicksend_api.get_messages")
    def test_fetch_all_messages_multiple_pages(self, mock_get_messages):
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

        messages = list(fetch_all_messages("test_user", "test_key", "2024-02-18 18:00:00", "2024-02-19 17:59:59"))

        self.assertEqual(len(messages), 2)
        self.assertEqual(messages[0], [
            {"message_id": "123", "to": "+15555555555", "body": "Test message 1", "status": "SUCCESS"}
        ])
        self.assertEqual(messages[1], [
            {"message_id": "456", "to": "+15555555555", "body": "Test message 2", "status": "SUCCESS"}
        ])
        self.assertEqual(mock_get_messages.call_count, 2)
        mock_get_messages.assert_any_call("test_user", "test_key", 1708300800, 1708387199, 1)
        mock_get_messages.assert_any_call("test_user", "test_key", 1708300800, 1708387199, 2)
