# src/storage.py

import pandas as pd
import boto3
import io
import os
from datetime import datetime

def convert_to_parquet(messages):
    """
    Converts a list of message dictionaries into a Parquet file stored in memory.
    Returns the Parquet data as bytes.
    """
    df = pd.DataFrame(messages)
    parquet_buffer = io.BytesIO()
    df.to_parquet(parquet_buffer, index=False)
    return parquet_buffer.getvalue()

def get_s3_client():
    s3_endpoint = os.getenv("S3_ENDPOINT")
    s3_bucket = os.getenv("S3_BUCKET")

    if not s3_endpoint or not s3_bucket:
        raise EnvironmentError("Missing required environment variables: S3_ENDPOINT or S3_BUCKET.")

    return boto3.client("s3", endpoint_url=s3_endpoint), s3_bucket

def store_messages(messages):
    if not messages:
        return

    s3_client, s3_bucket = get_s3_client()

    parquet_data = convert_to_parquet(messages)

    timestamp = datetime.strptime(messages[0]["timestamp"], "%Y-%m-%d %H:%M:%S")
    s3_key = f"sms-logs/year={timestamp.year}/month={timestamp.month:02}/day={timestamp.day:02}/messages.parquet"

    response = s3_client.put_object(Bucket=s3_bucket, Key=s3_key, Body=parquet_data)
