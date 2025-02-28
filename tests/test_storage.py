import unittest
from unittest.mock import patch
from src.storage import store_messages
import os
import json

class TestS3Storage(unittest.TestCase):

    @patch.dict(os.environ, {"S3_BUCKET": "babtestbucket", "S3_ENDPOINT": "http://localhost:4566"})
    @patch("src.storage.boto3.client")
    def test_store_messages_to_s3(self, mock_boto_client):
        mock_s3 = mock_boto_client.return_value

        messages = [
            {"message_id": "123", "to": "+15555555555", "body": "Test message", "status": "SUCCESS", "date": "1708387199"}
        ]

        store_messages(messages)

        mock_s3.put_object.assert_called_once()
        args, kwargs = mock_s3.put_object.call_args

        # ✅ Ensure correct S3 path format
        self.assertIn("sms-logs/year=2024/month=02/day=19/messages.json", kwargs["Key"])

        # ✅ Ensure data is stored as JSON, not Parquet
        stored_json = json.loads(kwargs["Body"])
        self.assertEqual(stored_json, messages)  # Should match the original messages list

if __name__ == "__main__":
    unittest.main()