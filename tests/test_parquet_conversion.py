import unittest
import pyarrow.parquet as pq
import pyarrow as pa
import io
from src.storage import convert_to_parquet

class TestParquetConversion(unittest.TestCase):

    def test_convert_messages_to_parquet(self):
        messages = [
            {"message_id": "123", "to": "+15555555555", "body": "Test message", "status": "SUCCESS", "timestamp": "2024-02-19 14:30:00"},
            {"message_id": "456", "to": "+15555555555", "body": "Another message", "status": "FAILED", "timestamp": "2024-02-19 15:00:00"}
        ]

        parquet_data = convert_to_parquet(messages)

        # Read back Parquet data to verify correctness using PyArrow
        buffer = io.BytesIO(parquet_data)
        table = pq.read_table(buffer)

        # Convert PyArrow table to dictionary for easier validation
        df_dict = table.to_pydict()

        self.assertEqual(len(df_dict["message_id"]), 2)  # Should store two messages
        self.assertIn("message_id", df_dict)
        self.assertEqual(df_dict["message_id"][0], "123")
        self.assertEqual(df_dict["message_id"][1], "456")

if __name__ == "__main__":
    unittest.main()
