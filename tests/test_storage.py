import unittest
from unittest.mock import patch, MagicMock
from datetime import datetime
import json
from src.time_utils import convert_from_epoch
from src.storage import store_messages, generate_s3_key

class TestStorage(unittest.TestCase):

    @patch.dict("os.environ", {"S3_BUCKET": "clicksend-canary-data", "S3_ENDPOINT": "https://s3.amazonaws.com"})
    @patch("src.storage.boto3.client")
    @patch("src.storage.convert_to_parquet")
    def test_store_messages_to_s3(self, mock_convert_to_parquet, mock_boto_client):
        mock_s3 = mock_boto_client.return_value
        mock_convert_to_parquet.return_value = b"fake-parquet-data"

        first_message_epoch = 1740774645  # ✅ Fixed epoch timestamp (UTC)
        timestamp = convert_from_epoch(first_message_epoch)  # ✅ Convert to datetime
        expected_key = f"sms-logs/year={timestamp.strftime('%Y')}/month={timestamp.strftime('%m')}/day={timestamp.strftime('%d')}/messages-{timestamp.strftime('%H-%M-%S')}.parquet"

        messages = [{"message_id": "123", "status": "delivered", "sent_date": first_message_epoch}]

        store_messages(messages)

        mock_s3.put_object.assert_called_once_with(
            Bucket="clicksend-canary-data",
            Key=expected_key,
            Body=b"fake-parquet-data",
            ContentType="application/parquet"
        )


class TestStorageFileNaming(unittest.TestCase):

    def test_s3_key_format(self):
        # Given a specific datetime
        test_datetime = datetime(2025, 2, 28, 14, 30, 45)  # 2025-02-28 14:30:45

        # Expected filename format
        expected_key = "year=2025/month=02/day=28/messages-14-30-45.parquet"

        # When generating an S3 key
        generated_key = generate_s3_key(test_datetime)

        # Then it should match the expected format
        self.assertEqual(generated_key, expected_key)

if __name__ == "__main__":
    unittest.main()