import pyarrow.parquet as pq
import pyarrow as pa
import boto3
import io
import os
from datetime import datetime
from src.time_utils import convert_from_epoch

def convert_to_parquet(messages):
    """
    Converts a list of message dictionaries into a Parquet file stored in memory using PyArrow.
    Returns the Parquet data as bytes.
    """
    if not messages:
        raise ValueError("No messages to convert to Parquet.")

    # Convert list of dictionaries into a PyArrow Table
    table = pa.Table.from_pydict({key: [msg[key] for msg in messages] for key in messages[0]})

    # Write table to an in-memory buffer
    buffer = io.BytesIO()
    pq.write_table(table, buffer)
    return buffer.getvalue()

def get_s3_client():
    s3_endpoint = os.getenv("S3_ENDPOINT")
    s3_bucket = os.getenv("S3_BUCKET")

    if not s3_endpoint or not s3_bucket:
        raise EnvironmentError("Missing required environment variables: S3_ENDPOINT or S3_BUCKET.")

    return boto3.client("s3", endpoint_url=s3_endpoint), s3_bucket

def store_messages(messages):
    print(f"attempting to store messages: {len(messages)}")

    if not messages:
        return

    s3_client, s3_bucket = get_s3_client()

    parquet_data = convert_to_parquet(messages)

    timestamp = convert_from_epoch(int(messages[0]["date"]))
    s3_key = f"sms-logs/year={timestamp.year}/month={timestamp.month:02}/day={timestamp.day:02}/messages.parquet"

    response = s3_client.put_object(Bucket=s3_bucket, Key=s3_key, Body=parquet_data)