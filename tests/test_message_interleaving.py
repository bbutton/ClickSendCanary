import unittest
from unittest.mock import patch
from src.message_retriever import fetch_and_store_all_messages

class TestFetchAndStoreMessages(unittest.TestCase):

    @patch("src.clicksend_api.get_messages")
    @patch("src.message_retriever.store_messages")
    def test_fetch_and_store_all_messages(self, mock_store_messages, mock_get_messages):
        mock_get_messages.side_effect = [
            ([{"message_id": "123", "to": "+15555555555", "body": "Test message 1", "status": "SUCCESS"}], 200, 2),
            ([{"message_id": "456", "to": "+15555555555", "body": "Test message 2", "status": "SUCCESS"}], 200, 2)
        ]

        messages_stored, error_code = fetch_and_store_all_messages(
            "test_user", "test_key", "2024-02-19 00:00:00", "2024-02-19 23:59:59"
        )

        self.assertEqual(messages_stored, 2)
        self.assertEqual(error_code, 200)
        self.assertEqual(mock_store_messages.call_count, 2)

        mock_store_messages.assert_any_call([
            {"message_id": "123", "to": "+15555555555", "body": "Test message 1", "status": "SUCCESS"}
        ])
        mock_store_messages.assert_any_call([
            {"message_id": "456", "to": "+15555555555", "body": "Test message 2", "status": "SUCCESS"}
        ])

    @patch("src.message_retriever.store_messages")  # ✅ Mock S3 storage
    @patch("src.message_retriever.fetch_all_messages")  # ✅ Mock API retrieval where it is USED
    def test_no_messages_fetched_nothing_stored(self, mock_fetch_all_messages, mock_store_messages):
        def mock_fetch():
            yield ([], 200)  # ✅ Ensures messages is an empty list, not None

        mock_fetch_all_messages.return_value = mock_fetch()  # ✅ Return mocked generator

        messages_stored, error_code = fetch_and_store_all_messages(
            "test_user", "test_key", "2024-02-19 00:00:00", "2024-02-19 23:59:59"
        )

        print(f"Messages Stored: {messages_stored}, Error Code: {error_code}")
        print(f"Mock Calls: {mock_store_messages.call_args_list}")

        self.assertEqual(messages_stored, 0)  # ✅ Ensure no messages are counted
        self.assertEqual(error_code, 200)  # ✅ Ensure no error occurred
        mock_store_messages.assert_not_called()  # ✅ Ensure storage is NOT called

    @patch("src.message_retriever.store_messages")  # ✅ Mock S3 storage
    @patch("src.message_retriever.fetch_all_messages")  # ✅ Mock API message retrieval
    def test_fetch_and_store_all_messages_stores_messages(self, mock_fetch_all_messages, mock_store_messages):
        def mock_fetch():
            yield ([{"message_id": "123", "to": "+15555555555", "body": "Test message", "status": "SUCCESS"}], 200)
            yield ([{"message_id": "456", "to": "+15555555555", "body": "Test message 2", "status": "SUCCESS"}], 200)

        mock_fetch_all_messages.return_value = mock_fetch()  # ✅ Return generator

        messages_stored, error_code = fetch_and_store_all_messages(
            "test_user", "test_key", "2024-02-19 00:00:00", "2024-02-19 23:59:59"
        )

        self.assertEqual(2, messages_stored)  # ✅ Should store 2 messages
        self.assertEqual(200, error_code)
        self.assertEqual(2, mock_store_messages.call_count)  # ✅ Ensure store_messages() was called twice

    @patch("src.message_retriever.store_messages")
    @patch("src.message_retriever.fetch_all_messages")
    def test_fetch_and_store_all_messages_handles_404(self, mock_fetch_all_messages, mock_store_messages):
        mock_fetch_all_messages.return_value = iter([
            ([], 404),  # ✅ Simulate API returning no messages (404)
            ([], 404)
        ])

        messages_stored, error_code = fetch_and_store_all_messages("test_user", "test_key", "2024-02-19 00:00:00", "2024-02-19 23:59:59")

        self.assertEqual(messages_stored, 0)  # ✅ No messages should be stored
        self.assertEqual(error_code, 404)
        mock_store_messages.assert_not_called()

    @patch("src.message_retriever.store_messages")  # ✅ store_messages is patched first
    @patch("src.clicksend_api.get_messages")  # ✅ get_messages is patched second
    def test_fetch_and_store_all_messages_handles_500(self, mock_get_messages, mock_store_messages):
        mock_get_messages.side_effect = [
            (None, 500, None)  # ✅ Ensure the first response is a 500
        ]

        messages_stored, error_code = fetch_and_store_all_messages(
            "test_user", "test_key", "2024-02-19 00:00:00", "2024-02-19 23:59:59"
        )

        self.assertEqual(0, messages_stored)
        self.assertEqual(500, error_code)
        mock_store_messages.assert_not_called()


if __name__ == "__main__":
    unittest.main()