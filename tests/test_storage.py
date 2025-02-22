import unittest
from unittest.mock import patch
from src.storage import store_messages
import datetime
import os

class TestS3Storage(unittest.TestCase):

    @patch.dict(os.environ, {"S3_BUCKET": "babtestbucket", "S3_ENDPOINT": "http://localhost:4566"})
    @patch("src.storage.boto3.client")
    @patch("src.storage.convert_to_parquet")  # Mock Parquet conversion
    def test_store_messages_to_s3(self, mock_convert_to_parquet, mock_boto_client):
        mock_s3 = mock_boto_client.return_value
        mock_convert_to_parquet.return_value = b"fake-parquet-data"

        messages = [
            {"message_id": "123", "to": "+15555555555", "body": "Test message", "status": "SUCCESS", "date": "1708387199"}
        ]

        store_messages(messages)

        mock_s3.put_object.assert_called_once()
        args, kwargs = mock_s3.put_object.call_args
        self.assertIn("sms-logs/year=2024/month=02/day=19/messages.parquet", kwargs["Key"])
        self.assertEqual(kwargs["Body"], b"fake-parquet-data")

if __name__ == "__main__":
    unittest.main()