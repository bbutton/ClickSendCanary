import unittest
from unittest.mock import patch

from src.clicksend_api import fetch_all_messages

import unittest
from unittest.mock import patch
from src.clicksend_api import get_messages

class TestClickSendAPI(unittest.TestCase):

    @patch("src.clicksend_api.requests.get")
    def test_get_messages_returns_messages_on_success(self, mock_requests_get):
        mock_requests_get.return_value.status_code = 200
        mock_requests_get.return_value.json.return_value = {
            "data": {
                "current_page": 1,
                "last_page": 3,
                "data": [
                    {"message_id": "123", "to": "+15555555555", "body": "Test message", "status": "SUCCESS"}
                ]
            }
        }

        messages, status_code, last_page = get_messages("test_user", "test_key", 1708300800, 1708387199)

        expected_messages = [
            {"message_id": "123", "to": "+15555555555", "body": "Test message", "status": "SUCCESS"}
        ]
        self.assertEqual(messages, expected_messages)
        self.assertEqual(status_code, 200)

        self.assertEqual(last_page, 3)

    @patch("src.clicksend_api.requests.get")
    def test_get_messages_returns_empty_on_404(self, mock_requests_get):
        mock_requests_get.return_value.status_code = 404
        mock_requests_get.return_value.text = "Not Found"

        messages, status_code, last_page = get_messages("test_user", "test_key", 1708300800, 1708387199)

        self.assertEqual(messages, [])  # ✅ Should return empty list, not None
        self.assertEqual(status_code, 404)
        self.assertIsNone(last_page)

    @patch("src.clicksend_api.requests.get")
    def test_get_messages_returns_none_on_500(self, mock_requests_get):
        mock_requests_get.return_value.status_code = 500
        mock_requests_get.return_value.text = "Internal Server Error"

        messages, status_code, last_page = get_messages("test_user", "test_key", 1708300800, 1708387199)

        self.assertIsNone(messages)  # ✅ Should return None for failures
        self.assertEqual(status_code, 500)
        self.assertIsNone(last_page)

class TestMessageRetrieval(unittest.TestCase):

    @patch("src.clicksend_api.get_messages")
    def test_fetch_all_messages_single_page(self, mock_get_messages):
        mock_get_messages.return_value = (
            [  # ✅ Updated to return messages as a list
                {"message_id": "123", "to": "+15555555555", "body": "Test message", "status": "SUCCESS"}
            ],
            200,  # ✅ Added status_code
            1  # ✅ Added last_page
        )

        messages = list(fetch_all_messages("test_user", "test_key", "2024-02-18 18:00:00", "2024-02-19 17:59:59"))

        self.assertEqual(len(messages), 1)

        extracted_messages, status_code = messages[0]
        self.assertEqual(extracted_messages, [
            {"message_id": "123", "to": "+15555555555", "body": "Test message", "status": "SUCCESS"}
        ])
        self.assertEqual(status_code, 200)  # ✅ Also verify status code
        mock_get_messages.assert_called_once_with("test_user", "test_key", 1708300800, 1708387199, 1)

    @patch("src.clicksend_api.get_messages")
    def test_fetch_all_messages_multiple_pages(self, mock_get_messages):
        mock_get_messages.side_effect = [
            (
                [  # ✅ Updated to return messages as a list
                    {"message_id": "123", "to": "+15555555555", "body": "Test message 1", "status": "SUCCESS"}
                ],
                200,  # ✅ Added status_code
                2  # ✅ Added last_page
            ),
            (
                [  # ✅ Second page of messages
                    {"message_id": "456", "to": "+15555555555", "body": "Test message 2", "status": "SUCCESS"}
                ],
                200,  # ✅ Added status_code
                2  # ✅ Added last_page
            )
        ]

        messages = list(fetch_all_messages("test_user", "test_key", "2024-02-18 18:00:00", "2024-02-19 17:59:59"))

        self.assertEqual(len(messages), 2)

        ### CHANGE START - Extract messages before assertion
        extracted_messages_1, status_code_1 = messages[0]
        extracted_messages_2, status_code_2 = messages[1]

        self.assertEqual(extracted_messages_1, [
            {"message_id": "123", "to": "+15555555555", "body": "Test message 1", "status": "SUCCESS"}
        ])
        self.assertEqual(status_code_1, 200)  # ✅ Verify status code

        self.assertEqual(extracted_messages_2, [
            {"message_id": "456", "to": "+15555555555", "body": "Test message 2", "status": "SUCCESS"}
        ])
        self.assertEqual(status_code_2, 200)  # ✅ Verify status code
        ### CHANGE END

        self.assertEqual(mock_get_messages.call_count, 2)
        mock_get_messages.assert_any_call("test_user", "test_key", 1708300800, 1708387199, 1)
        mock_get_messages.assert_any_call("test_user", "test_key", 1708300800, 1708387199, 2)