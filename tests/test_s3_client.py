import unittest
import os
from unittest.mock import patch
from src.storage import get_s3_client

class TestS3Client(unittest.TestCase):

    @patch.dict(os.environ, {"S3_BUCKET": "babtestbucket", "S3_ENDPOINT": "http://localhost:4566"})
    def test_get_s3_client_success(self):
        client, bucket = get_s3_client()
        self.assertIsNotNone(client)  # Should return a valid client
        self.assertEqual(bucket, "babtestbucket")

    @patch.dict(os.environ, {}, clear=True)  # Simulate missing env vars
    def test_get_s3_client_missing_env_vars(self):
        with self.assertRaises(EnvironmentError):
            get_s3_client()

if __name__ == "__main__":
    unittest.main()